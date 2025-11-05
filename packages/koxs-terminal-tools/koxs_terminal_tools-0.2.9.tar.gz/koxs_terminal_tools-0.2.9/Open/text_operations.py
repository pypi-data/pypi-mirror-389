class TextOperations:
    """文本操作功能"""
    
    def koxs_replace_text(self, koxs_line_number, koxs_start_pos, koxs_end_pos, koxs_new_text):
        """koxs替换指定位置的文本"""
        if not 0 <= koxs_line_number < len(self.koxs_lines):
            return False
        koxs_old_line = self.koxs_lines[koxs_line_number]
        if isinstance(koxs_old_line, (bytes, bytearray)):
            koxs_old_line = bytes(koxs_old_line)
            koxs_start_pos = max(0, min(koxs_start_pos, len(koxs_old_line)))
            koxs_end_pos = max(koxs_start_pos, min(koxs_end_pos, len(koxs_old_line)))
            if isinstance(koxs_new_text, str):
                koxs_new_text = koxs_new_text.encode('utf-8')
            koxs_new_line = koxs_old_line[:koxs_start_pos] + koxs_new_text + koxs_old_line[koxs_end_pos:]
        else:
            koxs_old_line = str(koxs_old_line)
            koxs_start_pos = max(0, min(koxs_start_pos, len(koxs_old_line)))
            koxs_end_pos = max(koxs_start_pos, min(koxs_end_pos, len(koxs_old_line)))
            koxs_new_line = koxs_old_line[:koxs_start_pos] + koxs_new_text + koxs_old_line[koxs_end_pos:]
        self.koxs_lines[koxs_line_number] = koxs_new_line
        return self.koxs_save_file()

    def koxs_insert_text(self, koxs_line_number, koxs_position, koxs_text):
        """koxs在指定位置插入文本"""
        return self.koxs_replace_text(koxs_line_number, koxs_position, koxs_position, koxs_text)

    def koxs_delete_text(self, koxs_line_number, koxs_start_pos, koxs_end_pos):
        """koxs删除指定位置的文本"""
        return self.koxs_replace_text(koxs_line_number, koxs_start_pos, koxs_end_pos, "")

    def koxs_replace_all(self, koxs_old_text, koxs_new_text, koxs_case_sensitive=False):
        """koxs全局替换文本"""
        koxs_changed = False
        for koxs_idx in range(len(self.koxs_lines)):
            koxs_line = self.koxs_lines[koxs_idx]
            if isinstance(koxs_line, (bytes, bytearray)):
                if isinstance(koxs_old_text, str):
                    koxs_old_bytes = koxs_old_text.encode('utf-8')
                else:
                    koxs_old_bytes = koxs_old_text
                
                if isinstance(koxs_new_text, str):
                    koxs_new_bytes = koxs_new_text.encode('utf-8')
                else:
                    koxs_new_bytes = koxs_new_text
                
                if not koxs_case_sensitive and isinstance(koxs_old_text, str):
                    koxs_line_lower = koxs_line.lower()
                    koxs_old_lower = koxs_old_text.lower().encode('utf-8')
                    koxs_pos = koxs_line_lower.find(koxs_old_lower)
                    while koxs_pos != -1:
                        koxs_line = koxs_line[:koxs_pos] + koxs_new_bytes + koxs_line[koxs_pos + len(koxs_old_bytes):]
                        koxs_line_lower = koxs_line.lower()
                        koxs_pos = koxs_line_lower.find(koxs_old_lower, koxs_pos + len(koxs_new_bytes))
                        koxs_changed = True
                else:
                    koxs_pos = koxs_line.find(koxs_old_bytes)
                    while koxs_pos != -1:
                        koxs_line = koxs_line[:koxs_pos] + koxs_new_bytes + koxs_line[koxs_pos + len(koxs_old_bytes):]
                        koxs_pos = koxs_line.find(koxs_old_bytes, koxs_pos + len(koxs_new_bytes))
                        koxs_changed = True
            else:
                if not koxs_case_sensitive:
                    koxs_line_lower = koxs_line.lower()
                    koxs_old_lower = koxs_old_text.lower()
                    koxs_pos = koxs_line_lower.find(koxs_old_lower)
                    while koxs_pos != -1:
                        koxs_line = koxs_line[:koxs_pos] + koxs_new_text + koxs_line[koxs_pos + len(koxs_old_text):]
                        koxs_line_lower = koxs_line.lower()
                        koxs_pos = koxs_line_lower.find(koxs_old_lower, koxs_pos + len(koxs_new_text))
                        koxs_changed = True
                else:
                    koxs_pos = koxs_line.find(koxs_old_text)
                    while koxs_pos != -1:
                        koxs_line = koxs_line[:koxs_pos] + koxs_new_text + koxs_line[koxs_pos + len(koxs_old_text):]
                        koxs_pos = koxs_line.find(koxs_old_text, koxs_pos + len(koxs_new_text))
                        koxs_changed = True
            
            self.koxs_lines[koxs_idx] = koxs_line
        
        if koxs_changed:
            return self.koxs_save_file()
        return koxs_changed