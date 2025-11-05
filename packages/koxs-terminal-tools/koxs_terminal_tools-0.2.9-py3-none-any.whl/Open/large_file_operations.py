class LargeFileOperations:
    """大文件操作功能"""
    
    def koxs_process_large_file(self, koxs_callback, koxs_chunk_size=None):
        """koxs处理大文件（逐块处理）"""
        if not self.koxs_is_large_file or not self.koxs_file_handle:
            return False
        
        chunk_size = koxs_chunk_size or self.koxs_chunk_size
        self.koxs_file_handle.seek(0)
        
        results = []
        while True:
            chunk = self.koxs_file_handle.read(chunk_size)
            if not chunk:
                break
            
            result = koxs_callback(chunk)
            results.append(result)
        
        return results

    def koxs_search_large_file(self, koxs_search_term):
        """koxs在大文件中搜索"""
        if not self.koxs_is_large_file:
            return self.koxs_search_text(koxs_search_term)
        
        def search_callback(chunk):
            positions = []
            start = 0
            while True:
                pos = chunk.find(koxs_search_term, start)
                if pos == -1:
                    break
                positions.append(pos)
                start = pos + len(koxs_search_term)
            return positions
        
        return self.koxs_process_large_file(search_callback)

    def koxs_get_line_chunk(self, koxs_start_line, koxs_chunk_size=100):
        """koxs获取文件块（用于大文件浏览）"""
        if self.koxs_is_large_file:
            # 大文件模式需要特殊处理
            if not self.koxs_file_handle:
                return []
            
            lines = []
            self.koxs_file_handle.seek(0)
            for i, line in enumerate(self.koxs_file_handle):
                if i >= koxs_start_line and i < koxs_start_line + koxs_chunk_size:
                    lines.append(line)
                elif i >= koxs_start_line + koxs_chunk_size:
                    break
            return lines
        else:
            # 小文件直接返回
            return self.koxs_lines[koxs_start_line:koxs_start_line + koxs_chunk_size]