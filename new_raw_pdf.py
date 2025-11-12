import re
import json
from typing import List, Dict, Optional, Tuple
import pypdf


class PDFTOCParser:
    '''解析器类'''
    
    def __init__(self, pdf_path: str, max_pages: int = 10, offset : int = 0):
        """
        初始化解析器
        
        Args:
            pdf_path: PDF文件路径
            max_pages: 搜索目录的最大页数
            offset: 实际的第一页与页码的第一页的偏移量
        """
        self.pdf_path = pdf_path
        self.max_pages = max_pages
        self.offset = offset
        self.reader = pypdf.PdfReader(pdf_path)
        
    def extract_toc_text(self) -> List[Tuple[int, str]]:
        """
        提取前N页的文本内容
        
        Returns:
            [(页码, 文本内容), ...]
        """
        toc_pages = []
        num_pages = min(self.max_pages, len(self.reader.pages))
        
        for page_num in range(num_pages):
            page = self.reader.pages[page_num]
            text = page.extract_text()
            toc_pages.append((page_num + 1, text))
            
        return toc_pages
    
    def is_toc_line(self, line: str) -> bool:
        line = line.strip()
        if not line or len(line) < 5:  # 太短的行不可能是目录
            return False
        
        # 排除目录标题本身
        if re.match(r'^(目录|CONTENTS|Contents|TABLE OF CONTENTS)\s*$', line, re.I):
            return False
        
        # 检查行尾页码
        page_match = re.search(r'(?:\.{2,}|…+|\s+)(\d{1,4})\s*$', line)
        if not page_match:
            return False
        
        page_num = int(page_match.group(1))
        if page_num < 1 or page_num > 9999:
            return False
        
        # 检查行首格式
        patterns = [
            r'^第[一二三四五六七八九十百千\d]+[章节条款部分篇]',  
            r'^附[件图表录]',  # 附件/附图/附表/附录
            r'^\d+\.\d+\.\d+\.\d+',  # 1.1.1.1 (四级)
            r'^\d+\.\d+\.\d+',  # 1.1.1
            r'^\d+\.\d+',       # 1.1
            r'^\d+\.',          # 1.
            r'^\d+\s+\S',       # 1 后面有内容
            r'^[IVX]+\.',       # I., II., III. (罗马数字)
        ]
        
        return any(re.match(pattern, line) for pattern in patterns)
    
    def extract_level(self, line: str) -> int:
        """
        提取目录层级
        
        Args:
            line: 目录行
            
        Returns:
            层级(1,2,3...)
        """
        line = line.strip()
        
        # 第X章/节 -> 1级
        if re.match(r'^第[一二三四五六七八九十\d]+[章节]', line):
            return 1
        
        # 附件 -> 1级
        if re.match(r'^附件', line):
            return 1
        
        # 第X条/款/部分 -> 2级
        if re.match(r'^第[一二三四五六七八九十\d]+[条款部分]', line):
            return 2
        
        # 数字格式判断层级 (从最长的开始匹配)
        if re.match(r'^\d+\.\d+\.\d+\.\d+', line):
            return 4
        elif re.match(r'^\d+\.\d+\.\d+', line):
            return 3
        elif re.match(r'^\d+\.\d+', line):
            return 2
        elif re.match(r'^\d+\.', line):
            return 1
        elif re.match(r'^\d+\s', line):
            return 1
            
        return 1
    
    def extract_page_number(self, line: str) -> Optional[int]:
        """
        提取页码
        
        Args:
            line: 目录行
            
        Returns:
            页码数字,如果提取失败返回None
        """
        # 匹配行尾的数字(1-4位数字),前面可能有点号、省略号或空格
        match = re.search(r'[\.…\s]+(\d{1,4})\s*$', line)
        if match:
            page_num = int(match.group(1))
            # 验证页码合理性
            if 1 <= page_num <= 9999:
                return page_num
        return None
    
    def extract_title(self, line: str) -> str:
        """
        提取标题(去除序号、点号分隔符和页码)
        
        Args:
            line: 目录行
            
        Returns:
            标题文本
        """
        line = line.strip()
        
        # 去除行尾的点号/省略号和页码
        title = re.sub(r'[\.…\s]+\d{1,4}\s*$', '', line)
        
        # 去除行首的序号
        title = re.sub(r'^第[一二三四五六七八九十\d]+[章节条款部分]\s*', '', title)
        title = re.sub(r'^附件\s*', '', title)
        title = re.sub(r'^\d+(\.\d+)*\.?\s*', '', title)
        
        # 去除标题中的连续点号(分隔符)
        title = re.sub(r'\.{2,}', '', title)
        title = re.sub(r'…+', '', title)
        
        return title.strip()
    
    def parse_toc_content(self, text: str) -> List[Dict]:
        """
        解析单页的目录内容
        
        Args:
            text: 页面文本
            
        Returns:
            目录项列表
        """
        lines = text.split('\n')
        toc_items = []
        
        for line in lines:
            if self.is_toc_line(line):
                level = self.extract_level(line)
                page_num = self.extract_page_number(line)
                title = self.extract_title(line)
                
                if title and page_num is not None:
                    toc_items.append({
                        'level': level,
                        'title': title,
                        'page_start': page_num,
                        'page_end': None,  # 后续填充
                        'children': [],
                        'content': None # 后续补充
                    })
        
        return toc_items
    
    def extract_pdf_pages(self, page_range: str) -> str:
        """
        提取 PDF 指定页码范围的内容
        示例: "3-5" 或 "1" 或 "10-15"
        会自动应用offset偏移量
        """
        # 解析页码
        if '-' in page_range:
            start, end = map(int, page_range.split('-'))
        else:
            start = end = int(page_range)
        
        # 应用offset
        start += self.offset
        end += self.offset
        
        total_pages = len(self.reader.pages)
        
        if start < 1:
            return f"[错误] 应用offset后起始页 {start} 小于1"
        
        if start > total_pages:
            return f"[错误] 应用offset后起始页 {start} 超出总页数 {total_pages}"
        
        end = min(end, total_pages)
        text = ""
        
        for page_num in range(start - 1, end):  # pypdf 从0开始
            page = self.reader.pages[page_num]
            page_text = page.extract_text()
            if page_text:
                text += f"[第 {page_num + 1} 页 (目录标注: {page_num + 1 - self.offset})]\n{page_text}\n{'='*50}\n"
        
        return text.strip() if text else "[警告] 指定页内容为空"

    def build_content(self, toc_items: List[Dict]) -> List[Dict]:
        """
        递归构建页码范围对应的内容
        只有叶子节点(没有children的目录)才提取content
        
        Args:
            toc_items: 目录项列表
            
        Returns:
            填充了content的目录项列表
        """
        for item in toc_items:
            # 递归处理子节点
            if item['children']:
                self.build_content(item['children'])
                item['content'] = ""  # 父节点content为空
            else:
                # 叶子节点:提取内容
                page_range = f"{item['page_start']}-{item['page_end']}"
                item['content'] = self.extract_pdf_pages(page_range)
        
        return toc_items

    
    def build_page_ranges(self, toc_items: List[Dict]) -> List[Dict]:
        """
        构建页码范围(page_start - page_end)
        
        Args:
            toc_items: 目录项列表
            
        Returns:
            填充了page_end的目录项列表
        """
        for i in range(len(toc_items)):
            if i < len(toc_items) - 1:
                # 当前项的结束页是下一项的开始页，避免漏掉内容
                toc_items[i]['page_end'] = toc_items[i + 1]['page_start']
            else:
                # 最后一项,结束页设为PDF总页数
                toc_items[i]['page_end'] = len(self.reader.pages)
        
        # 格式化page_range字段
        for item in toc_items:
            item['page_range'] = f"{item['page_start']}-{item['page_end']}"
            
        return toc_items
    
    def build_hierarchy(self, toc_items: List[Dict]) -> List[Dict]:
        """
        构建目录层级结构
        
        Args:
            toc_items: 扁平的目录项列表
            
        Returns:
            层级化的目录结构
        """
        if not toc_items:
            return []
        
        root = []
        stack = []  # 用于追踪每个层级的最后一个节点
        
        for item in toc_items:
            level = item['level']
            
            # 弹出所有更高或相同层级的节点
            while stack and stack[-1]['level'] >= level:
                stack.pop()
            
            # 如果是一级节点,直接加到root
            if level == 1 or not stack:
                root.append(item)
            else:
                # 加到父节点的children中
                parent = stack[-1]
                parent['children'].append(item)
            
            stack.append(item)
        
        return root
    
    def fix_parent_page_ranges(self, toc_items: List[Dict]) -> List[Dict]:
        """
        修正父节点的页码范围(递归处理)
        父节点的page_end应该等于最后一个子节点的page_end
        
        Args:
            toc_items: 层级化的目录列表
            
        Returns:
            修正后的目录列表
        """
        for item in toc_items:
            if item['children']:
                # 递归处理子节点
                self.fix_parent_page_ranges(item['children'])
                
                # 父节点的page_end = 最后一个子节点的page_end
                last_child = item['children'][-1]
                item['page_end'] = last_child['page_end']
                item['page_range'] = f"{item['page_start']}-{item['page_end']}"
        
        return toc_items
    
    def parse(self) -> Dict:
        """
        执行完整的目录解析
        
        Returns:
            JSON格式的目录结构
        """
        # 1. 提取文本
        toc_pages = self.extract_toc_text()
        
        # 2. 解析所有目录页
        all_toc_items = []
        for page_num, text in toc_pages:
            items = self.parse_toc_content(text)
            all_toc_items.extend(items)
        
        if not all_toc_items:
            return {
                'status': 'failed',
                'message': '未找到目录内容',
                'toc': []
            }
        
        # 3. 构建页码范围
        all_toc_items = self.build_page_ranges(all_toc_items)

        # 4. 构建层级结构
        hierarchical_toc = self.build_hierarchy(all_toc_items)

        # 5. 修正父节点的页码范围
        hierarchical_toc = self.fix_parent_page_ranges(hierarchical_toc)

        # 6. 提取内容
        hierarchical_toc = self.build_content(hierarchical_toc)
        
        return {
            'status': 'success',
            'total_pages': len(self.reader.pages),
            'toc_items_count': len(all_toc_items),
            'toc': hierarchical_toc
        }
    
    def to_json(self, output_path: Optional[str] = None) -> str:
        """
        输出JSON格式
        
        Args:
            output_path: 输出文件路径,如果为None则返回JSON字符串
            
        Returns:
            JSON字符串
        """
        result = self.parse()
        json_str = json.dumps(result, ensure_ascii=False, indent=2)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
        
        return json_str


# 使用示例
if __name__ == "__main__":
    # 创建解析器
    parser = PDFTOCParser("article.pdf", max_pages=10, offset=10)

    # 测试
    # line = "1. 总 则......................................................................................................................... 1"
    # print(parser.is_toc_line(line))  # 看看返回True还是False
    
    
    # 解析并输出JSON
    json_output = parser.to_json("toc_output.json")
    print(json_output)
    
    # 或者直接获取Python字典
    result = parser.parse()
    print(f"找到 {result['toc_items_count']} 个目录项")
    print(f"PDF总页数: {result['total_pages']}")
    