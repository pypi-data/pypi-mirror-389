class LineOperations:
    """行操作功能"""
    
    def koxs_get_line(self, koxs_line_number):
        """koxs获取指定行的内容"""
        if 0 <= koxs_line_number < len(self.koxs_lines):
            return self.koxs_lines[koxs_line_number]
        return None

    def koxs_set_line(self, koxs_line_number, koxs_content):
        """koxs设置指定行的内容"""
        while koxs_line_number >= len(self.koxs_lines):
            self.koxs_lines.append('\n' if isinstance(koxs_content, str) else b'\n')
        self.koxs_lines[koxs_line_number] = koxs_content
        return self.koxs_save_file()

    def koxs_insert_line(self, koxs_line_number, koxs_content):
        """koxs在指定行插入新行"""
        if koxs_line_number < 0:
            koxs_line_number = 0
        elif koxs_line_number > len(self.koxs_lines):
            koxs_line_number = len(self.koxs_lines)
        self.koxs_lines.insert(koxs_line_number, koxs_content)
        return self.koxs_save_file()

    def koxs_delete_line(self, koxs_line_number):
        """koxs删除指定行"""
        if 0 <= koxs_line_number < len(self.koxs_lines):
            del self.koxs_lines[koxs_line_number]
            return self.koxs_save_file()
        return False

    def koxs_append_line(self, koxs_content):
        """koxs在文件末尾追加一行"""
        self.koxs_lines.append(koxs_content)
        return self.koxs_save_file()

    def koxs_duplicate_line(self, koxs_line_number):
        """koxs复制指定行"""
        if 0 <= koxs_line_number < len(self.koxs_lines):
            koxs_content = self.koxs_lines[koxs_line_number]
            self.koxs_lines.insert(koxs_line_number + 1, koxs_content)
            return self.koxs_save_file()
        return False

    def koxs_move_line(self, koxs_from_line, koxs_to_line):
        """koxs移动行到新位置"""
        if (0 <= koxs_from_line < len(self.koxs_lines) and 
            0 <= koxs_to_line <= len(self.koxs_lines)):
            koxs_content = self.koxs_lines.pop(koxs_from_line)
            if koxs_to_line > koxs_from_line:
                koxs_to_line -= 1
            self.koxs_lines.insert(koxs_to_line, koxs_content)
            return self.koxs_save_file()
        return False