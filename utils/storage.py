"""
儲存管理 - 處理已回覆貼文的記錄
"""
from pathlib import Path
from typing import Set
from config.settings import FILES


class PostStorage:
    """已回覆貼文的儲存管理"""
    
    def __init__(self, filepath=None):
        """
        初始化儲存管理
        
        Args:
            filepath: 儲存文件路徑，預設使用 settings 中的配置
        """
        self.filepath = Path(filepath) if filepath else Path(FILES["replied_posts"])
        self._cache = None  # 快取已讀取的 ID
    
    def load(self) -> Set[str]:
        """
        讀取已處理過的貼文ID列表
        
        Returns:
            已處理的貼文 ID 集合
        """
        if self._cache is not None:
            return self._cache
        
        try:
            if not self.filepath.exists():
                self._cache = set()
                return self._cache
            
            with open(self.filepath, "r", encoding="utf-8") as f:
                # 讀取所有非空行，去除空白
                self._cache = set(line.strip() for line in f if line.strip())
                return self._cache
        except Exception as e:
            print(f"警告：讀取已回覆記錄文件時出錯: {e}")
            self._cache = set()
            return self._cache
    
    def save(self, post_id: str) -> bool:
        """
        將已處理的貼文ID保存到文件
        
        Args:
            post_id: 貼文 ID
        
        Returns:
            是否成功儲存
        """
        try:
            with open(self.filepath, "a", encoding="utf-8") as f:
                f.write(f"{post_id}\n")
            
            # 更新快取
            if self._cache is not None:
                self._cache.add(post_id)
            
            return True
        except Exception as e:
            print(f"錯誤：儲存貼文ID時出錯: {e}")
            return False
    
    def contains(self, post_id: str) -> bool:
        """
        檢查某個貼文ID是否已記錄
        
        Args:
            post_id: 貼文 ID
        
        Returns:
            是否已記錄
        """
        replied_ids = self.load()
        return post_id in replied_ids
    
    def count(self) -> int:
        """
        獲取已記錄的貼文數量
        
        Returns:
            已記錄的數量
        """
        return len(self.load())
    
    def get_recent(self, n: int = 5) -> list:
        """
        獲取最近記錄的 N 個貼文 ID
        
        Args:
            n: 要獲取的數量
        
        Returns:
            最近的貼文 ID 列表
        """
        try:
            if not self.filepath.exists():
                return []
            
            with open(self.filepath, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
                return lines[-n:] if len(lines) > n else lines
        except Exception as e:
            print(f"警告：讀取最近記錄時出錯: {e}")
            return []
    
    def clear(self) -> bool:
        """
        清空所有記錄（謹慎使用）
        
        Returns:
            是否成功清空
        """
        try:
            if self.filepath.exists():
                self.filepath.unlink()
            self._cache = set()
            return True
        except Exception as e:
            print(f"錯誤：清空記錄時出錯: {e}")
            return False
    
    def export_to_list(self) -> list:
        """
        將所有記錄匯出為列表
        
        Returns:
            貼文 ID 列表
        """
        return list(self.load())


# 全局儲存實例
_storage_instance = None

def get_storage(filepath=None, reinit=False):
    """
    獲取全局儲存實例
    
    Args:
        filepath: 儲存文件路徑
        reinit: 是否強制重新初始化
    
    Returns:
        PostStorage 實例
    """
    global _storage_instance
    
    if _storage_instance is None or reinit:
        _storage_instance = PostStorage(filepath=filepath)
    
    return _storage_instance
