"""
日誌系統 - 統一的日誌輸出管理
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
from config.settings import FILES

class AgentLogger:
    """統一的日誌管理類"""
    
    def __init__(self, log_file=None, console_level=logging.INFO, file_level=logging.DEBUG):
        """
        初始化日誌系統
        
        Args:
            log_file: 日誌文件路徑，None 則不寫入文件
            console_level: 控制台輸出級別
            file_level: 文件輸出級別
        """
        self.logger = logging.getLogger("ReplyAgent")
        self.logger.setLevel(logging.DEBUG)
        
        # 避免重複添加 handler
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # 控制台 handler - 使用彩色輸出
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_level)
        console_formatter = ColoredFormatter(
            '%(levelname_colored)s %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # 文件 handler - 詳細記錄
        if log_file:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(file_level)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def section(self, message):
        """輸出分隔線區段"""
        self.logger.info("=" * 50)
        self.logger.info(message)
        self.logger.info("=" * 50)
    
    def post_header(self, index, total, post_id):
        """輸出貼文標題行"""
        self.logger.info(f"\n[{index}/{total}] 貼文ID: {post_id}")
    
    def post_title(self, title):
        """輸出貼文標題"""
        self.logger.info(f"  標題: {title}")
    
    def post_content_preview(self, content, max_length=100):
        """輸出貼文內容預覽"""
        preview = content[:max_length] + ("..." if len(content) > max_length else "")
        self.logger.info(f"  內容預覽: {preview}")
    
    def success(self, message):
        """成功訊息（綠色勾號）"""
        self.logger.info(f"  ✓ {message}")
    
    def skip(self, message):
        """跳過訊息（圓圈叉號）"""
        self.logger.info(f"  ⊗ {message}")
    
    def reject(self, message):
        """拒絕訊息（斜線圓圈）"""
        self.logger.info(f"  ⊘ {message}")
    
    def action(self, message):
        """動作訊息（箭頭）"""
        self.logger.info(f"  → {message}")
    
    def back(self, message):
        """返回訊息（左箭頭）"""
        self.logger.info(f"  ← {message}")
    
    def ai(self, message):
        """AI 相關訊息（機器人圖標）"""
        self.logger.info(f"  🤖 {message}")
    
    def reply(self, message):
        """回覆內容訊息（對話框圖標）— 完整顯示"""
        self.logger.info(f"  💬 生成的回覆:")
        for line in message.splitlines():
            self.logger.info(f"      {line}")
    
    def warning(self, message):
        """警告訊息"""
        self.logger.warning(f"  ⚠ {message}")
    
    def error(self, message):
        """錯誤訊息"""
        self.logger.error(f"  ✗ {message}")
    
    def info(self, message):
        """一般訊息"""
        self.logger.info(message)
    
    def debug(self, message):
        """除錯訊息"""
        self.logger.debug(message)
    
    def summary(self, processed, skipped, total_recorded):
        """輸出統計摘要"""
        self.section("處理完成！")
        self.info(f"  新處理: {processed} 個貼文")
        self.info(f"  跳過: {skipped} 個貼文")
        self.info(f"  總計已記錄: {total_recorded} 個貼文")
        self.info("=" * 50)


class ColoredFormatter(logging.Formatter):
    """帶顏色的日誌格式化器"""
    
    # ANSI 顏色碼
    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[37m',      # 白色
        'WARNING': '\033[33m',   # 黃色
        'ERROR': '\033[31m',     # 紅色
        'CRITICAL': '\033[35m',  # 紫色
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # 添加彩色的級別名稱
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname_colored = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        else:
            record.levelname_colored = levelname
        
        return super().format(record)


# 全局日誌實例
_logger_instance = None

def get_logger(log_file=None, reinit=False):
    """
    獲取全局日誌實例
    
    Args:
        log_file: 日誌文件路徑
        reinit: 是否強制重新初始化
    
    Returns:
        AgentLogger 實例
    """
    global _logger_instance
    
    if _logger_instance is None or reinit:
        if log_file is None:
            log_file = FILES.get("log_file")
        _logger_instance = AgentLogger(log_file=log_file)
    
    return _logger_instance
