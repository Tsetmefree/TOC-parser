"""
目录结构化解析器
支持 DOCX, PDF 格式的目录提取
"""

import re
import json
from pathlib import Path
from typing import List, Dict

# pip install python-docx pdfplumber
from docx import Document
import pdfplumber


class TOCParser:
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.suffix = self.file_path.suffix.lower()
        self.toc_entries = []
        
    def parse(self) -> Dict:
        print(f"📖 开始解析: {self.file_path.name}")
        
        try:
            if self.suffix == '.docx':
                paragraphs = self._read_docx()
            elif self.suffix == '.pdf':
                paragraphs = self._read_pdf()
            else:
                return self._error_result(f"不支持的格式: {self.suffix}")
            
            self._extract_toc(paragraphs)
            
            structured = self._build_tree()
            
            return self._generate_result(structured)
        
        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()
            return self._error_result(str(e))
    
    def _read_docx(self) -> List[str]:
        print("  → 读取DOCX...")
        doc = Document(self.file_path)
        paras = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        print(f"  ✓ {len(paras)} 个段落")
        return paras
    
    def _read_pdf(self) -> List[str]:
        print("  → 读取PDF...")
        lines = []
        with pdfplumber.open(self.file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    lines.extend([ln.strip() for ln in text.split('\n') if ln.strip()])
        print(f"  ✓ {len(lines)} 行文本")
        return lines
    
    def _extract_toc(self, paragraphs: List[str]):
        print("  → 提取目录...")
        
        # 正则模式：按优先级排序
        patterns = [
            # PDF格式: "1. 总则............1" 或 "1.1 编制依据........1"
            (r'^(\d+)\.\s+(.+?)\.{2,}(\d+)$', 'dot-fill'),
            (r'^(\d+\.\d+)\s+(.+?)\.{2,}(\d+)$', 'dot-fill'),
            (r'^(\d+\.\d+\.\d+)\s+(.+?)\.{2,}(\d+)$', 'dot-fill'),
            
            # DOCX格式: Tab或多空格分隔
            (r'^(\d+)\.\s+([^\t]+?)\t+(\d+)$', 'tab'),
            (r'^(\d+\.\d+)\s+([^\t]+?)\t+(\d+)$', 'tab'),
            (r'^(\d+)\.\s+(.+?)\s{3,}(\d+)$', 'space'),
            (r'^(\d+\.\d+)\s+(.+?)\s{3,}(\d+)$', 'space'),
        ]
        
        in_toc = False
        match_count = 0
        
        for text in paragraphs:
            if re.search(r'^目\s*录$', text):
                in_toc = True
                print("  ✓ 找到目录")
                continue
            
            if not in_toc:
                continue
            
            if text.startswith(('附图', '附件', '附表', '第一章', '1 ')):
                if not text.startswith('1.'):  # 避免把"1.1"当成结束
                    print("  ✓ 目录结束")
                    break
            
            for pattern, ptype in patterns:
                match = re.match(pattern, text)
                if match:
                    number = match.group(1).rstrip('.')
                    title = match.group(2).strip()
                    page = match.group(3)
                    
                    # 清理标题
                    title = re.sub(r'\s+', ' ', title)  # 多空格→单空格
                    title = re.sub(r'\.+$', '', title)   # 去尾部点号
                    
                    # 计算层级
                    level = number.count('.') + 1
                    
                    self.toc_entries.append({
                        'number': number,
                        'title': title,
                        'page': int(page),
                        'level': level
                    })
                    
                    match_count += 1
                    if match_count <= 5:  # 只显示前5个
                        print(f"     ✓ {number} {title} (第{page}页) [{ptype}]")
                    
                    break
        
        print(f"  ✓ 提取 {len(self.toc_entries)} 个条目")
        if len(self.toc_entries) > 5:
            print(f"     ... 还有 {len(self.toc_entries) - 5} 个")
    
    def _build_tree(self) -> List[Dict]:
        print("  → 构建树形结构...")
        
        if not self.toc_entries:
            return []
        
        root = []
        stack = []
        
        for entry in self.toc_entries:
            node = {
                'number': entry['number'],
                'title': entry['title'],
                'page': entry['page'],
                'level': entry['level'],
                'children': []
            }
            
            level = entry['level']
            
            if level == 1:
                root.append(node)
                stack = [node]
            elif level == 2 and len(stack) >= 1:
                stack[0]['children'].append(node)
                stack = stack[:1] + [node]
            elif level == 3 and len(stack) >= 2:
                stack[1]['children'].append(node)
                stack = stack[:2] + [node]
        
        level_counts = {}
        for e in self.toc_entries:
            level_counts[e['level']] = level_counts.get(e['level'], 0) + 1
        
        print(f"  ✓ {len(root)} 个一级章节", end='')
        if level_counts:
            print(f" (共{len(self.toc_entries)}个: ", end='')
            print(', '.join([f"{k}级:{v}个" for k, v in sorted(level_counts.items())]), end='')
            print(")")
        else:
            print()
        
        return root
    
    def _generate_result(self, structured: List[Dict]) -> Dict:
        level_stats = {}
        for e in self.toc_entries:
            level_stats[e['level']] = level_stats.get(e['level'], 0) + 1
        
        return {
            'success': True,
            'metadata': {
                'filename': self.file_path.name,
                'format': self.suffix,
                'total_sections': len(self.toc_entries),
                'level_stats': level_stats
            },
            'toc': structured,
            'flat_list': self.toc_entries
        }
    
    def _error_result(self, msg: str) -> Dict:
        print(f"❌ {msg}")
        return {
            'success': False,
            'error': msg,
            'metadata': {},
            'toc': [],
            'flat_list': []
        }
    
    def save_json(self, output_path: str = None):
        if not output_path:
            output_path = self.file_path.stem + "_目录.json"
        
        result = self.parse()
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 已保存: {output_path}")
        return result
    
    def print_tree(self):
        result = self.parse()
        
        if not result['success']:
            return
        
        print("\n" + "="*60)
        print("📚 目录结构")
        print("="*60)
        
        def show(node, indent=0):
            icon = "📁" if node['children'] else "📄"
            prefix = "  " * indent
            print(f"{prefix}{icon} {node['number']} {node['title']} (p.{node['page']})")
            for child in node['children']:
                show(child, indent + 1)
        
        for chapter in result['toc']:
            show(chapter)
        
        stats = result['metadata']['level_stats']
        print("\n" + "="*60)
        print(f"统计: {result['metadata']['total_sections']} 个章节 ({stats})")


if __name__ == "__main__":
    import sys
    
    file_path = sys.argv[1] if len(sys.argv) > 1 else "test.pdf" # 文件路径
    
    parser = TOCParser(file_path)
    parser.print_tree()
    
    # 可选: 保存JSON
    # parser.save_json()