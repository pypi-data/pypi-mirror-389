class BatchOperations:
    """批量操作功能"""
    
    def koxs_batch_operations(self, koxs_operations):
        """koxs批量执行操作"""
        self.koxs_save_to_undo_stack()
        
        results = []
        for operation in koxs_operations:
            op_type = operation.get('type')
            try:
                if op_type == 'set_line':
                    result = self.koxs_set_line(operation['line'], operation['content'])
                elif op_type == 'insert_line':
                    result = self.koxs_insert_line(operation['line'], operation['content'])
                elif op_type == 'delete_line':
                    result = self.koxs_delete_line(operation['line'])
                elif op_type == 'replace_text':
                    result = self.koxs_replace_text(
                        operation['line'], operation['start'], 
                        operation['end'], operation['content']
                    )
                elif op_type == 'append_line':
                    result = self.koxs_append_line(operation['content'])
                elif op_type == 'replace_regex':
                    result = self.koxs_replace_regex(
                        operation['pattern'], operation['replacement'], 
                        operation.get('flags', 0)
                    )
                else:
                    result = False
                
                results.append((op_type, result))
                
            except Exception as e:
                results.append((op_type, False, str(e)))
        
        return results

    def koxs_batch_replace(self, koxs_replacements):
        """koxs批量替换文本"""
        self.koxs_save_to_undo_stack()
        
        for replacement in koxs_replacements:
            if 'line' in replacement:
                self.koxs_replace_text(
                    replacement['line'],
                    replacement.get('start', 0),
                    replacement.get('end', len(self.koxs_lines[replacement['line']])),
                    replacement['content']
                )
        return True

    def koxs_batch_delete_lines(self, koxs_line_numbers):
        """koxs批量删除行"""
        self.koxs_save_to_undo_stack()
        
        # 从大到小排序删除，避免索引变化
        for line_num in sorted(koxs_line_numbers, reverse=True):
            if 0 <= line_num < len(self.koxs_lines):
                del self.koxs_lines[line_num]
        return True

    def koxs_batch_insert_lines(self, koxs_insertions):
        """koxs批量插入行"""
        self.koxs_save_to_undo_stack()
        
        for insertion in sorted(koxs_insertions, key=lambda x: x['line'], reverse=True):
            self.koxs_insert_line(insertion['line'], insertion['content'])
        return True