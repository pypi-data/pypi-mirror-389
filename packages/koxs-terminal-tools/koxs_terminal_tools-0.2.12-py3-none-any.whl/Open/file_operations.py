import os

class FileOperations:
    """文件操作功能"""
    
    def koxs_set_filename(self, koxs_new_filename):
        """koxs设置文件名"""
        self.koxs_close_large_file()
        self.koxs_filename = koxs_new_filename
        self.koxs_lines = []
        self.koxs_undo_stack = []
        self.koxs_redo_stack = []
        self.koxs_is_large_file = False
        
        if koxs_new_filename:
            self.koxs_load_file()
        return True

    def koxs_get_filename(self):
        """koxs获取当前文件名"""
        return self.koxs_filename

    def koxs_load_file(self, koxs_filename=None):
        """koxs加载文件内容到内存（支持大文件）"""
        if koxs_filename:
            self.koxs_filename = koxs_filename
        
        if not self.koxs_filename:
            print("koxs错误: 未设置文件名")
            return False
        
        try:
            # 检查文件大小决定加载方式
            file_size = os.path.getsize(self.koxs_filename)
            
            if file_size > 1024 * 1024:  # 大于1MB视为大文件
                self.koxs_is_large_file = True
                self.koxs_file_handle = open(self.koxs_filename, 'r', encoding='utf-8')
                print(f"koxs提示: 大文件模式 ({file_size//1024}KB)")
                return True
            else:
                # 小文件正常加载
                with open(self.koxs_filename, 'r', encoding='utf-8') as koxs_file:
                    self.koxs_lines = koxs_file.readlines()
                return True
                
        except FileNotFoundError:
            self.koxs_lines = []
            print(f"koxs提示: 文件 '{self.koxs_filename}' 不存在，已创建空文件")
            return True
        except Exception as koxs_error:
            print(f"koxs加载文件错误: {koxs_error}")
            self.koxs_lines = []
            return False

    def koxs_close_large_file(self):
        """koxs关闭大文件句柄"""
        if self.koxs_file_handle:
            self.koxs_file_handle.close()
            self.koxs_file_handle = None

    def koxs_save_file(self, koxs_filename=None):
        """koxs保存内容到文件"""
        if koxs_filename:
            self.koxs_filename = koxs_filename
        
        if not self.koxs_filename:
            print("koxs错误: 未设置文件名")
            return False
        
        # 保存当前状态到撤销栈
        self.koxs_save_to_undo_stack()
            
        try:
            with open(self.koxs_filename, 'w', encoding='utf-8') as koxs_file:
                koxs_file.writelines(self.koxs_lines)
            return True
        except Exception as koxs_error:
            print(f"koxs保存文件时出错: {koxs_error}")
            return False

    def koxs_save_as(self, koxs_new_filename):
        """koxs另存为文件"""
        self.koxs_filename = koxs_new_filename
        return self.koxs_save_file()