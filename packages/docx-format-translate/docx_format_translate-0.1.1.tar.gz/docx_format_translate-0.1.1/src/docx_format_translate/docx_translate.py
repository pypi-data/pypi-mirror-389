# Copyright 2020 The HuggingFace Team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import zipfile, tempfile, shutil, random, re, os, hashlib
from lxml import etree
import copy
from typing import List, Any, Tuple
from lxml.etree import QName
from dataclasses import dataclass, field
from typing import List, Dict, Any
from .utils import *

def find_word_occurrences(word: str,
                          token_list: List,
                          idx: int) -> List[Tuple[int, int]]:
    """
    在 token_list 中查找所有连续子序列，其拼接结果等于 word，
    并且给定的 idx 落在该子序列的索引区间内。

    返回所有满足条件的 (start, end) 区间列表；若无，返回 []。
    """
    n = len(token_list)
    w_len = len(word)
    results: List[Tuple[int, int]] = []

    # 枚举所有连续子序列
    for start in range(n):
        # 剪枝：剩余拼不出 word 长度
        remain_chars = sum(len(token_list[k][0]) for k in range(start, n))
        if remain_chars < w_len:
            break

        cur_len = 0
        for end in range(start, n):
            cur_len += len(token_list[end][0])
            # 长度超了，再往后也不可能匹配
            if cur_len > w_len:
                break
            # 长度正好，检查拼接
            if cur_len == w_len:
                if ''.join([i[0] for i in token_list[start:end+1]]) == word:
                    # 检查 idx 是否落在 [start, end]
                    if start <= idx <= end:
                        results.extend([start, end])
                        return results
                break  # 再往后 cur_len 只会更大

    return results

def restore_true_indices(chars: List[str], idx_seq: List[int]) -> List[int]:
    """
    根据空格位置恢复索引序列的真实索引
    
    Args:
        chars: 包含空格的字符列表
        idx_seq: 对应非空格字符的索引序列
    
    Returns:
        恢复后的真实索引列表
    """
    # 记录所有非空格字符在原始列表中的索引
    non_space_indices = [i for i, ch in enumerate(chars) if ch != ' ']
    
    # 根据idx_seq中的值，去非空格索引列表中找对应的真实索引
    return [non_space_indices[idx] for idx in idx_seq]

def tranlate_algin(sentences_rpr, translate_func):
    tranlat_rprs=[]
    for sentence in sentences_rpr:
        text=''.join([s[0] for s in sentence])
        translate_text=translate_func(text)
        translate_text=translate_text.replace('\t','').replace('\n','')
        translate_words=split_word(translate_text)
        origin_words=[s[0] for s in sentence]
        align_seq=word_align([w for w in origin_words if w!=' '],[w for w in translate_words if w!=' '])
        seq_i=0
        new_align_seq=[]
        if align_seq!=[]:
            for w in translate_words:
                if w!=' ':
                    new_align_seq.append(align_seq[seq_i])
                    seq_i+=1
                else:
                    if seq_i>len(align_seq)-1:
                        new_align_seq.append(align_seq[-1])
                    else:
                        new_align_seq.append(align_seq[seq_i])
            align_seq=restore_true_indices(origin_words,new_align_seq)
        else:
            # 文本均为' '
            align_seq=[i for i in range(len(translate_words))]
        tranlate_rpr=[]
        for w,i in zip(translate_words,align_seq):
            if sentence[i][0] in w:
                idx=find_word_occurrences(w, sentence, i)
                if idx!=[]:
                    for j in range(idx[0],idx[1]+1):
                        tranlate_rpr.append((sentence[j][0],[copy.copy(p) for p in sentence[j][1]]))
                    continue
            tranlate_rpr.append((w,[copy.copy(p) for p in sentence[i][1]]))
        tranlat_rprs.extend(tranlate_rpr)
    return tranlat_rprs

def split_tuples_to_sentences(tuples: List[Tuple[str, Any]]) -> List[List[Tuple[str, Any]]]:
    """
    把 (text, payload) 列表按句子切分点拆成两重列表，每子列表是一句。
    切分点落在 text 内部时，拆元组；payload 保持；顺序保持。
    """
    if not tuples:
        return []

    full_text = ''.join(t[0] for t in tuples)
    split_pos = split_sents(full_text)
    if not split_pos:
        return [tuples[:]]

    # 1. 记录每个 text 在整句中的 [start, end)
    offsets: List[Tuple[int, int]] = []
    start = 0
    for txt, _ in tuples:
        offsets.append((start, start + len(txt)))
        start += len(txt)

    sentences: List[List[Tuple[str, Any]]] = []
    cur_sent: List[Tuple[str, Any]] = []
    pos_idx = 0
    next_sp_idx = 0
    cur_end = split_pos[0] if split_pos else len(full_text)

    # 2. 顺序处理每个元组
    while pos_idx < len(offsets):
        s, e = offsets[pos_idx]
        txt, pay = tuples[pos_idx]

        # 2.1 整 text 都在当前句区间
        if e <= cur_end:
            cur_sent.append((txt, [copy.copy(p) for p in pay]))
            pos_idx += 1
            continue

        # 2.2 切分点落在 text 内部 → 拆元组
        if s < cur_end < e:
            left_txt = txt[:cur_end - s]
            right_txt = txt[cur_end - s:]
            if left_txt:
                cur_sent.append((left_txt, [copy.copy(p) for p in pay]))
            sentences.append(cur_sent)
            cur_sent = [(right_txt, [copy.copy(p) for p in pay])] if right_txt else []
            pos_idx += 1
        else:  # s >= cur_end，整 text 归下一句
            sentences.append(cur_sent)
            cur_sent = []

        # 推进句区间
        next_sp_idx += 1
        cur_end = split_pos[next_sp_idx] if next_sp_idx < len(split_pos) else len(full_text)

    # 3. 最后一句
    if cur_sent:
        sentences.append(cur_sent)
    return sentences


NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}

@dataclass
class BookMark:
    start: etree._Element =None  # w:bookmarkStart 节点
    end: etree._Element =None
    skip: bool = False
    close: bool = False

    def __eq__(self, other):
        return self is other
    
    def __str__(self):
        s = (
                f"start: {etree.tostring(self.start, encoding='unicode', pretty_print=True).strip() if self.begin else None}\n"
                f"end: {etree.tostring(self.end, encoding='unicode', pretty_print=True).strip() if self.end else None}\n"
                f"skip: {self.skip}\n"
                f"close: {self.close}\n"
            )
        return s

@dataclass
class Field:
    begin: etree._Element =None  # w:fldChar begin 节点
    separate: etree._Element=None 
    end: etree._Element=None 
    insert_text: List[etree._Element]=field(default_factory=list) 
    skip: bool = False
    close: bool = False
    hyperlink: Dict = None
    activate_hl_fld: etree._Element = None

    def __eq__(self, other):
        return self is other
    
    def __str__(self):
        s = (
                f"begin: {etree.tostring(self.begin, encoding='unicode', pretty_print=True).strip() if self.begin else None}\n"
                f"separate: {etree.tostring(self.separate, encoding='unicode', pretty_print=True).strip() if self.separate else None}\n"
                f"end: {etree.tostring(self.end, encoding='unicode', pretty_print=True).strip() if self.end else None}\n"
                f"insert_text: {[etree.tostring(ele, encoding='unicode', pretty_print=True).strip() for ele in self.insert_text]}\n"
                f"skip: {self.skip}\n"
                f"close: {self.close}\n"
            )
        return s

@dataclass
class TraceNode:
    rPr: etree._Element =None
    is_text:bool =False
    is_visible:bool  = False
    is_image:bool = False
    is_fldsimple:bool = False
    hyperlink:Dict =None
    fld: Field=None
    bookmark_id: List[str]=None
    invisible_element: etree._Element =None
    image_element_r: etree._Element =None
    fld_simple_element_r: etree._Element =None
    close_bookmark_ids: List[int] = field(default_factory=list) 
    close_flds: List[Field] = field(default_factory=list) 

    def __copy__(self):
        new=TraceNode()
        new.rPr=self.rPr
        new.is_text=self.is_text
        new.is_visible=self.is_visible
        new.is_image=self.is_image
        new.is_fldsimple=self.is_fldsimple
        new.hyperlink=self.hyperlink
        new.fld=self.fld
        new.bookmark_id=copy.deepcopy(self.bookmark_id)
        new.invisible_element=copy.deepcopy(self.invisible_element)
        new.image_element_r=copy.deepcopy(self.image_element_r)
        new.fld_simple_element_r=copy.deepcopy(self.fld_simple_element_r)
        new.close_bookmark_ids=copy.deepcopy(self.close_bookmark_ids)
        new.close_flds=copy.deepcopy(self.close_flds)
        return new

def run_category(r):
    """
    返回 'begin' | 'separate' | 'end' | 'instr' | 'text' | 'image'
    """
    if r.xpath('w:fldChar', namespaces=NS):
        return r.xpath('w:fldChar/@w:fldCharType', namespaces=NS)[0]   # begin/separate/end
    if r.xpath('w:instrText', namespaces=NS):
        return 'instr'
    if r.xpath('w:t | w:delText | w:tab | w:br | w:noBreakHyphen | w:softHyphen | w:cr', namespaces=NS):
        return 'text'
    if r.xpath('self::w:drawing | self::w:pict', namespaces=NS):
        return 'image'
    if r.xpath('self::w:fldSimple', namespaces=NS):
        return 'fldSimple'
    return None

def iter_run_nodes(run):
    """
    按原顺序遍历 <w:r> 子节点：
    可见文字 → text
    不可见符号 → 返回整个节点（零长符号）
    """
    for child in run:
        tag = QName(child).localname
        if tag in ('t'):
            yield child.text
        elif tag in ('delText'):
            yield None
        elif tag in ('tab', 'br', 'noBreakHyphen', 'softHyphen', 'cr'):
            yield copy.deepcopy(child)

bookmark_dict:Dict[int, BookMark] = {}
bookmark_id=[]
st_fld=[]
skip_fld=[]
def process_run(r, hyperlink=None):
    out=[]
    rPr = r.find('w:rPr', NS)
    r_c=run_category(r)
    if r_c=='begin':
        fld=Field(begin=copy.deepcopy(r))
        if hyperlink!=None:
            fld.hyperlink=hyperlink
        st_fld.append(fld)
        return []
    if r_c=='separate':
        st_fld[-1].separate=copy.deepcopy(r)
        return []
    if r_c=='end':
        st_fld[-1].end=copy.deepcopy(r)
        st_fld[-1].close=True
        if st_fld[-1].skip:
            skip_fld.append(st_fld[-1])
        st_fld.pop()
        return []
    if r_c=='instr':
        st_fld[-1].insert_text.append(copy.deepcopy(r))
        return []
    if r_c=='del':
        return []
    if r_c=='text':
        t_n=TraceNode()
        if bookmark_id:
            t_n.bookmark_id=copy.deepcopy(bookmark_id)
        # 处理域
        if st_fld:
            t_n.fld=st_fld[-1]
        if hyperlink:
            t_n.hyperlink=hyperlink
        t_n.rPr=copy.deepcopy(rPr)
        for t in iter_run_nodes(r):
            if t==None:
                continue
            if type(t)==str:
                for w in split_word(t):
                    t_n.is_visible=True
                    t_n.is_text=True
                    out.append((w,copy.copy(t_n)))
                continue
            if type(t)==etree._Element:
                tmp=copy.copy(t_n)
                tmp.is_visible=False
                tmp.invisible_element=t
                out.append(('',tmp))
                continue
    if r_c =='image':
        t_n=TraceNode(is_image=True, image_element_r=copy.deepcopy(r))
        if bookmark_id:
            t_n.bookmark_id=copy.deepcopy(bookmark_id)
        if st_fld:
            t_n.fld=st_fld[-1]
        elif hyperlink:
            t_n.hyperlink=hyperlink
        out.append(('',t_n))
    if r_c=='fldSimple':
        t_n=TraceNode(is_fldsimple=True, fld_simple_element_r=copy.deepcopy(r))
        if bookmark_id:
            t_n.bookmark_id=copy.deepcopy(bookmark_id)
        if st_fld:
            t_n.fld=st_fld[-1]
        elif hyperlink:
            t_n.hyperlink=hyperlink
        out.append(('',t_n))
    return out

def extract_tokens_with_format(p_el):
    output = []
    #域栈
    for child in p_el:                       # 直接子节点
        tag = QName(child).localname
        if tag == 'bookmarkStart':
            id=child.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id')
            bookmark_dict[id]=BookMark(start=copy.deepcopy(child))
            bookmark_id.append(id)
        elif tag == 'bookmarkEnd':
            id=child.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id')
            if id not in bookmark_dict:
                continue
            bookmark_dict[id].end=copy.deepcopy(child)
            bookmark_dict[id].close=True
            bookmark_id.remove(id)
        elif tag == 'hyperlink':
            hl={k: copy.deepcopy(v) for k, v in child.attrib.items()}
            for r in child.xpath('.//w:r', namespaces=NS):
                output.extend(process_run(r, hyperlink=hl))
        elif tag == 'fldSimple':
            output.extend(process_run(child))
        elif tag == 'r':
            output.extend(process_run(child))
    result=[]
    start=[]
    end=[]
    while output!=[] and output[0][0]=='':
        start.append(output[0][1])
        output.pop()
    while output!=[] and output[-1][0]=='':
        end.append(output[-1][1])
        output.pop(-1)

    for out in output:
        if out[0]=='':
            result[-1][1].append(out[1])
        else:
            result.append((out[0],[out[1]]))
    return start, result, end

def delete_only_hyperlink_bookmark_run(p_el: etree._Element):
    """
    只删除：
    1. 整个 <w:hyperlink> 容器
    2. 所有 bookmarkStart/bookmarkEnd
    3. 所有 <w:r>（文字、符号、域、图片）
    保留：w:pPr、w:proofErr、w:ins、w:del 等非内容节点
    """
    # ① 删除整个超链接容器
    for hl in list(p_el.xpath('.//w:hyperlink', namespaces=NS)):
        if hl.getparent() is not None:
            hl.getparent().remove(hl)
    # ④ 删除所有 fldSimple 节点
    for fld in list(p_el.xpath('.//w:fldSimple', namespaces=NS)):
        if fld.getparent() is not None:
            fld.getparent().remove(fld)
    # ② 删除所有书签节点
    for bm in list(p_el.xpath('.//w:bookmarkStart | .//w:bookmarkEnd', namespaces=NS)):
        if bm.getparent() is not None:
            bm.getparent().remove(bm)

    # ③ 删除所有 w:r（文字、符号、域、图片）
    for r in list(p_el.xpath('.//w:r', namespaces=NS)):
        if r.getparent() is not None:
            r.getparent().remove(r)

    for c in list(p_el.xpath('.//w:commentRangeStart | .//w:commentRangeEnd', namespaces=NS)):
        if c.getparent() is not None:
            c.getparent().remove(c)
    
    for r in list(p_el.xpath('.//w:del | .//w:ins', namespaces=NS)):
        if r.getparent() is not None:
            r.getparent().remove(r)
    

def bookmark_close(word_format:List[Tuple[str, List[TraceNode]]]):
    ids=[]
    for k,v in bookmark_dict.items():
        if v.close==True:
            ids.append(k)
    for _,formats in reversed(word_format):
        for f in formats:
            if f.bookmark_id!=None:
                for i in f.bookmark_id:
                    if str(i) in ids:
                        f.close_bookmark_ids.append(i)
                        ids.remove(i)
    return [ i for i in ids if bookmark_dict[i].skip]

def skip_fld_close(word_format:List[Tuple[str, List[TraceNode]]]):
    for _,formats in reversed(word_format):
        for f in formats: 
            if f.fld in skip_fld:
                f.close_flds.append(f.fld)
                skip_fld.remove(f.fld)   
    return skip_fld

class Context:
    def __init__(self, p_el: etree._Element):
        self.activate_hyperlink:Tuple[Dict,etree._Element]=None
        self.activate_fld:Tuple[Field,List[etree._Element]]=None
        self.activate_run:Tuple[etree._Element,etree._Element]=None
        self.activate_bookmark_ids=[]
        self.p_el=p_el

    def rebuild_bookmark_start(self, trace_node: TraceNode):
        if trace_node.bookmark_id==None:
            return 
        for id in trace_node.bookmark_id:
            if id in self.activate_bookmark_ids:
                continue 
            if bookmark_dict[id].skip==False:
                self.activate_bookmark_ids.append(id)
                self.p_el.append(bookmark_dict[id].start)

    def rebuild_bookmark_end(self, trace_node: TraceNode):
        if trace_node.close_bookmark_ids!=[]:
            for id in trace_node.close_bookmark_ids:
                if self.activate_hyperlink!=None:
                    if self.activate_run!=None:
                        self.activate_hyperlink[1].append(self.activate_run[1])
                        self.activate_run=None
                    self.p_el.append(self.activate_hyperlink[1])
                    self.activate_hyperlink=None
                if self.activate_run!=None:
                    self.p_el.append(self.activate_run[1])
                    self.activate_run=None
                self.p_el.append(bookmark_dict[id].end)
                del bookmark_dict[id]

    def create_w_text(self, text, format, run):
        if format.is_text:
            new_t = etree.SubElement(run, '{%s}t' % NS['w'])
            new_t.text = text
            if ' ' in text:
                new_t.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve') 
        if format.is_visible==False:
            run.append(format.invisible_element)

    def update_activate_hyperlink(self, hl_dict, hl):
        if self.activate_hyperlink==None:
            self.activate_hyperlink=(hl_dict,hl)
        else:
            if self.activate_run!=None:
                self.activate_hyperlink[1].append(self.activate_run[1])
                self.activate_run=None
            self.p_el.append(self.activate_hyperlink[1])
            self.activate_hyperlink==(hl_dict,hl)

    def update_activate_run(self, rPr,run):
        if self.activate_run==None:
            return
        if self.activate_hyperlink!=None:
            self.activate_hyperlink[1].append(self.activate_run[1])
        else:
            self.p_el.append(self.activate_run[1])
        self.activate_run=(rPr,run)
            
    def create_run(self, format:TraceNode):
        if self.activate_run !=None and format.rPr is self.activate_run[0]:
            return self.activate_run[1]
        else:
            new_r = etree.Element('{%s}r' % NS['w'], nsmap=NS)
            rPr=format.rPr
            if rPr is not None:
                new_r.append(copy.deepcopy(rPr))
            self.activate_run=(format.rPr,new_r)
            self.update_activate_run(rPr,new_r)
            return new_r

    def rebuild_image(self, format:TraceNode):
        image_ele=format.image_element_r
        if self.activate_hyperlink!=None and format.hyperlink==None:
            if self.activate_run!=None:
                self.activate_hyperlink[1].append(self.activate_run[1])
                self.activate_run=None
            self.p_el.append(self.activate_hyperlink[1])
            self.activate_hyperlink=None
            self.p_el.append(image_ele)
            return
        if self.activate_hyperlink==None and format.hyperlink==None:
            if self.activate_run!=None:
                self.p_el.append(self.activate_run[1])
                self.activate_run=None
            self.p_el.append(image_ele)
            return
        if self.activate_hyperlink!=None and format.hyperlink!=None:
            if self.activate_hyperlink[0] is format.hyperlink:
                if self.activate_run!=None:
                    self.activate_hyperlink[1].append(self.activate_run[1])
                    self.activate_run=None
                self.activate_hyperlink[1].append(image_ele)
                return
            else:
                if self.activate_run!=None:
                    self.activate_hyperlink[1].append(self.activate_run[1])
                    self.activate_run=None
                self.p_el.append(self.activate_hyperlink[1])
                hl=self.create_hyperlink_from_dict(format.hyperlink)
                hl.append(image_ele)
                self.activate_hyperlink=(format.hyperlink,hl)
                return
        if self.activate_hyperlink==None and format.hyperlink!=None:
            if self.activate_run!=None:
                self.p_el.append(self.activate_run[1])
                self.activate_run=None
            hl=self.create_hyperlink_from_dict(format.hyperlink)
            hl.append(image_ele)
            self.activate_hyperlink=(format.hyperlink,hl)
            return

    def rebuild_fldsimple(self, format:TraceNode):
        fld_ele=format.fld_simple_element_r
        if self.activate_hyperlink!=None and format.hyperlink==None:
            if self.activate_run!=None:
                self.activate_hyperlink[1].append(self.activate_run[1])
                self.activate_run=None
            self.p_el.append(self.activate_hyperlink[1])
            self.activate_hyperlink=None
            self.p_el.append(fld_ele)
            return
        if self.activate_hyperlink==None and format.hyperlink==None:
            if self.activate_run!=None:
                self.p_el.append(self.activate_run[1])
                self.activate_run=None
            self.p_el.append(fld_ele)
            return
        if self.activate_hyperlink!=None and format.hyperlink!=None:
            if self.activate_hyperlink[0] is format.hyperlink:
                if self.activate_run!=None:
                    self.activate_hyperlink[1].append(self.activate_run[1])
                    self.activate_run=None
                self.activate_hyperlink[1].append(fld_ele)
                return
            else:
                if self.activate_run!=None:
                    self.activate_hyperlink[1].append(self.activate_run[1])
                    self.activate_run=None
                self.p_el.append(self.activate_hyperlink[1])
                hl=self.create_hyperlink_from_dict(format.hyperlink)
                hl.append(fld_ele)
                self.activate_hyperlink=(format.hyperlink,hl)
                return
        if self.activate_hyperlink==None and format.hyperlink!=None:
            if self.activate_run!=None:
                self.p_el.append(self.activate_run[1])
                self.activate_run=None
            hl=self.create_hyperlink_from_dict(format.hyperlink)
            hl.append(fld_ele)
            self.activate_hyperlink=(format.hyperlink,hl)
            return

    def rebuild_run(self, text, format:TraceNode):
        if format.hyperlink==None:
            if self.activate_hyperlink!=None:
                if self.activate_run!=None:
                    self.activate_hyperlink[1].append(self.activate_run[1])
                    self.activate_run=None
                self.p_el.append(self.activate_hyperlink[1])
                self.activate_hyperlink=None
        if format.is_image:
            self.rebuild_image(format)
        elif format.is_fldsimple:
            self.rebuild_fldsimple(format)
        else:
            run=self.create_run(format)
            self.create_w_text(text, format, run)

    def create_hyperlink_from_dict(self, saved_attrs: dict, nsmap=NS):
        """
        根据 Clark 键字典重建 <w:hyperlink> 空壳（无子节点）
        返回新元素
        """
        # 1. 创建空壳
        new_hl = etree.Element('{%s}hyperlink' % NS['w'], nsmap=nsmap)
        saved_attrs=copy.deepcopy(saved_attrs)
        # 2. 一次性挂回全部 Clark 键属性
        for clark_k, v in saved_attrs.items():
            new_hl.set(clark_k, v)   # lxml 自动识别命名空间
        return new_hl

    def rebuild_hyperlink(self, text, format):
        if format.hyperlink==None:
            return False
        if self.activate_hyperlink==None:
            hl=self.create_hyperlink_from_dict(format.hyperlink)
            self.update_activate_hyperlink(format.hyperlink, hl)
            self.rebuild_run(text, format)
            return

        if format.hyperlink is self.activate_hyperlink[0]:
            self.rebuild_run(text, format)
        else:
            hl=self.create_hyperlink_from_dict(format.hyperlink)
            self.update_activate_hyperlink(format.hyperlink, hl)
            self.rebuild_run(text, format)

    def create_fld_begin_inert(self, fld:Field):
        if fld.begin==None:
            return
        
        if self.activate_hyperlink!=None and fld.hyperlink!=None:
            if self.activate_hyperlink[0] is fld.hyperlink:
                hl=self.activate_hyperlink[1]
                if self.activate_run!=None:
                    hl.append(self.activate_run[1])
                    self.activate_run=None
                hl.append(copy.deepcopy(fld.begin))
                if fld.insert_text!=[]:
                    for i in fld.insert_text:
                        hl.append(copy.deepcopy(i))
                fld.activate_hl_fld=hl
                self.activate_fld=fld
                if fld.close==False:
                    fld.begin=None
                    fld.insert_text=[]
                return
            else:
                hl=self.activate_hyperlink[1]
                if self.activate_run!=None:
                    hl.append(self.activate_run[1])
                    self.activate_run=None
                self.p_el.append(hl)
                self.activate_hyperlink=None
                hl=self.create_hyperlink_from_dict(fld.hyperlink)
                hl.append(copy.deepcopy(fld.begin))
                if fld.insert_text!=[]:
                    for i in fld.insert_text:
                        hl.append(copy.deepcopy(i))
                self.activate_hyperlink=(fld.hyperlink,hl)
                self.activate_fld=fld
                fld.activate_hl_fld=hl
                if fld.close==False:
                    fld.begin=None
                    fld.insert_text=[]
                return

        if self.activate_hyperlink==None and fld.hyperlink!=None:
            if self.activate_run!=None:
                    self.p_el.append(self.activate_run[1])
                    self.activate_run=None
            hl=self.create_hyperlink_from_dict(fld.hyperlink)
            hl.append(copy.deepcopy(fld.begin))
            if fld.insert_text!=[]:
                for i in fld.insert_text:
                    hl.append(copy.deepcopy(i))
            self.activate_hyperlink=(fld.hyperlink,hl)
            self.activate_fld=fld
            fld.activate_hl_fld=hl
            if fld.close==False:
                fld.begin=None
                fld.insert_text=[]
            return

        if self.activate_hyperlink!=None and fld.hyperlink==None:
            hl=self.activate_hyperlink[1]
            if self.activate_run!=None:
                hl.append(self.activate_run[1])
            self.p_el.append(hl)
            self.activate_hyperlink=None
            self.activate_run=None
            self.p_el.append(copy.deepcopy(fld.begin))
            if fld.insert_text!=[]:
                for i in fld.insert_text:
                    self.p_el.append(copy.deepcopy(i))
            self.activate_fld=fld
            if fld.close==False:
                fld.begin=None
                fld.insert_text=[]
            return
    
        if fld.hyperlink==None and self.activate_hyperlink==None:
            if self.activate_run!=None:
                self.p_el.append(self.activate_run[1])
                self.activate_run=None
            self.p_el.append(copy.deepcopy(fld.begin))
            if fld.insert_text!=[]:
                for i in fld.insert_text:
                    self.p_el.append(copy.deepcopy(i))
            self.activate_fld=fld
            if fld.close==False:
                fld.begin=None
                fld.insert_text=[]
            return

    def create_fld_inert(self, fld:Field):
        if self.activate_hyperlink!=None and fld.hyperlink!=None:
            if self.activate_hyperlink[0] is fld.hyperlink:
                hl=self.activate_hyperlink[1]
                if self.activate_run!=None:
                    hl.append(self.activate_run[1])
                    self.activate_run=None
                for i in fld.insert_text:
                    hl.append(copy.deepcopy(i))
                if fld.close==False:
                    fld.insert_text=[]
                return
            else:
                for i in fld.insert_text:
                    fld.activate_hl_fld.append(copy.deepcopy(i))
                if fld.close==False:
                    fld.insert_text=[]
                return
        
        if self.activate_hyperlink!=None and fld.hyperlink==None:
            hl=self.activate_hyperlink[1]
            if self.activate_run!=None:
                hl.append(self.activate_run[1])
                self.activate_run=None
            self.p_el.append(hl)
            self.activate_hyperlink=None
            for i in fld.insert_text:
                self.p_el.append(copy.deepcopy(i))
            if fld.close==False:
                fld.insert_text=[]
            return
        
        if self.activate_hyperlink==None and fld.hyperlink==None:
            if self.activate_run!=None:
                self.p_el.append(self.activate_run[1])
                self.activate_run=None
            for i in fld.insert_text:
                self.p_el.append(copy.deepcopy(i))
            if fld.close==False:
                fld.insert_text=[]
            return


    def create_fld_separate(self, fld:Field):
        if fld.separate==None:
            return
        
        if self.activate_hyperlink!=None and fld.hyperlink!=None:
            if self.activate_hyperlink[0] is fld.hyperlink:
                hl=self.activate_hyperlink[1]
                if self.activate_run!=None:
                    hl.append(self.activate_run[1])
                    self.activate_run=None
                hl.append(copy.deepcopy(fld.separate))
                if fld.close==False:
                    fld.separate=None
                return
            else:
                fld.activate_hl_fld.append(copy.deepcopy(fld.separate))
                if fld.close==False:
                    fld.separate=None
                return
        
        if self.activate_hyperlink!=None and fld.hyperlink==None:
            hl=self.activate_hyperlink[1]
            if self.activate_run!=None:
                hl.append(self.activate_run[1])
                self.activate_run=None
            self.p_el.append(hl)
            self.activate_hyperlink=None
            self.p_el.append(copy.deepcopy(fld.separate))
            if fld.close==False:
                fld.separate=None
            return
        
        if self.activate_hyperlink==None and fld.hyperlink==None:
            if self.activate_run!=None:
                self.p_el.append(self.activate_run[1])
                self.activate_run=None
            self.p_el.append(copy.deepcopy(fld.separate))
            if fld.close==False:
                fld.separate=None
            return
        

    def create_fld_end(self, fld:Field):
        if fld.end==None:
            return

        if self.activate_hyperlink==None and fld.hyperlink!=None:
            fld.activate_hl_fld.append(copy.deepcopy(fld.end))
            if fld.skip==True:
                fld.end=None
            self.activate_fld=None
            return

        if self.activate_hyperlink!=None and fld.hyperlink!=None:
            if self.activate_hyperlink[0] is fld.hyperlink:
                hl=self.activate_hyperlink[1]
                if self.activate_run!=None:
                    hl.append(self.activate_run[1])
                    self.activate_run=None
                hl.append(copy.deepcopy(fld.end))
                if fld.skip==True:
                    fld.end=None
                self.activate_fld=None
                return
            else:
                fld.activate_hl_fld.append(copy.deepcopy(fld.end))
                if fld.skip==True:
                    fld.end=None
                self.activate_fld=None
                return
        
        if self.activate_hyperlink!=None and fld.hyperlink==None:
            hl=self.activate_hyperlink[1]
            if self.activate_run!=None:
                hl.append(self.activate_run[1])
                self.activate_run=None
            self.p_el.append(hl)
            self.activate_hyperlink=None
            self.p_el.append(copy.deepcopy(fld.end))
            if fld.skip==True:
                fld.end=None
            self.activate_fld=None
            return
        
        if self.activate_hyperlink==None and fld.hyperlink==None:
            if self.activate_run!=None:
                self.p_el.append(self.activate_run[1])
                self.activate_run=None
            self.p_el.append(copy.deepcopy(fld.end))
            if fld.skip==True:
                fld.end=None
            self.activate_fld=None
            return
     
    def rebuild_fldr_skip(self, text, format):
        if format.fld.skip==False:
            return None 
        if format.fld.insert_text!=[]:
            self.create_fld_inert(format.fld)
            format.fld.insert_text=[]
        if format.fld.separate!=None:
            self.create_fld_separate(format.fld)
            format.fld.separate=None
        if format.hyperlink!=None:
            self.rebuild_hyperlink(text, format)
        else:
            self.rebuild_run(text, format)
        if format.fld.close:
            for f in format.close_flds:
                self.create_fld_end(f)
                f.end=None

    def rebuild_fldr(self, text, format):
        if format.fld==None or format.fld.skip==True:
            return False
        if self.activate_fld==None:
            self.create_fld_begin_inert(format.fld)
            self.create_fld_separate(format.fld)
            if format.hyperlink!=None:
                self.rebuild_hyperlink(text, format)
            else:
                self.rebuild_run(text, format)
            return
        if format.fld is self.activate_fld:
            if format.hyperlink!=None:
                self.rebuild_hyperlink(text, format)
            else:
                self.rebuild_run(text, format)
        else:
            if self.activate_fld.end !=None:
                self.create_fld_end(self.activate_fld)
            self.create_fld_begin_inert(format.fld)
            self.create_fld_separate(format.fld)
            if format.hyperlink!=None:
                self.rebuild_hyperlink(text, format)
            else:
                self.rebuild_run(text, format)

    def clean(self):
        if self.activate_hyperlink!=None:
            if self.activate_run!=None:
                self.activate_hyperlink[1].append(self.activate_run[1])
                self.activate_run=None
            self.p_el.append(self.activate_hyperlink[1])
            self.activate_hyperlink=None
        else:
            if self.activate_run!=None:
                self.p_el.append(self.activate_run[1])
                self.activate_run=None
        if self.activate_fld!=None and self.activate_fld.close:
            self.create_fld_end(self.activate_fld)
        for fld in st_fld:
            if fld.skip:
                continue
            if fld is self.activate_fld:
                continue
            self.create_fld_begin_inert(fld)
            if fld.separate!=None:
                self.create_fld_separate(fld)

def rebuild_para_from_tokens(p_el, head, tokens_with_format, tail):
    """
    清空非域 run，按“路径索引”合并连续同格式 token，重建段落
    tokens_with_format: [(token, path_idx), ...]
    """
    if not tokens_with_format:
        return

    # 1. 只删非域、非超链接、非书签的纯文本 run
    delete_only_hyperlink_bookmark_run(p_el)

    head_bookmark_ids=bookmark_close(tokens_with_format)
    for id in head_bookmark_ids:
        p_el.append(bookmark_dict[id].end)
        del bookmark_dict[id]
    
    head_fld_end=skip_fld_close(tokens_with_format)
    for fld in head_fld_end:
        p_el.append(fld.end)
        skip_fld.remove(fld)

    activate_hyperlink:Tuple[Dict,etree._Element]=None
    activate_fld:Tuple[Field,List[etree._Element]]=None
    activate_run:Tuple[etree._Element,etree._Element]=None
    context=Context(p_el)

    for format in head:
        context.rebuild_bookmark_start(format)
        if format.fld!=None:
            if format.fld.skip==False:
                context.rebuild_fldr('', format)
            else:
                context.rebuild_fldr_skip('', format)
        elif format.hyperlink!=None:
            context.rebuild_hyperlink('', format)
        else:
            context.rebuild_run('', format)
        context.rebuild_bookmark_end(format)

    for word,formats in tokens_with_format:
        for format in formats:
            if format.is_text:
                text=word
            else:
                text=''
            context.rebuild_bookmark_start(format)
            if format.fld!=None:
                if format.fld.skip==False:
                    context.rebuild_fldr(text, format)
                else:
                    context.rebuild_fldr_skip(text, format)
            elif format.hyperlink!=None:
                context.rebuild_hyperlink(text, format)
            else:
                context.rebuild_run(text, format)
            context.rebuild_bookmark_end(format)
    
    for format in head:
        context.rebuild_bookmark_start(format)
        if format.fld!=None:
            if format.fld.skip==False:
                context.rebuild_fldr('', format)
            else:
                context.rebuild_fldr_skip('', format)
        elif format.hyperlink!=None:
            context.rebuild_hyperlink('', format)
        else:
            context.rebuild_run('', format)
        context.rebuild_bookmark_end(format)
    
    context.clean()
        
def clean_bookmark():
    for k in list(bookmark_dict.keys()):
        if bookmark_dict[k].start!=None and bookmark_dict[k].end!=None:
            del bookmark_dict[k]
            continue
        bookmark_dict[k].skip=True

def clean_fldr():
    if st_fld==[]:
        return
    for f in st_fld:
        f.begin=None
        f.end=None
        f.separate=None
        f.insert_text=[]
        f.skip=True

def translate_docx_with_format(src_docx, dst_docx, translate_func):
    with tempfile.TemporaryDirectory() as tmp:
        zipfile.ZipFile(src_docx).extractall(tmp)
        xml_path = os.path.join(tmp, 'word/document.xml')
        tree = etree.parse(xml_path)
        root = tree.getroot()

        for p in root.xpath('.//w:p', namespaces=NS):
            head, word_format, tail = extract_tokens_with_format(p)
            sentences_format=split_tuples_to_sentences(word_format)
            translates_format=tranlate_algin(sentences_format, translate_func)
            rebuild_para_from_tokens(p, head, translates_format, tail)
            clean_bookmark()
            clean_fldr()

        tree.write(xml_path, xml_declaration=True, encoding='utf-8', standalone=True)
        shutil.make_archive(tmp, 'zip', tmp)
        shutil.move(tmp + '.zip', dst_docx)

# ------------------- 调用 -------------------
if __name__ == '__main__':

    translate_docx_with_format('/dbfs/FileStore/docx/6__Template__2_6_4_Pharmacokinetics_Written_Summary_IND.docx', '/dbfs/FileStore/docx/6__Template__2_6_4_Pharmacokinetics_Written_Summary_IND_format.docx', translate_en2cn)
    print('Saved')