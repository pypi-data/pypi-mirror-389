import os
import re
from datetime import datetime
from typing import List, Dict, Any

# 修复导入 - 使用相对导入
from .parsers import (
    ChatGPTParser, DeepSeekParser, ClaudeParser, UniversalParser
)

class AIExporter:
    """多平台AI对话导出器"""
    
    def __init__(self):
        self.parsers = [
            ChatGPTParser(),
            DeepSeekParser(), 
            ClaudeParser(),
            UniversalParser()  # 通用解析器放在最后
        ]
    
    def detect_platform(self, file_path: str):
        """检测文件格式并返回合适的解析器"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        for parser in self.parsers:
            if parser.can_parse(file_path):
                print(f"✅ 检测到 {parser.get_platform_name()} 格式")
                return parser
        
        print("⚠️  无法识别格式，使用通用解析器")
        return self.parsers[-1]
    
    def convert(self, input_path: str, output_dir: str = "./ai_output"):
        """转换入口函数"""
        os.makedirs(output_dir, exist_ok=True)
        
        # 检测文件格式
        parser = self.detect_platform(input_path)
        
        # 解析对话
        print("📖 正在解析对话...")
        conversations = parser.parse(input_path)
        
        if not conversations:
            print("❌ 未找到可转换的对话数据")
            return
        
        print(f"📝 找到 {len(conversations)} 个对话")
        
        # 转换每个对话
        successful = 0
        for i, conversation in enumerate(conversations, 1):
            try:
                print(f"🔄 正在转换第 {i}/{len(conversations)} 个对话...")
                self._convert_single(conversation, output_dir, parser.get_platform_name())
                successful += 1
            except Exception as e:
                print(f"❌ 转换对话时出错: {e}")
                continue
        
        print(f"✅ 成功转换 {successful}/{len(conversations)} 个对话")
    
    def _convert_single(self, conversation: Dict[str, Any], output_dir: str, platform: str):
        """转换单个对话为Markdown"""
        title = conversation.get('title', '未命名对话')
        messages = conversation.get('messages', [])
        
        if not messages:
            raise ValueError("对话中没有消息内容")
        
        # 生成安全文件名
        safe_title = self._safe_filename(title)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{safe_title}.md"
        filepath = os.path.join(output_dir, filename)
        
        # 构建Markdown内容
        md_content = self._build_markdown(title, messages, platform)
        
        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"📄 已创建: {filename}")
    
    def _safe_filename(self, filename: str) -> str:
        """生成安全的文件名"""
        # 移除或替换非法字符
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 限制长度
        if len(safe_name) > 100:
            safe_name = safe_name[:100]
        return safe_name
    
    def _build_markdown(self, title: str, messages: List[Dict[str, Any]], platform: str) -> str:
        """构建Markdown内容"""
        lines = []
        
        # YAML front matter
        lines.append("---")
        lines.append(f"title: {title}")
        lines.append(f"platform: {platform}")
        lines.append(f"export_date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"message_count: {len(messages)}")
        lines.append("---")
        lines.append("")
        
        # 标题和元信息
        lines.append(f"# {title}")
        lines.append("")
        lines.append(f"**平台**: {platform}  |  **消息数量**: {len(messages)}  |  **导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # 添加消息
        for i, msg in enumerate(messages, 1):
            role = msg['role']
            content = msg['content']
            
            # 角色显示名称映射
            role_display = {
                'user': '👤 用户',
                'human': '👤 用户',
                'assistant': '🤖 助手', 
                'system': '⚙️ 系统',
                'tool': '🛠️ 工具'
            }.get(role, f'❓ {role}')
            
            lines.append(f"## {role_display}")
            lines.append("")
            
            # 处理消息内容
            if content.strip():
                lines.append(content.strip())
            else:
                lines.append("*(空消息)*")
            
            lines.append("")
            
            # 添加分隔线（除了最后一条消息）
            if i < len(messages):
                lines.append("---")
                lines.append("")
        
        return '\n'.join(lines)

def convert(input_path: str, output_dir: str = "./ai_output"):
    """便捷转换函数"""
    exporter = AIExporter()
    exporter.convert(input_path, output_dir)

def main():
    """命令行入口点"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='将多平台AI对话导出为Markdown格式',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
支持平台:
  • ChatGPT (.zip 导出文件)
  • DeepSeek (.jsonl 文件)
  • Claude (.json 文件)
  • 其他AI平台 (通用JSON/JSONL格式)

示例:
  ai-export chatgpt_export.zip
  ai-export deepseek_conversation.jsonl -o ./output
  ai-export claude_chat.json
        """
    )
    
    parser.add_argument('input_file', help='输入文件路径')
    parser.add_argument('-o', '--output', default='./ai_output', 
                       help='输出目录 (默认: ./ai_output)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"❌ 错误: 文件 '{args.input_file}' 不存在")
        return
    
    print("🚀 AI对话导出工具")
    print("=" * 50)
    
    exporter = AIExporter()
    exporter.convert(args.input_file, args.output)
    
    print("=" * 50)
    print("🎉 转换完成！")

if __name__ == "__main__":
    main()