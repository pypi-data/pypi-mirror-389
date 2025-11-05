"""
KOXS 终端颜色工具包
提供终端颜色输出和样式控制功能
包含打印版本和字符串返回版本
"""

from .koxs import (
    # 颜色变量
    koxs_reset,
    koxs_color_black, koxs_color_red, koxs_color_green, koxs_color_yellow,
    koxs_color_blue, koxs_color_magenta, koxs_color_cyan, koxs_color_white,
    koxs_color_bright_red, koxs_color_bright_green, koxs_color_bright_yellow,
    koxs_color_bright_blue, koxs_color_bright_magenta, koxs_color_bright_cyan,
    koxs_style_bold, koxs_style_underline,
    
    # 打印函数
    koxs_print_black, koxs_print_red, koxs_print_green, koxs_print_yellow,
    koxs_print_blue, koxs_print_magenta, koxs_print_cyan, koxs_print_white,
    koxs_print_bright_red, koxs_print_bright_green, koxs_print_bright_yellow,
    koxs_print_bright_blue, koxs_print_bright_magenta, koxs_print_bright_cyan,
    koxs_print_bold, koxs_print_underline
)

from .koxy import (
    # 字符串返回函数
    koxs_black, koxs_red, koxs_green, koxs_yellow, koxs_blue, koxs_magenta,
    koxs_cyan, koxs_white, koxs_bright_red, koxs_bright_green, koxs_bright_yellow,
    koxs_bright_blue, koxs_bright_magenta, koxs_bright_cyan, koxs_bold, koxs_underline
)

# 为方便使用，创建简化的别名
# 颜色变量别名
reset = koxs_reset
black = koxs_color_black
red = koxs_color_red
green = koxs_color_green
yellow = koxs_color_yellow
blue = koxs_color_blue
magenta = koxs_color_magenta
cyan = koxs_color_cyan
white = koxs_color_white
bright_red = koxs_color_bright_red
bright_green = koxs_color_bright_green
bright_yellow = koxs_color_bright_yellow
bright_blue = koxs_color_bright_blue
bright_magenta = koxs_color_bright_magenta
bright_cyan = koxs_color_bright_cyan
bold = koxs_style_bold
underline = koxs_style_underline

# 打印函数别名
print_black = koxs_print_black
print_red = koxs_print_red
print_green = koxs_print_green
print_yellow = koxs_print_yellow
print_blue = koxs_print_blue
print_magenta = koxs_print_magenta
print_cyan = koxs_print_cyan
print_white = koxs_print_white
print_bright_red = koxs_print_bright_red
print_bright_green = koxs_print_bright_green
print_bright_yellow = koxs_print_bright_yellow
print_bright_blue = koxs_print_bright_blue
print_bright_magenta = koxs_print_bright_magenta
print_bright_cyan = koxs_print_bright_cyan
print_bold = koxs_print_bold
print_underline = koxs_print_underline

# 字符串返回函数别名（使用koxy中的函数）
color_black = koxs_black
color_red = koxs_red
color_green = koxs_green
color_yellow = koxs_yellow
color_blue = koxs_blue
color_magenta = koxs_magenta
color_cyan = koxs_cyan
color_white = koxs_white
color_bright_red = koxs_bright_red
color_bright_green = koxs_bright_green
color_bright_yellow = koxs_bright_yellow
color_bright_blue = koxs_bright_blue
color_bright_magenta = koxs_bright_magenta
color_bright_cyan = koxs_bright_cyan
color_bold = koxs_bold
color_underline = koxs_underline

# 定义包的公开接口
__all__ = [
    # 模块
    'koxs', 'koxy',
    
    # 颜色变量
    'koxs_reset', 'reset',
    'koxs_color_black', 'black', 'koxs_color_red', 'red', 'koxs_color_green', 'green',
    'koxs_color_yellow', 'yellow', 'koxs_color_blue', 'blue', 'koxs_color_magenta', 'magenta',
    'koxs_color_cyan', 'cyan', 'koxs_color_white', 'white',
    'koxs_color_bright_red', 'bright_red', 'koxs_color_bright_green', 'bright_green',
    'koxs_color_bright_yellow', 'bright_yellow', 'koxs_color_bright_blue', 'bright_blue',
    'koxs_color_bright_magenta', 'bright_magenta', 'koxs_color_bright_cyan', 'bright_cyan',
    'koxs_style_bold', 'bold', 'koxs_style_underline', 'underline',
    
    # 打印函数
    'koxs_print_black', 'print_black', 'koxs_print_red', 'print_red',
    'koxs_print_green', 'print_green', 'koxs_print_yellow', 'print_yellow',
    'koxs_print_blue', 'print_blue', 'koxs_print_magenta', 'print_magenta',
    'koxs_print_cyan', 'print_cyan', 'koxs_print_white', 'print_white',
    'koxs_print_bright_red', 'print_bright_red', 'koxs_print_bright_green', 'print_bright_green',
    'koxs_print_bright_yellow', 'print_bright_yellow', 'koxs_print_bright_blue', 'print_bright_blue',
    'koxs_print_bright_magenta', 'print_bright_magenta', 'koxs_print_bright_cyan', 'print_bright_cyan',
    'koxs_print_bold', 'print_bold', 'koxs_print_underline', 'print_underline',
    
    # 字符串返回函数
    'koxs_black', 'color_black', 'koxs_red', 'color_red', 'koxs_green', 'color_green',
    'koxs_yellow', 'color_yellow', 'koxs_blue', 'color_blue', 'koxs_magenta', 'color_magenta',
    'koxs_cyan', 'color_cyan', 'koxs_white', 'color_white', 'koxs_bright_red', 'color_bright_red',
    'koxs_bright_green', 'color_bright_green', 'koxs_bright_yellow', 'color_bright_yellow',
    'koxs_bright_blue', 'color_bright_blue', 'koxs_bright_magenta', 'color_bright_magenta',
    'koxs_bright_cyan', 'color_bright_cyan', 'koxs_bold', 'color_bold', 'koxs_underline', 'color_underline'
]

# 包元数据
__version__ = '1.0.0'
__author__ = 'koxs'
__description__ = 'KOXS 终端颜色输出和样式控制工具包'