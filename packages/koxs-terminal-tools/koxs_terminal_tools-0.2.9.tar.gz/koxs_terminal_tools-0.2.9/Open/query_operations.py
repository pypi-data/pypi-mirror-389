class QueryOperations:
    """查询操作功能"""
    
    def koxs_get_all_lines(self):
        """koxs获取所有行内容"""
        return self.koxs_lines.copy()

    def koxs_clear_content(self):
        """koxs清空内容"""
        self.koxs_lines = []
        return True

    def koxs_clear_file(self):
        """koxs清空文件内容"""
        self.koxs_lines = []
        return self.koxs_save_file()

    def koxs_get_line_count(self):
        """koxs获取总行数"""
        return len(self.koxs_lines)

    def koxs_search_text(self, koxs_search_term, koxs_case_sensitive=False):
        """koxs搜索文本"""
        koxs_results = []
        for koxs_idx, koxs_line in enumerate(self.koxs_lines):
            if isinstance(koxs_line, (bytes, bytearray)):
                if isinstance(koxs_search_term, str):
                    koxs_search_bytes = koxs_search_term.encode('utf-8')
                else:
                    koxs_search_bytes = koxs_search_term
                if not koxs_case_sensitive and isinstance(koxs_search_term, str):
                    koxs_line_lower = koxs_line.lower()
                    koxs_search_lower = koxs_search_term.lower().encode('utf-8')
                    koxs_pos = koxs_line_lower.find(koxs_search_lower)
                else:
                    koxs_pos = koxs_line.find(koxs_search_bytes)
                if koxs_pos != -1:
                    koxs_results.append((koxs_idx, koxs_pos))
            else:
                if not koxs_case_sensitive:
                    koxs_line_lower = koxs_line.lower()
                    koxs_search_lower = koxs_search_term.lower()
                    koxs_pos = koxs_line_lower.find(koxs_search_lower)
                else:
                    koxs_pos = koxs_line.find(koxs_search_term)
                if koxs_pos != -1:
                    koxs_results.append((koxs_idx, koxs_pos))
        return koxs_results

    def koxs_get_file_info(self):
        """koxs获取文件信息"""
        koxs_total_chars = 0
        for koxs_line in self.koxs_lines:
            koxs_total_chars += len(str(koxs_line))
        return {
            'koxs_filename': self.koxs_filename,
            'koxs_line_count': len(self.koxs_lines),
            'koxs_total_chars': koxs_total_chars,
            'koxs_is_binary': any(isinstance(line, (bytes, bytearray)) for line in self.koxs_lines),
            'koxs_is_large_file': self.koxs_is_large_file
        }