import re

class RegexOperations:
    """正则表达式操作功能"""
    
    def koxs_replace_regex(self, koxs_pattern, koxs_replacement, koxs_flags=0):
        """koxs使用正则表达式替换文本"""
        self.koxs_save_to_undo_stack()
        
        changed = False
        for i in range(len(self.koxs_lines)):
            if isinstance(self.koxs_lines[i], str):
                new_line, count = re.subn(
                    koxs_pattern, koxs_replacement, 
                    self.koxs_lines[i], flags=koxs_flags
                )
                if count > 0:
                    self.koxs_lines[i] = new_line
                    changed = True
        
        if changed:
            return True
        return False

    def koxs_find_regex(self, koxs_pattern, koxs_flags=0):
        """koxs使用正则表达式查找"""
        results = []
        for i, line in enumerate(self.koxs_lines):
            if isinstance(line, str):
                matches = re.finditer(koxs_pattern, line, flags=koxs_flags)
                for match in matches:
                    results.append({
                        'line': i,
                        'start': match.start(),
                        'end': match.end(),
                        'match': match.group(),
                        'groups': match.groups()
                    })
        return results