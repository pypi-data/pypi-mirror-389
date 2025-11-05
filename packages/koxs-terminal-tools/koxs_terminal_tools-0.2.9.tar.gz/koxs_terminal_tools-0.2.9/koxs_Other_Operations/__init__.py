"""
KOXS 其他操作工具包
提供编码转换和文件整理功能
"""

from . import koxs编码
from . import 整理

# 导入主要功能到包级别，方便直接使用
from .koxs编码 import (
    encode_text,
    decode_text,
    detect_encoding,
    convert_file_encoding,
    batch_convert_encoding
)

from .整理 import (
    organize_files,
    auto_organize,
    get_organization_rules
)

# 定义包的公开接口
__all__ = [
    # 模块
    'koxs编码',
    '整理',
    
    # 编码功能
    'encode_text',
    'decode_text', 
    'detect_encoding',
    'convert_file_encoding',
    'batch_convert_encoding',
    
    # 整理功能
    'organize_files',
    'auto_organize',
    'get_organization_rules'
]

# 包元数据
__version__ = '1.0.0'
__author__ = 'koxs'
__description__ = 'KOXS 编码转换和文件整理工具包'