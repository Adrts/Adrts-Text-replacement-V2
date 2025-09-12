import os
import re
import glob
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import codecs
from tkinter.scrolledtext import ScrolledText
import threading

class RuleDialog(tk.Toplevel):
    """添加/编辑规则的对话框"""
    def __init__(self, parent, title="添加替换规则", rule=None):
        super().__init__(parent)
        self.parent = parent
        self.title(title)
        self.rule = rule
        self.result = None
        
        self.font = ('SimHei', 10)
        self.option_add("*Font", self.font)
        self.create_widgets()
        self.geometry("500x350")
        self.transient(parent)
        self.grab_set()
        self.parent.wait_window(self)

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="规则别名:").grid(row=0, column=0, sticky=tk.W, pady=10)
        self.alias_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.alias_var, width=50).grid(row=0, column=1, sticky=tk.W, pady=10)
        
        ttk.Label(main_frame, text="查找内容:").grid(row=1, column=0, sticky=tk.NW, pady=10)
        self.find_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.find_var, width=50).grid(row=1, column=1, sticky=tk.W, pady=10)
        
        ttk.Label(main_frame, text="替换内容:").grid(row=2, column=0, sticky=tk.NW, pady=10)
        self.replace_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.replace_var, width=50).grid(row=2, column=1, sticky=tk.W, pady=10)
        
        self.use_regex = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            main_frame, 
            text="使用正则表达式匹配", 
            variable=self.use_regex
        ).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        if self.rule:
            self.alias_var.set(self.rule["alias"])
            self.find_var.set(self.rule["find"])
            self.replace_var.set(self.rule["replace"])
            if "use_regex" in self.rule:
                self.use_regex.set(self.rule["use_regex"])
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="确认", command=self.on_confirm).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="取消", command=self.on_cancel).pack(side=tk.LEFT, padx=10)
        
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)

    def on_confirm(self):
        alias = self.alias_var.get().strip()
        find_str = self.find_var.get()
        replace_str = self.replace_var.get()
        
        if not alias:
            messagebox.showwarning("警告", "请输入规则别名")
            return
            
        self.result = {
            "alias": alias,
            "find": find_str,
            "replace": replace_str,
            "use_regex": self.use_regex.get()
        }
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()

class BatchTextReplacer:
    def __init__(self, root):
        self.root = root
        self.root.title("批量文本替换程序")
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)
        
        self.font_config()
        self.replace_rules = []
        # 扩展编码列表，支持全球主要语言
        self.encodings = [
            "自动检测", 
            # 通用Unicode编码
            "utf-8", "utf-8-sig", "utf-16", "utf-16-le", "utf-16-be", "utf-32",
            # 中文编码
            "gbk", "gb2312", "gb18030", "big5", "big5-hkscs",
            # 日文编码
            "shift_jis", "euc-jp", "iso-2022-jp",
            # 韩文编码
            "euc-kr", "iso-2022-kr", "cp949",
            # 西欧语言编码
            "iso-8859-1", "iso-8859-2", "iso-8859-3", "iso-8859-4", 
            "iso-8859-5", "iso-8859-6", "iso-8859-7", "iso-8859-8", 
            "iso-8859-9", "iso-8859-10", "iso-8859-13", "iso-8859-15",
            # Windows系统编码
            "windows-1250", "windows-1251", "windows-1252", "windows-1253",
            "windows-1254", "windows-1255", "windows-1256", "windows-1257",
            "windows-1258",
            # 其他常用编码
            "koi8-r", "koi8-u", "mac-cyrillic", "mac-roman"
        ]
        self.simple_mode = tk.BooleanVar(value=False)
        self.create_widgets()
        self.running = False

    def font_config(self):
        default_font = ('SimHei', 10)
        self.root.option_add("*Font", default_font)

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # 1. 文件夹选择部分
        folder_frame = ttk.LabelFrame(main_frame, text="文件夹选择", padding="5")
        folder_frame.grid(row=0, column=0, columnspan=2, sticky=tk.W+tk.E+tk.N+tk.S, pady=5)
        
        ttk.Label(folder_frame, text="文件夹路径:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.folder_path = tk.StringVar()
        folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_path)
        folder_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=2, padx=5)
        ttk.Button(folder_frame, text="浏览...", command=self.browse_folder).grid(row=0, column=2, padx=5, pady=2)
        
        self.recursive_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(folder_frame, text="递归处理子文件夹", variable=self.recursive_var).grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=2)
        folder_frame.columnconfigure(1, weight=1)
        
        # 2. 替换筛选部分
        filter_frame = ttk.LabelFrame(main_frame, text="文件筛选", padding="5")
        filter_frame.grid(row=1, column=0, columnspan=2, sticky=tk.W+tk.E+tk.N+tk.S, pady=5)
        
        ttk.Label(filter_frame, text="筛选条件 (如 *.txt 或 *.*):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.filter_pattern = tk.StringVar(value="*.*")
        ttk.Entry(filter_frame, textvariable=self.filter_pattern).grid(row=0, column=1, sticky=tk.W+tk.E, pady=2, padx=5)
        filter_frame.columnconfigure(1, weight=1)
        
        # 3. 编码选择部分
        encoding_frame = ttk.LabelFrame(main_frame, text="编码设置", padding="5")
        encoding_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W+tk.E+tk.N+tk.S, pady=5)
        
        ttk.Label(encoding_frame, text="读取编码:").grid(row=0, column=0, sticky=tk.W, pady=2, padx=5)
        self.read_encoding = tk.StringVar(value="自动检测")
        # 使用更宽的下拉框以显示长编码名称
        read_encoding_combo = ttk.Combobox(
            encoding_frame, 
            textvariable=self.read_encoding, 
            values=self.encodings, 
            state="readonly",
            width=25
        )
        read_encoding_combo.grid(row=0, column=1, sticky=tk.W, pady=2, padx=5)
        
        ttk.Label(encoding_frame, text="保存编码:").grid(row=0, column=2, sticky=tk.W, pady=2, padx=5)
        self.write_encoding = tk.StringVar(value="保持原有编码")
        write_encoding_combo = ttk.Combobox(
            encoding_frame, 
            textvariable=self.write_encoding, 
            values=["保持原有编码"] + self.encodings[1:],  # 排除自动检测
            state="readonly",
            width=25
        )
        write_encoding_combo.grid(row=0, column=3, sticky=tk.W, pady=2, padx=5)
        encoding_frame.columnconfigure(4, weight=1)
        
        # 4. 规则部分
        rules_frame = ttk.LabelFrame(main_frame, text="替换规则", padding="5")
        rules_frame.grid(row=3, column=0, sticky=tk.W+tk.E+tk.N+tk.S, pady=5)
        
        rules_frame.columnconfigure(0, weight=1)
        rules_frame.rowconfigure(0, weight=1)
        rules_frame.update_idletasks()
        rules_frame.configure(width=500)
        rules_frame.grid_propagate(False)
        
        # 滚动条框架
        scroll_frame = ttk.Frame(rules_frame)
        scroll_frame.grid(row=0, column=0, sticky=tk.NSEW)
        
        # 垂直滚动条
        v_scrollbar = ttk.Scrollbar(scroll_frame, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 水平滚动条
        h_scrollbar = ttk.Scrollbar(scroll_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 规则列表
        self.rules_tree = ttk.Treeview(
            scroll_frame, 
            columns=("alias", "find", "replace", "regex"), 
            show="headings", 
            height=6,
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )
        
        v_scrollbar.config(command=self.rules_tree.yview)
        h_scrollbar.config(command=self.rules_tree.xview)
        
        # 设置列标题
        self.rules_tree.heading("alias", text="规则别名")
        self.rules_tree.heading("find", text="查找内容")
        self.rules_tree.heading("replace", text="替换内容")
        self.rules_tree.heading("regex", text="正则")
        
        # 列宽设置
        self.rules_tree.column("alias", width=90, stretch=tk.YES, minwidth=80)
        self.rules_tree.column("find", width=150, stretch=tk.YES, minwidth=120)
        self.rules_tree.column("replace", width=150, stretch=tk.YES, minwidth=120)
        self.rules_tree.column("regex", width=60, stretch=tk.NO, minwidth=60)
        
        self.rules_tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # 规则按钮
        rules_btn_frame = ttk.Frame(rules_frame)
        rules_btn_frame.grid(row=1, column=0, sticky=tk.EW, pady=5)
        
        ttk.Button(rules_btn_frame, text="添加规则", command=self.add_rule).pack(side=tk.LEFT, padx=2)
        ttk.Button(rules_btn_frame, text="编辑规则", command=self.edit_rule).pack(side=tk.LEFT, padx=2)
        ttk.Button(rules_btn_frame, text="删除规则", command=self.delete_rule).pack(side=tk.LEFT, padx=2)
        
        # 规则导入导出
        rule_io_frame = ttk.Frame(rules_frame)
        rule_io_frame.grid(row=2, column=0, sticky=tk.EW, pady=5)
        
        ttk.Button(rule_io_frame, text="保存规则", command=self.save_rules).pack(side=tk.LEFT, padx=2)
        ttk.Button(rule_io_frame, text="加载规则", command=self.load_rules).pack(side=tk.LEFT, padx=2)
        
        # 5. 消息部分
        message_frame = ttk.LabelFrame(main_frame, text="操作消息", padding="5")
        message_frame.grid(row=3, column=1, sticky=tk.W+tk.E+tk.N+tk.S, pady=5)
        
        self.message_text = ScrolledText(message_frame, wrap=tk.WORD, state=tk.DISABLED, height=10)
        self.message_text.pack(fill=tk.BOTH, expand=True)
        
        message_ctrl_frame = ttk.Frame(message_frame)
        message_ctrl_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        
        ttk.Checkbutton(
            message_ctrl_frame, 
            text="简洁模式（不显示单个文件详情）", 
            variable=self.simple_mode
        ).pack(side=tk.LEFT)
        
        ttk.Button(message_ctrl_frame, text="清空消息", command=self.clear_messages).pack(side=tk.RIGHT, padx=5)
        
        # 6. 操作按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, sticky=tk.W+tk.E, pady=10)
        
        self.find_only_btn = ttk.Button(btn_frame, text="仅查找", command=self.start_find_only)
        self.find_only_btn.pack(side=tk.LEFT, padx=10)
        
        self.replace_btn = ttk.Button(btn_frame, text="执行替换", command=self.start_replace)
        self.replace_btn.pack(side=tk.LEFT, padx=10)
        
        self.stop_btn = ttk.Button(btn_frame, text="终止操作", command=self.stop_processing, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        
        # 7. 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=5, column=0, columnspan=2, sticky=tk.W+tk.E)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)

    def add_rule(self):
        dialog = RuleDialog(self.root, "添加替换规则")
        if dialog.result:
            self.replace_rules.append(dialog.result)
            self.update_rules_tree()

    def edit_rule(self):
        selected = self.rules_tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择要编辑的规则")
            return
            
        index = int(self.rules_tree.item(selected[0])["tags"][0])
        rule = self.replace_rules[index]
        
        dialog = RuleDialog(self.root, "编辑替换规则", rule)
        if dialog.result:
            self.replace_rules[index] = dialog.result
            self.update_rules_tree()

    def delete_rule(self):
        selected = self.rules_tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择要删除的规则")
            return
            
        if messagebox.askyesno("确认", "确定要删除选中的规则吗?"):
            index = int(self.rules_tree.item(selected[0])["tags"][0])
            del self.replace_rules[index]
            self.update_rules_tree()

    def update_rules_tree(self):
        for item in self.rules_tree.get_children():
            self.rules_tree.delete(item)
            
        for i, rule in enumerate(self.replace_rules):
            regex_flag = "是" if rule.get("use_regex", False) else "否"
            self.rules_tree.insert(
                "", tk.END, 
                values=(rule["alias"], rule["find"], rule["replace"], regex_flag), 
                tags=(i,)
            )

    def save_rules(self):
        if not self.replace_rules:
            messagebox.showinfo("提示", "没有可保存的规则")
            return
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(self.replace_rules, f, ensure_ascii=False, indent=2)
                self.add_message(f"规则已成功保存到 {file_path}")
            except Exception as e:
                self.add_message(f"保存规则失败: {str(e)}")

    def load_rules(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.replace_rules = json.load(f)
                self.update_rules_tree()
                self.add_message(f"已从 {file_path} 加载规则")
            except Exception as e:
                self.add_message(f"加载规则失败: {str(e)}")

    def add_message(self, message, force=False):
        if self.simple_mode.get() and not force:
            return
            
        self.message_text.config(state=tk.NORMAL)
        self.message_text.insert(tk.END, message + "\n")
        self.message_text.see(tk.END)
        self.message_text.config(state=tk.DISABLED)

    def clear_messages(self):
        self.message_text.config(state=tk.NORMAL)
        self.message_text.delete(1.0, tk.END)
        self.message_text.config(state=tk.DISABLED)

    def detect_encoding(self, file_path):
        # 扩展编码检测列表，优先检测常用编码
        encodings_to_try = [
            "utf-8", "utf-8-sig", "gbk", "gb2312", "gb18030", 
            "big5", "shift_jis", "euc-jp", "windows-1252",
            "iso-8859-1", "utf-16", "utf-16-le", "utf-16-be"
        ]
        
        for encoding in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read(1024)  # 读取部分内容测试编码
                return encoding
            except UnicodeDecodeError:
                continue
                
        return "utf-8"  # 默认编码

    def read_file_with_encoding(self, file_path):
        read_enc = self.read_encoding.get()
        
        if read_enc == "自动检测":
            encoding = self.detect_encoding(file_path)
            self.add_message(f"自动检测 {file_path} 编码为: {encoding}")
        else:
            encoding = read_enc
            
        try:
            with codecs.open(file_path, 'r', encoding=encoding, errors='replace') as f:
                content = f.read()
            return content, encoding
        except Exception as e:
            raise Exception(f"读取文件失败: {str(e)}")

    def write_file_with_encoding(self, file_path, content, original_encoding):
        write_enc = self.write_encoding.get()
        
        if write_enc == "保持原有编码":
            encoding = original_encoding
        else:
            encoding = write_enc
            
        try:
            with codecs.open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
            return True
        except Exception as e:
            raise Exception(f"写入文件失败: {str(e)}")

    def find_files(self):
        folder = self.folder_path.get()
        pattern = self.filter_pattern.get()
        
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("错误", "请选择有效的文件夹")
            return []
            
        if not pattern:
            messagebox.showerror("错误", "请输入筛选条件")
            return []
            
        files = []
        recursive = self.recursive_var.get()
        
        if recursive:
            for root_dir, _, _ in os.walk(folder):
                files.extend(glob.glob(os.path.join(root_dir, pattern)))
        else:
            files = glob.glob(os.path.join(folder, pattern))
        
        self.add_message(f"共找到 {len(files)} 个符合条件的文件", force=True)
        return files

    def process_file(self, file_path, replace_mode=True):
        try:
            content, original_encoding = self.read_file_with_encoding(file_path)
            modified = False
            matches = 0
            
            for rule in self.replace_rules:
                find_str = rule["find"]
                replace_str = rule["replace"]
                use_regex = rule.get("use_regex", False)
                
                if use_regex:
                    find_pattern = find_str
                else:
                    find_pattern = re.escape(find_str)
                
                count = len(re.findall(find_pattern, content))
                if count > 0:
                    matches += count
                    if replace_mode:
                        new_content = re.sub(find_pattern, replace_str, content)
                        if new_content != content:
                            content = new_content
                            modified = True
            
            if not self.simple_mode.get():
                if matches > 0:
                    self.add_message(f"在 {file_path} 中找到 {matches} 处匹配")
                    if replace_mode and modified:
                        self.add_message(f"已成功替换 {file_path}")
                else:
                    self.add_message(f"{file_path} 中未找到匹配内容")
            
            if replace_mode and modified:
                self.write_file_with_encoding(file_path, content, original_encoding)
                
            return (True, matches, None)
                
        except Exception as e:
            error_msg = f"处理 {file_path} 时出错: {str(e)}"
            self.add_message(error_msg, force=True)
            return (False, 0, error_msg)

    def process_files(self, replace_mode=True):
        if not self.replace_rules:
            messagebox.showinfo("提示", "请先添加替换规则")
            self.status_var.set("就绪")
            self.find_only_btn.config(state=tk.NORMAL)
            self.replace_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            return
            
        files = self.find_files()
        if not files:
            self.add_message("未找到符合条件的文件", force=True)
            self.status_var.set("就绪")
            self.find_only_btn.config(state=tk.NORMAL)
            self.replace_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            return
        
        if self.simple_mode.get():
            self.add_message("开始处理文件...", force=True)
        
        total_files = len(files)
        processed = 0
        success_count = 0
        total_matches = 0
        replaced_files = 0
        failed_files = []
        
        for file_path in files:
            if not self.running:
                self.add_message("操作已终止", force=True)
                break
                
            processed += 1
            self.status_var.set(f"工作中 - 处理 {processed}/{total_files}")
            
            success, matches, error = self.process_file(file_path, replace_mode)
            total_matches += matches
            
            if success:
                success_count += 1
                if replace_mode and matches > 0:
                    replaced_files += 1
            else:
                failed_files.append((file_path, error))
        
        self.add_message("\n===== 处理总结 =====", force=True)
        if self.running:
            if replace_mode:
                self.add_message(f"替换完成 - 共处理 {processed} 个文件", force=True)
                self.add_message(f"实际修改: {replaced_files} 个文件", force=True)
            else:
                self.add_message(f"查找完成 - 共处理 {processed} 个文件", force=True)
        else:
            self.add_message(f"操作终止 - 已处理 {processed}/{total_files} 个文件", force=True)
            if replace_mode:
                self.add_message(f"已修改: {replaced_files} 个文件", force=True)
            
        self.add_message(f"成功: {success_count} 个文件", force=True)
        self.add_message(f"找到匹配: {total_matches} 处", force=True)
        
        if failed_files:
            self.add_message(f"失败: {len(failed_files)} 个文件", force=True)
            if not self.simple_mode.get():
                for file, error in failed_files:
                    self.add_message(f"  - {file}: {error}", force=True)
        
        self.running = False
        self.status_var.set("就绪")
        self.find_only_btn.config(state=tk.NORMAL)
        self.replace_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def stop_processing(self):
        if self.running:
            self.running = False
            self.add_message("正在终止操作...请稍候", force=True)
            self.status_var.set("正在终止...")

    def start_find_only(self):
        self.start_processing(replace_mode=False)

    def start_replace(self):
        if messagebox.askyesno("确认替换", "确定要执行替换操作吗？这可能会修改多个文件的内容。"):
            self.start_processing(replace_mode=True)

    def start_processing(self, replace_mode):
        self.running = True
        self.find_only_btn.config(state=tk.DISABLED)
        self.replace_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("工作中")
        self.add_message("开始处理...", force=True)
        
        thread = threading.Thread(target=self.process_files, args=(replace_mode,))
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = BatchTextReplacer(root)
    root.mainloop()
