#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Koxs颜色核心模块 - 返回字符串版本
"""

import sys
import platform

# 检测操作系统，Windows需要特殊处理
IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    try:
        import ctypes
        # 启用Windows终端颜色支持
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except:
        pass

# 重置所有样式
koxs_reset = '\033[0m'

# 基础颜色（变量名）
koxs_color_black = '\033[30m'
koxs_color_red = '\033[31m'
koxs_color_green = '\033[32m'
koxs_color_yellow = '\033[33m'
koxs_color_blue = '\033[34m'
koxs_color_magenta = '\033[35m'
koxs_color_cyan = '\033[36m'
koxs_color_white = '\033[37m'

# 亮色（变量名）
koxs_color_bright_red = '\033[91m'
koxs_color_bright_green = '\033[92m'
koxs_color_bright_yellow = '\033[93m'
koxs_color_bright_blue = '\033[94m'
koxs_color_bright_magenta = '\033[95m'
koxs_color_bright_cyan = '\033[96m'

# 样式（变量名）
koxs_style_bold = '\033[1m'
koxs_style_underline = '\033[4m'

# 颜色函数（返回字符串，函数名）
def koxs_black(text):
    return f"{koxs_color_black}{text}{koxs_reset}"

def koxs_red(text):
    return f"{koxs_color_red}{text}{koxs_reset}"

def koxs_green(text):
    return f"{koxs_color_green}{text}{koxs_reset}"

def koxs_yellow(text):
    return f"{koxs_color_yellow}{text}{koxs_reset}"

def koxs_blue(text):
    return f"{koxs_color_blue}{text}{koxs_reset}"

def koxs_magenta(text):
    return f"{koxs_color_magenta}{text}{koxs_reset}"

def koxs_cyan(text):
    return f"{koxs_color_cyan}{text}{koxs_reset}"

def koxs_white(text):
    return f"{koxs_color_white}{text}{koxs_reset}"

def koxs_bright_red(text):
    return f"{koxs_color_bright_red}{text}{koxs_reset}"

def koxs_bright_green(text):
    return f"{koxs_color_bright_green}{text}{koxs_reset}"

def koxs_bright_yellow(text):
    return f"{koxs_color_bright_yellow}{text}{koxs_reset}"

def koxs_bright_blue(text):
    return f"{koxs_color_bright_blue}{text}{koxs_reset}"

def koxs_bright_magenta(text):
    return f"{koxs_color_bright_magenta}{text}{koxs_reset}"

def koxs_bright_cyan(text):
    return f"{koxs_color_bright_cyan}{text}{koxs_reset}"

def koxs_bold(text):
    return f"{koxs_style_bold}{text}{koxs_reset}"

def koxs_underline(text):
    return f"{koxs_style_underline}{text}{koxs_reset}"