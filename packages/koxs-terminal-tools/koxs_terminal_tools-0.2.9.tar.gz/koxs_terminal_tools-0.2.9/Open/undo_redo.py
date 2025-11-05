class UndoRedo:
    """撤销重做功能"""
    
    def koxs_save_to_undo_stack(self):
        """koxs保存当前状态到撤销栈"""
        if self.koxs_lines:
            self.koxs_undo_stack.append(self.koxs_lines.copy())
            self.koxs_redo_stack.clear()  # 新的操作清空重做栈
            # 限制撤销栈大小
            if len(self.koxs_undo_stack) > 50:
                self.koxs_undo_stack.pop(0)

    def koxs_undo(self):
        """koxs撤销操作"""
        if self.koxs_undo_stack:
            # 保存当前状态到重做栈
            if self.koxs_lines:
                self.koxs_redo_stack.append(self.koxs_lines.copy())
            
            # 恢复上一个状态
            self.koxs_lines = self.koxs_undo_stack.pop()
            return True
        return False

    def koxs_redo(self):
        """koxs重做操作"""
        if self.koxs_redo_stack:
            # 保存当前状态到撤销栈
            if self.koxs_lines:
                self.koxs_undo_stack.append(self.koxs_lines.copy())
            
            # 恢复重做状态
            self.koxs_lines = self.koxs_redo_stack.pop()
            return True
        return False

    def koxs_get_undo_count(self):
        """koxs获取可撤销次数"""
        return len(self.koxs_undo_stack)

    def koxs_get_redo_count(self):
        """koxs获取可重做次数"""
        return len(self.koxs_redo_stack)