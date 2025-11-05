from .file_operations import FileOperations
from .line_operations import LineOperations
from .text_operations import TextOperations
from .batch_operations import BatchOperations
from .undo_redo import UndoRedo
from .regex_operations import RegexOperations
from .large_file_operations import LargeFileOperations
from .query_operations import QueryOperations

class koxsFileEditor(
    FileOperations,
    LineOperations,
    TextOperations,
    BatchOperations,
    UndoRedo,
    RegexOperations,
    LargeFileOperations,
    QueryOperations
):
    """
    koxs文件编辑器 - 增强版
    支持批量操作、撤销/重做、大文件处理、正则表达式
    """

    def __init__(self, koxs_filename=None, koxs_chunk_size=8192):
        self.koxs_filename = koxs_filename
        self.koxs_lines = []
        self.koxs_undo_stack = []
        self.koxs_redo_stack = []
        self.koxs_chunk_size = koxs_chunk_size
        self.koxs_is_large_file = False
        self.koxs_file_handle = None
        
        if koxs_filename:
            self.koxs_load_file()

    def __del__(self):
        """koxs析构函数，确保文件句柄关闭"""
        self.koxs_close_large_file()

    def __enter__(self):
        """支持上下文管理器"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文时关闭文件句柄"""
        self.koxs_close_large_file()
    
    def __repr__(self):
        """字符串表示"""
        return f"koxsFileEditor(filename={self.koxs_filename}, lines={len(self.koxs_lines)})"
    
    def __len__(self):
        """返回行数"""
        return len(self.koxs_lines)