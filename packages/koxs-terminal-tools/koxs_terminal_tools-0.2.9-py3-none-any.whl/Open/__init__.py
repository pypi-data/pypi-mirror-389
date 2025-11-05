""""
文件操作工具包
提供各种文件处理和文本操作功能
"""

from . import utils
from . import core
from . import text_operations
from . import line_operations
from . import file_operations
from . import batch_operations
from . import large_file_operations
from . import regex_operations
from . import query_operations
from . import undo_redo

# 导入核心功能到包级别，方便直接使用
from .core import FileProcessor
from .text_operations import TextOperations
from .line_operations import LineOperations
from .file_operations import FileOperations
from .batch_operations import BatchOperations
from .large_file_operations import LargeFileOperations
from .regex_operations import RegexOperations
from .query_operations import QueryOperations
from .undo_redo import UndoRedoManager

# 定义包的公开接口
__all__ = [
    'utils',
    'core',
    'text_operations', 
    'line_operations',
    'file_operations',
    'batch_operations',
    'large_file_operations',
    'regex_operations',
    'query_operations',
    'undo_redo',
    'FileProcessor',
    'TextOperations',
    'LineOperations', 
    'FileOperations',
    'BatchOperations',
    'LargeFileOperations',
    'RegexOperations',
    'QueryOperations',
    'UndoRedoManager'
]

# 包版本
__version__ = '1.0.0'
__author__ = 'koxs'
__description__ = '文件操作和文本处理工具包'