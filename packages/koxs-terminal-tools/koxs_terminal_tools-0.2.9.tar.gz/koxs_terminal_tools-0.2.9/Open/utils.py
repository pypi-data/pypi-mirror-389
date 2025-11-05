class Utils:
    """工具函数"""
    
    def koxs_validate_line_number(self, koxs_line_number):
        """验证行号是否有效"""
        return 0 <= koxs_line_number < len(self.koxs_lines)
    
    def koxs_validate_position(self, koxs_line_number, koxs_position):
        """验证位置是否有效"""
        if not self.koxs_validate_line_number(koxs_line_number):
            return False
        line_length = len(str(self.koxs_lines[koxs_line_number]))
        return 0 <= koxs_position <= line_length
    
    def koxs_ensure_line_exists(self, koxs_line_number, koxs_default_content='\n'):
        """确保行存在，如果不存在则创建"""
        while koxs_line_number >= len(self.koxs_lines):
            self.koxs_lines.append(koxs_default_content)