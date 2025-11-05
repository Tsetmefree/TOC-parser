"""
报告书目录解析器 
支持 DOCX, PDF 格式
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Optional

try:
    from docx import Document
except ImportError:
    print("请安装: pip install python-docx")

try:
    import pdfplumber
except ImportError:
    print("请安装: pip install pdfplumber")


class TOCParser:
    """目录解析器"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.suffix = self.file_path.suffix.lower()
        self.toc_entries = []  # 目录条目列表
        
    def parse(self) -> Dict:
        """主解析函数"""
        print(f"📖 开始解析: {self.file_path.name}")
        
        try:
            # 1. 读取文档内容
            if self.suffix == '.docx':
                paragraphs = self._read_docx()
            elif self.suffix == '.pdf':
                paragraphs = self._read_pdf()
            elif self.suffix == '.doc':
                return self._error_output("⚠️ DOC格式请先转换为DOCX")
            else:
                return self._error_output(f"❌ 不支持的格式: {self.suffix}")
            
            # 2. 提取目录条目
            self._extract_toc_entries(paragraphs)
            
            # 3. 构建层级结构
            structured_toc = self._build_structure()
            
            # 4. 生成输出
            return self._generate_output(structured_toc)
        
        except Exception as e:
            print(f"❌ 解析出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._error_output(f"解析错误: {str(e)}")
    
    def _read_docx(self) -> List[str]:
        """读取DOCX文档的所有段落"""
        print("  → 读取DOCX文件...")
        doc = Document(self.file_path)
        paragraphs = [para.text.strip() for para in doc.paragraphs if para.text.strip()]
        print(f"  ✓ 共 {len(paragraphs)} 个段落")
        return paragraphs
    
    def _read_pdf(self) -> List[str]:
        """读取PDF文档的所有文本行"""
        print("  → 读取PDF文件...")
        lines = []
        with pdfplumber.open(self.file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    lines.extend([line.strip() for line in text.split('\n') if line.strip()])
        print(f"  ✓ 共 {len(lines)} 行文本")
        return lines
    
    def _extract_toc_entries(self, paragraphs: List[str]):
        """提取目录条目"""
        print("  → 提取目录条目...")
        
        # 目录条目的正则模式
        patterns = [
            # 匹配: "1.	总  则	1"  (Tab分隔)
            r'^(\d+)\.\s+([^\t]+?)\s+(\d+)$',
            # 匹配: "1.1	编制依据	1"
            r'^(\d+\.\d+)\s+([^\t]+?)\s+(\d+)$',
            # 匹配: "1.1.1	xxx	1"
            r'^(\d+\.\d+\.\d+)\s+([^\t]+?)\s+(\d+)$',
            # 匹配多个空格分隔的情况: "1. 总则    1"
            r'^(\d+\.)\s+(.+?)\s{2,}(\d+)$',
            r'^(\d+\.\d+)\s+(.+?)\s{2,}(\d+)$',
            r'^(\d+\.\d+\.\d+)\s+(.+?)\s{2,}(\d+)$',
        ]
        
        in_toc = False  # 是否在目录部分
        toc_started = False
        
        for text in paragraphs:
            # 检测目录开始
            if re.search(r'^目\s*录$', text):
                in_toc = True
                toc_started = True
                print("  ✓ 找到目录起始")
                continue
            
            # 如果还没找到"目录"标题，跳过
            if not toc_started:
                continue
            
            # 检测目录结束
            if in_toc and (text.startswith('附图') or text.startswith('附件') or text.startswith('附表')):
                in_toc = False
                print("  ✓ 目录提取结束")
                continue
            
            if not in_toc:
                continue
            
            # 尝试匹配目录条目
            matched = False
            for pattern in patterns:
                match = re.match(pattern, text)
                if match:
                    number = match.group(1).rstrip('.')  # 移除末尾的点
                    title = match.group(2).strip()
                    # 清理标题中的多余空格
                    title = re.sub(r'\s+', ' ', title)
                    page = int(match.group(3))
                    
                    # 计算层级
                    level = number.count('.') + 1
                    
                    self.toc_entries.append({
                        'number': number,
                        'title': title,
                        'page': page,
                        'level': level
                    })
                    matched = True
                    break
            
            # 调试：打印未匹配的疑似目录行
            if not matched and in_toc and re.search(r'\d+$', text):
                print(f"  ⚠️  未匹配: {text[:50]}")
        
        print(f"  ✓ 提取了 {len(self.toc_entries)} 个目录条目")
        
        # 打印前10个条目供检查
        print("\n  📋 目录条目预览:")
        for entry in self.toc_entries[:10]:
            indent = "  " * entry['level']
            print(f"     {indent}{entry['number']} {entry['title']} → 第{entry['page']}页")
        
        if len(self.toc_entries) > 10:
            print(f"     ... 还有 {len(self.toc_entries) - 10} 个条目")
    
    def _build_structure(self) -> List[Dict]:
        """构建层级结构"""
        print("\n  → 构建章节层级结构...")
        
        if not self.toc_entries:
            print("  ⚠️  未找到任何目录条目")
            return []
        
        # 构建树形结构
        root = []
        stack = []  # 用于追踪当前各层级的父节点
        
        for entry in self.toc_entries:
            node = {
                'number': entry['number'],
                'title': entry['title'],
                'page': entry['page'],
                'level': entry['level'],
                'children': []
            }
            
            if entry['level'] == 1:
                # 一级章节
                root.append(node)
                stack = [node]
            elif entry['level'] == 2 and len(stack) >= 1:
                # 二级章节，挂到一级下
                stack[0]['children'].append(node)
                if len(stack) > 1:
                    stack[1] = node
                else:
                    stack.append(node)
            elif entry['level'] == 3 and len(stack) >= 2:
                # 三级章节，挂到二级下
                stack[1]['children'].append(node)
                if len(stack) > 2:
                    stack[2] = node
                else:
                    stack.append(node)
        
        print(f"  ✓ 构建了 {len(root)} 个一级章节")
        return root
    
    def _generate_output(self, structured_toc: List[Dict]) -> Dict:
        """生成结构化输出"""
        print("\n  → 生成结构化输出...")
        
        # 统计信息
        total_sections = len(self.toc_entries)
        level_1 = len([e for e in self.toc_entries if e['level'] == 1])
        level_2 = len([e for e in self.toc_entries if e['level'] == 2])
        level_3 = len([e for e in self.toc_entries if e['level'] == 3])
        
        output = {
            'success': True,
            'metadata': {
                'filename': self.file_path.name,
                'format': self.suffix,
                'total_sections': total_sections,
                'level_1_count': level_1,
                'level_2_count': level_2,
                'level_3_count': level_3,
            },
            'toc': structured_toc,
            'flat_list': self.toc_entries  # 同时提供扁平列表
        }
        
        print(f"  ✓ 完成！共 {total_sections} 个章节 (一级:{level_1}, 二级:{level_2}, 三级:{level_3})")
        return output
    
    def _error_output(self, message: str) -> Dict:
        """错误输出"""
        print(message)
        return {
            'success': False,
            'error': message,
            'metadata': {},
            'toc': [],
            'flat_list': []
        }
    
    def save_json(self, output_path: str = None):
        """保存为JSON文件"""
        if output_path is None:
            output_path = self.file_path.stem + "_目录.json"
        
        result = self.parse()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 已保存到: {output_path}")
        return result
    
    def print_tree(self):
        """以树形结构打印目录"""
        result = self.parse()
        
        if not result['success']:
            print(f"\n❌ {result['error']}")
            return
        
        print("\n" + "="*70)
        print("📚 目录结构树")
        print("="*70)
        
        def print_node(node, indent=0):
            prefix = "  " * indent
            icon = "📁" if node['children'] else "📄"
            print(f"{prefix}{icon} {node['number']} {node['title']} (第{node['page']}页)")
            for child in node['children']:
                print_node(child, indent + 1)
        
        for chapter in result['toc']:
            print_node(chapter)
        
        print("\n" + "="*70)
        print(f"统计: 共 {result['metadata']['total_sections']} 个章节")

if __name__ == "__main__":
    import sys
    
    # 从命令行获取文件路径，或使用默认值
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "test.docx"  # 文件路径
    
    # 创建解析器
    parser = TOCParser(file_path)
    
    # 方式1：打印树形结构
    parser.print_tree()
    
    # 方式2：保存为JSON
    parser.save_json("structure.json")
    
    # 方式3：获取原始数据
    # result = parser.parse()
    # if result['success']:
    #     print(f"提取了 {len(result['flat_list'])} 个目录条目")