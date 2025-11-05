import torch
import transformers
import itertools
from wtpsplit import SaT
import requests

# 对tgt分词：中文每字，英文按空格
import re

def is_chinese_char(char):
    return '\u4e00' <= char <= '\u9fff'

def split_with_spaces(text):
    """
    按空格分割文本，但保留空格作为独立的元素
    """
    if not text:
        return []
    
    result = []
    current_word = ''
    
    for char in text:
        if char == ' ':
            if current_word:
                result.append(current_word)
                current_word = ''
            result.append(' ')
        else:
            current_word += char
    
    if current_word:
        result.append(current_word)
    
    return result

def split_english_with_punct_preserve_space(text):
    """
    英文文本分割，保留空格和标点处理
    """
    result = []
    current_word = ''
    punct_pattern = r'[,!?;:""''，。！？；：、（）《》【】]'
    
    for char in text:
        if char == ' ':
            if current_word:
                result.append(current_word)
                current_word = ''
            result.append(' ')
        elif re.match(punct_pattern, char):
            if current_word:
                result.append(current_word + char)
                current_word = ''
            elif result and not result[-1].isspace():
                result[-1] += char
            else:
                result.append(char)
        else:
            current_word += char
    
    if current_word:
        result.append(current_word)
    
    return result

def split_word(text):
    # 如果全是中文，按字分
    if all(is_chinese_char(c) or not c.strip() for c in text):
        return list(text)
    # 如果全是英文，按空格分
    elif all(ord(c) < 128 for c in text):
        return split_english_with_punct_preserve_space(text)
    # 混合文本，中文每字，英文按空格，标点加入前一个词
    result = []
    buffer = ''
    punct_pattern = r'[\u3000-\u303F\uFF00-\uFFEF,!?;:""''，。！？；：、（）《》【】]'
    
    for c in text:
        if is_chinese_char(c):
            if buffer:
                # 处理buffer中的内容，保留空格
                buffer_parts = split_with_spaces(buffer)
                result.extend(buffer_parts)
                buffer = ''
            result.append(c)
        elif re.match(punct_pattern, c):
            if buffer:
                # 先处理buffer中的内容
                buffer_parts = split_with_spaces(buffer.rstrip())
                if buffer_parts and not buffer_parts[-1].isspace():
                    # 将标点加到最后一个非空格词上
                    non_space_parts = [p for p in buffer_parts if not p.isspace()]
                    if non_space_parts:
                        # 找到最后一个非空格词的位置
                        for i in range(len(buffer_parts) - 1, -1, -1):
                            if not buffer_parts[i].isspace():
                                buffer_parts[i] += c
                                break
                    result.extend(buffer_parts)
                else:
                    result.extend(buffer_parts)
                    if result and not result[-1].isspace():
                        result[-1] += c
                    else:
                        result.append(c)
                buffer = ''
            elif result and not result[-1].isspace():
                result[-1] += c
            else:
                result.append(c)
        else:
            buffer += c
    
    if buffer:
        result.extend(split_with_spaces(buffer))
    
    return result

model = transformers.BertModel.from_pretrained('bert-base-multilingual-cased')
tokenizer = transformers.BertTokenizer.from_pretrained('bert-base-multilingual-cased')

def word_align(sent_src,sent_tgt):
    token_src, token_tgt = [tokenizer.tokenize(word) for word in sent_src], [tokenizer.tokenize(word) for word in sent_tgt]
    wid_src, wid_tgt = [tokenizer.convert_tokens_to_ids(x) for x in token_src], [tokenizer.convert_tokens_to_ids(x) for x in token_tgt]
    ids_src, ids_tgt = tokenizer.prepare_for_model(list(itertools.chain(*wid_src)), return_tensors='pt', model_max_length=tokenizer.model_max_length, truncation=True)['input_ids'], tokenizer.prepare_for_model(list(itertools.chain(*wid_tgt)), return_tensors='pt', truncation=True, model_max_length=tokenizer.model_max_length)['input_ids']
    sub2word_map_src = []
    for i, word_list in enumerate(token_src):
        sub2word_map_src += [i for x in word_list]
    sub2word_map_tgt = []
    for i, word_list in enumerate(token_tgt):
        sub2word_map_tgt += [i for x in word_list]

    # alignment
    align_layer = 8
    threshold = 1e-3
    model.eval()
    with torch.no_grad():
        out_src = model(ids_src.unsqueeze(0), output_hidden_states=True)[2][align_layer][0, 1:-1]
        out_tgt = model(ids_tgt.unsqueeze(0), output_hidden_states=True)[2][align_layer][0, 1:-1]

        dot_prod = torch.matmul(out_src, out_tgt.transpose(-1, -2))

        softmax_srctgt = torch.nn.Softmax(dim=-1)(dot_prod)
        softmax_tgtsrc = torch.nn.Softmax(dim=-2)(dot_prod)

        softmax_inter = (softmax_srctgt > threshold)*(softmax_tgtsrc > threshold)
        prob = softmax_srctgt+softmax_tgtsrc

    # 为每个tgt subword (j) 找到最佳src subword (i)
    best_align = {}
    num_src = out_src.shape[0]
    num_tgt = out_tgt.shape[0]

    for j in range(num_tgt):
        # 找到所有与j对齐的i
        aligned_is = torch.nonzero(softmax_inter[:, j], as_tuple=False).squeeze(-1).tolist()
        if isinstance(aligned_is, int):
            aligned_is = [aligned_is]
        if aligned_is:
            # 多个i时，选取prob最大的i
            best_i = max(aligned_is, key=lambda i: prob[i, j].item())
        else:
            # 没有对齐时，直接选取prob最大的i
            best_i = torch.argmax(prob[:, j]).item()
        best_align[j] = (best_i,prob[best_i,j])

    align_seq=[]
    j_i={}
    for j, (i, prob) in best_align.items():
        j=sub2word_map_tgt[j]
        i=sub2word_map_src[i]
        if j not in j_i:
            j_i[j]=[(i,prob)]
        else:
            j_i[j].append((i,prob))

    for k in j_i.keys():
        if len(j_i[k])>1:
            j_i[k]=sorted(j_i[k],key=lambda x:x[1],reverse=True)
        align_seq.append((k,j_i[k][0][0]))

    align_seq.sort(key=lambda x:x[0])
    return [i for _,i in align_seq]

def translate_en2cn(text):
    '''dummy'''
    return text

sat = SaT("sat-12l-sm")
def split_sents(text):
    sents=sat.split(text,0.3)
    sents = [sent for sent in sents]
    sents = [sent for sent in sents if sent!='']
    split_pos=[]
    cur_pos=0
    for sent in sents:
        for c in sent:
            cur_pos+=1
        split_pos.append(cur_pos)
    return split_pos

if __name__=='__main__':
    src = ['The protein binding properties of ','BGB-XXX',' were evaluated in CD-1 (cluster of differentiation 1) mouse, Sprague-Dawley rat, beagle dog, cynomolgus monkey and human plasma using an equilibrium dialysis method at drug concentrations from 0.1 to 10 µM, in human liver microsomes and in Sprague-Dawley rat brain using an equilibrium dialysis method at drug concentration from 0.1 to 10 µM [Report ','No. BGB-XXX-DMPK-PK-D-0001, BGB-XXX-DMPK-PK-D-0002 and  BGB-XXX-DMPK-PK-D-0004','/ Section 6, section 7 and section 9 in Module 2.6.5].']

    tgt = '采用平衡透析法，在0.1 ~ 10 μM的药物浓度下评价了BGB-XXX与CD-1（分化抗原簇1）小鼠、Sprague-Dawley大鼠、比格犬、食蟹猴和人血浆的蛋白结合特性；采用平衡透析法，在0.1 ~ 10 μM的药物浓度下评价了BGB-XXX与人肝微粒体和Sprague-Dawley大鼠脑的蛋白结合特性[报告编号BGB-XXX-DMPK-PK-D-0001、BGB-XXX-DMPK-PK-D-0002和BGB-XXX-DMPK-PK-D-0004/模块2.6.5的章节6、章节7和章节9]。'
    src=''.join(src)
    sent_src=split_word(src)
    sent_tgt=split_word(tgt)
    align_seq=word_align(sent_src,sent_tgt)
    for j,i in enumerate(align_seq):
        print(i,j,sent_src[i],sent_tgt[j])