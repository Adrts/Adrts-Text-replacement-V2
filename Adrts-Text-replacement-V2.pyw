import os
import re
import glob
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import codecs
from tkinter.scrolledtext import ScrolledText
import threading
import queue
import traceback
from typing import List, Tuple, Dict, Optional


# 全局常量定义 - 所有外显文本均已宏定义
# 基础配置
DEFAULT_FONT = ('SimHei', 10)
RULE_DIALOG_GEOMETRY = "500x350"
MAIN_WINDOW_TITLE = "批量文本替换程序"
MAIN_WINDOW_GEOMETRY = "1100x700"
MAIN_WINDOW_MIN_SIZE = "900x600"

# 布局
DIALOG_FRAME_PADDING = "15"
MAIN_FRAME_PADDING = "10"
FRAME_PADDING = "5"
WIDGET_PADX = 5
WIDGET_PADY = 5
BUTTON_PADX = 10
BUTTON_PADY = 10

# 提示信息
PROMPT_ENTER_ALIAS = "请输入规则别名"
PROMPT_SELECT_RULE_EDIT = "请先选择要编辑的规则"
PROMPT_SELECT_RULE_DELETE = "请先选择要删除的规则"
PROMPT_CONFIRM_DELETE = "确定要删除选中的规则吗?"
PROMPT_NO_RULES_TO_SAVE = "没有可保存的规则"
PROMPT_NO_FILES_FOUND = "未找到符合条件的文件"
PROMPT_NO_RULES = "请先添加替换规则"
PROMPT_INVALID_FOLDER = "请选择有效的文件夹"
PROMPT_ENTER_FILTER = "请输入筛选条件"
PROMPT_ENTER_FIND = "请输入查找内容"
PROMPT_CONFIRM_REPLACE = "确定要执行替换操作吗？这可能会修改多个文件的内容。"
PROMPT_WARNING = "警告"
PROMPT_INFO = "提示"
PROMPT_CONFIRM = "确认"
PROMPT_ERROR = "错误"

# 操作消息
MSG_RULES_SAVED = "规则已成功保存到 {}"
MSG_SAVE_RULES_FAILED_IO = "保存规则失败（文件操作错误）: {}"
MSG_SAVE_RULES_FAILED_JSON = "保存规则失败（JSON格式错误）: {}"
MSG_RULES_LOADED = "已从 {} 加载规则"
MSG_LOAD_RULES_FAILED_IO = "加载规则失败（文件操作错误）: {}"
MSG_LOAD_RULES_FAILED_JSON = "加载规则失败（JSON解析错误）: {}"
MSG_ENCODING_DETECTED = "自动检测 {} 编码为: {}"
MSG_FILE_MATCHES_FOUND = "在 {} 中找到 {} 处匹配"
MSG_FILE_REPLACED = "已成功替换 {}"
MSG_FILE_NO_MATCHES = "{} 中未找到匹配内容"
MSG_FILE_PROCESS_ERROR = "处理 {} 时出错: {}"
MSG_TOTAL_FILES_FOUND = "共找到 {} 个符合条件的文件"
MSG_START_PROCESSING = "开始处理文件..."
MSG_OPERATION_ABORTED = "操作已终止"
MSG_PROCESSING_SUMMARY = "\n===== 处理总结 ====="
MSG_REPLACE_COMPLETE = "替换完成 - 共处理 {} 个文件"
MSG_FIND_COMPLETE = "查找完成 - 共处理 {} 个文件"
MSG_OPERATION_TERMINATED = "操作终止 - 已处理 {}/{} 个文件"
MSG_REPLACED_FILES = "实际修改: {} 个文件"
MSG_ALREADY_REPLACED_FILES = "已修改: {} 个文件"
MSG_SUCCESSFUL_FILES = "成功: {} 个文件"
MSG_TOTAL_MATCHES = "找到匹配: {} 处"
MSG_FAILED_FILES = "失败: {} 个文件"
MSG_ABORTING_OPERATION = "正在终止操作..."
MSG_START_PROCESS = "开始处理..."
MSG_INVALID_REGEX = "规则正则表达式无效: {}"
MSG_INVALID_RULES_FORMAT = "规则文件格式无效: {}"

# TreeView列
ALIAS_COL_NAME = "规则别名"
FIND_COL_NAME = "查找内容"
REPLACE_COL_NAME = "替换内容"
REGEX_COL_NAME = "正则"
ALIAS_COL_WIDTH = 90
ALIAS_COL_MIN_WIDTH = 80
FIND_COL_WIDTH = 150
FIND_COL_MIN_WIDTH = 120
REPLACE_COL_WIDTH = 150
REPLACE_COL_MIN_WIDTH = 120
REGEX_COL_WIDTH = 60
REGEX_COL_MIN_WIDTH = 60

# 状态信息
STATUS_READY = "就绪"
STATUS_WORKING = "工作中"
STATUS_PROCESSING = "工作中 - 处理 {}/{}"
STATUS_TERMINATING = "正在终止..."

# 按钮文本
BTN_BROWSE = "浏览..."
BTN_ADD_RULE = "添加规则"
BTN_EDIT_RULE = "编辑规则"
BTN_DELETE_RULE = "删除规则"
BTN_SAVE_RULES = "保存规则"
BTN_LOAD_RULES = "加载规则"
BTN_CLEAR_MSG = "清空消息"
BTN_FIND_ONLY = "仅查找"
BTN_REPLACE = "执行替换"
BTN_STOP = "终止操作"
BTN_CONFIRM = "确认"
BTN_CANCEL = "取消"

# 标签文本
LABEL_FOLDER_PATH = "文件夹路径:"
LABEL_RECURSIVE = "递归处理子文件夹"
LABEL_FILE_FILTER_FRAME = "文件筛选"  # 框架标题
LABEL_FILE_FILTER_PROMPT = "筛选条件 (如 *.txt 或 *.*):"  # 输入框前的提示
LABEL_READ_ENCODING = "读取编码:"
LABEL_WRITE_ENCODING = "保存编码:"
LABEL_RULE_ALIAS = "规则别名:"
LABEL_FIND_CONTENT = "查找内容:"
LABEL_REPLACE_CONTENT = "替换内容:"
LABEL_REGEX = "使用正则表达式匹配"
LABEL_FOLDER_SELECT = "文件夹选择"
LABEL_ENCODING_SETTINGS = "编码设置"
LABEL_REPLACE_RULES = "替换规则"
LABEL_OPERATION_MESSAGES = "操作消息"
LABEL_SIMPLE_MODE = "快速模式（不显示单个文件详情）"

# 对话框标题
DLG_TITLE_ADD_RULE = "添加替换规则"
DLG_TITLE_EDIT_RULE = "编辑替换规则"


class RuleDialog(tk.Toplevel):
    """添加/编辑规则的对话框"""
    def __init__(self, parent, title=DLG_TITLE_ADD_RULE, rule=None):
        super().__init__(parent)
        self.parent = parent
        self.title(title)
        self.rule = rule
        self.result = None
        
        self.font = DEFAULT_FONT
        self.option_add("*Font", self.font)
        self.create_widgets()
        self.geometry(RULE_DIALOG_GEOMETRY)
        self.transient(parent)
        self.grab_set()
        self.parent.wait_window(self)

    def create_widgets(self):
        main_frame = ttk.Frame(self, padding=DIALOG_FRAME_PADDING)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text=LABEL_RULE_ALIAS).grid(row=0, column=0, sticky=tk.W, pady=BUTTON_PADY)
        self.alias_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.alias_var, width=50).grid(row=0, column=1, sticky=tk.W, pady=BUTTON_PADY)
        
        ttk.Label(main_frame, text=LABEL_FIND_CONTENT).grid(row=1, column=0, sticky=tk.NW, pady=BUTTON_PADY)
        self.find_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.find_var, width=50).grid(row=1, column=1, sticky=tk.W, pady=BUTTON_PADY)
        
        ttk.Label(main_frame, text=LABEL_REPLACE_CONTENT).grid(row=2, column=0, sticky=tk.NW, pady=BUTTON_PADY)
        self.replace_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.replace_var, width=50).grid(row=2, column=1, sticky=tk.W, pady=BUTTON_PADY)
        
        self.use_regex = tk.BooleanVar(value=False)
        ttk.Checkbutton(main_frame, text=LABEL_REGEX, variable=self.use_regex).grid(
            row=3, column=0, columnspan=2, sticky=tk.W, pady=BUTTON_PADY)
        
        if self.rule:
            self.alias_var.set(self.rule["alias"])
            self.find_var.set(self.rule["find"])
            self.replace_var.set(self.rule["replace"])
            self.use_regex.set(self.rule.get("use_regex", False))
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=BUTTON_PADY)
        
        ttk.Button(btn_frame, text=BTN_CONFIRM, command=self.on_confirm).pack(side=tk.LEFT, padx=BUTTON_PADX)
        ttk.Button(btn_frame, text=BTN_CANCEL, command=self.on_cancel).pack(side=tk.LEFT, padx=BUTTON_PADX)
        
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)

    def on_confirm(self):
        if not (alias := self.alias_var.get().strip()):
            messagebox.showwarning(PROMPT_WARNING, PROMPT_ENTER_ALIAS)
            return
        if not self.find_var.get():
            messagebox.showwarning(PROMPT_WARNING, PROMPT_ENTER_FIND)
            return
        if self.use_regex.get():
            try:
                re.compile(self.find_var.get())
            except re.error as e:
                messagebox.showerror(PROMPT_ERROR, MSG_INVALID_REGEX.format(e))
                return

        self.result = {
            "alias": alias,
            "find": self.find_var.get(),
            "replace": self.replace_var.get(),
            "use_regex": self.use_regex.get()
        }
        self.destroy()

    def on_cancel(self):
        self.result = None
        self.destroy()


class BatchTextReplacer:
    def __init__(self, root):
        self.root = root
        self.root.title(MAIN_WINDOW_TITLE)
        self.root.geometry(MAIN_WINDOW_GEOMETRY)
        self.root.minsize(*MAIN_WINDOW_MIN_SIZE.split('x'))
        
        self.font_config()
        self.replace_rules = []
        self.supported_encodings = [
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
        self.simple_mode = tk.BooleanVar(value=True)
        self.compiled_rules = []
        self.create_widgets()
        self.running = False

        # 跨线程 UI 更新队列：工作线程只入队，主线程统一执行
        self._track_var(self.simple_mode, "_simple_mode")
        self._track_var(self.read_encoding, "_read_encoding")
        self._track_var(self.write_encoding, "_write_encoding")
        self._ui_queue = queue.Queue()
        self.root.after(100, self._process_ui_queue)

    def font_config(self):
        self.root.option_add("*Font", DEFAULT_FONT)

    def _track_var(self, var, attr):
        """同步 Tk 变量到普通属性，避免工作线程直接读取 Tk 变量"""
        setattr(self, attr, var.get())
        var.trace_add("write", lambda *_, v=var, a=attr: setattr(self, a, v.get()))

    def _schedule_ui(self, callback, *args):
        """把 UI 操作放入队列，由主线程执行"""
        self._ui_queue.put((callback, args))

    def _process_ui_queue(self):
        while True:
            try:
                callback, args = self._ui_queue.get_nowait()
            except queue.Empty:
                break
            try:
                callback(*args)
            except Exception:
                traceback.print_exc()
        self.root.after(100, self._process_ui_queue)

    def _append_message(self, message):
        self.message_text.config(state=tk.NORMAL)
        self.message_text.insert(tk.END, message + "\n")
        self.message_text.see(tk.END)
        self.message_text.config(state=tk.DISABLED)

    def _set_status(self, text):
        self.status_var.set(text)

    def _set_busy(self, busy):
        state = tk.DISABLED if busy else tk.NORMAL
        self.find_only_btn.config(state=state)
        self.replace_btn.config(state=state)
        self.stop_btn.config(state=tk.NORMAL if busy else tk.DISABLED)
        for btn in self.rule_buttons + self.rule_io_buttons:
            btn.config(state=state)
        self.read_encoding_combo.config(state="disabled" if busy else "readonly")
        self.write_encoding_combo.config(state="disabled" if busy else "readonly")

    def _reset_ui(self):
        self.status_var.set(STATUS_READY)
        self._set_busy(False)

    def _grid_widget(self, widget, row, col, **kwargs):
        """统一处理grid布局参数"""
        default_args = {"sticky": tk.W+tk.E, "pady": WIDGET_PADY, "padx": WIDGET_PADX}
        default_args.update(kwargs)
        widget.grid(row=row, column=col,** default_args)

    def create_widgets(self):
        """创建主界面组件"""
        main_frame = ttk.Frame(self.root, padding=MAIN_FRAME_PADDING)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        self.create_folder_frame(main_frame)
        self.create_filter_frame(main_frame)
        self.create_encoding_frame(main_frame)
        self.create_rules_frame(main_frame)
        self.create_message_frame(main_frame)
        self.create_button_frame(main_frame)
        self.create_status_bar(main_frame)

    def create_folder_frame(self, parent):
        folder_frame = ttk.LabelFrame(parent, text=LABEL_FOLDER_SELECT, padding=FRAME_PADDING)
        self._grid_widget(folder_frame, 0, 0, columnspan=2, sticky=tk.W+tk.E+tk.N+tk.S)
        
        ttk.Label(folder_frame, text=LABEL_FOLDER_PATH).grid(row=0, column=0, sticky=tk.W, pady=WIDGET_PADY)
        self.folder_path = tk.StringVar()
        folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_path)
        folder_entry.grid(row=0, column=1, sticky=tk.W+tk.E, pady=WIDGET_PADY, padx=WIDGET_PADX)
        ttk.Button(folder_frame, text=BTN_BROWSE, command=self.browse_folder).grid(
            row=0, column=2, padx=WIDGET_PADX, pady=WIDGET_PADY)
        
        self.recursive_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(folder_frame, text=LABEL_RECURSIVE, variable=self.recursive_var).grid(
            row=1, column=0, columnspan=3, sticky=tk.W, pady=WIDGET_PADY)
        folder_frame.columnconfigure(1, weight=1)

    def create_filter_frame(self, parent):
        filter_frame = ttk.LabelFrame(parent, text=LABEL_FILE_FILTER_FRAME, padding=FRAME_PADDING)
        self._grid_widget(filter_frame, 1, 0, columnspan=2, sticky=tk.W+tk.E+tk.N+tk.S)
        
        ttk.Label(filter_frame, text=LABEL_FILE_FILTER_PROMPT).grid(row=0, column=0, sticky=tk.W, pady=WIDGET_PADY)
        self.file_filter_pattern = tk.StringVar(value="*.*")
        ttk.Entry(filter_frame, textvariable=self.file_filter_pattern).grid(
            row=0, column=1, sticky=tk.W+tk.E, pady=WIDGET_PADY, padx=WIDGET_PADX)
        filter_frame.columnconfigure(1, weight=1)

    def create_encoding_frame(self, parent):
        encoding_frame = ttk.LabelFrame(parent, text=LABEL_ENCODING_SETTINGS, padding=FRAME_PADDING)
        self._grid_widget(encoding_frame, 2, 0, columnspan=2, sticky=tk.W+tk.E+tk.N+tk.S)
        
        ttk.Label(encoding_frame, text=LABEL_READ_ENCODING).grid(
            row=0, column=0, sticky=tk.W, pady=WIDGET_PADY, padx=WIDGET_PADX)
        self.read_encoding = tk.StringVar(value="自动检测")
        self.read_encoding_combo = ttk.Combobox(
            encoding_frame, textvariable=self.read_encoding,
            values=self.supported_encodings, state="readonly", width=25
        )
        self.read_encoding_combo.grid(row=0, column=1, sticky=tk.W, pady=WIDGET_PADY, padx=WIDGET_PADX)

        ttk.Label(encoding_frame, text=LABEL_WRITE_ENCODING).grid(
            row=0, column=2, sticky=tk.W, pady=WIDGET_PADY, padx=WIDGET_PADX)
        self.write_encoding = tk.StringVar(value="保持原有编码")
        self.write_encoding_combo = ttk.Combobox(
            encoding_frame, textvariable=self.write_encoding,
            values=["保持原有编码"] + self.supported_encodings[1:],
            state="readonly", width=25
        )
        self.write_encoding_combo.grid(row=0, column=3, sticky=tk.W, pady=WIDGET_PADY, padx=WIDGET_PADX)
        encoding_frame.columnconfigure(4, weight=1)

    def create_rules_frame(self, parent):
        rules_frame = ttk.LabelFrame(parent, text=LABEL_REPLACE_RULES, padding=FRAME_PADDING)
        self._grid_widget(rules_frame, 3, 0, sticky=tk.W+tk.E+tk.N+tk.S)
        
        rules_frame.columnconfigure(0, weight=1)
        rules_frame.rowconfigure(0, weight=1)
        rules_frame.update_idletasks()
        rules_frame.configure(width=500)
        rules_frame.grid_propagate(False)
        
        scroll_frame = ttk.Frame(rules_frame)
        scroll_frame.grid(row=0, column=0, sticky=tk.NSEW)
        
        v_scrollbar = ttk.Scrollbar(scroll_frame, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        h_scrollbar = ttk.Scrollbar(scroll_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.rules_tree = ttk.Treeview(
            scroll_frame, columns=("alias", "find", "replace", "regex"), 
            show="headings", height=6,
            yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set
        )
        
        v_scrollbar.config(command=self.rules_tree.yview)
        h_scrollbar.config(command=self.rules_tree.xview)
        
        self.rules_tree.heading("alias", text=ALIAS_COL_NAME)
        self.rules_tree.heading("find", text=FIND_COL_NAME)
        self.rules_tree.heading("replace", text=REPLACE_COL_NAME)
        self.rules_tree.heading("regex", text=REGEX_COL_NAME)
        
        self.rules_tree.column("alias", width=ALIAS_COL_WIDTH, stretch=tk.YES, minwidth=ALIAS_COL_MIN_WIDTH)
        self.rules_tree.column("find", width=FIND_COL_WIDTH, stretch=tk.YES, minwidth=FIND_COL_MIN_WIDTH)
        self.rules_tree.column("replace", width=REPLACE_COL_WIDTH, stretch=tk.YES, minwidth=REPLACE_COL_MIN_WIDTH)
        self.rules_tree.column("regex", width=REGEX_COL_WIDTH, stretch=tk.NO, minwidth=REGEX_COL_MIN_WIDTH)
        
        self.rules_tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        rules_btn_frame = ttk.Frame(rules_frame)
        rules_btn_frame.grid(row=1, column=0, sticky=tk.EW, pady=WIDGET_PADY)
        
        self.rule_buttons = []
        for btn_text, cmd in [(BTN_ADD_RULE, self.add_rule),
                             (BTN_EDIT_RULE, self.edit_rule), 
                             (BTN_DELETE_RULE, self.delete_rule)]:
            btn = ttk.Button(rules_btn_frame, text=btn_text, command=cmd)
            btn.pack(side=tk.LEFT, padx=WIDGET_PADX)
            self.rule_buttons.append(btn)
        
        rule_io_frame = ttk.Frame(rules_frame)
        rule_io_frame.grid(row=2, column=0, sticky=tk.EW, pady=WIDGET_PADY)
        
        self.rule_io_buttons = []
        for btn_text, cmd in [(BTN_SAVE_RULES, self.save_rules), (BTN_LOAD_RULES, self.load_rules)]:
            btn = ttk.Button(rule_io_frame, text=btn_text, command=cmd)
            btn.pack(side=tk.LEFT, padx=WIDGET_PADX)
            self.rule_io_buttons.append(btn)

    def create_message_frame(self, parent):
        message_frame = ttk.LabelFrame(parent, text=LABEL_OPERATION_MESSAGES, padding=FRAME_PADDING)
        self._grid_widget(message_frame, 3, 1, sticky=tk.W+tk.E+tk.N+tk.S)
        
        self.message_text = ScrolledText(message_frame, wrap=tk.WORD, state=tk.DISABLED, height=10)
        self.message_text.pack(fill=tk.BOTH, expand=True)
        
        message_ctrl_frame = ttk.Frame(message_frame)
        message_ctrl_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=WIDGET_PADY)
        
        ttk.Checkbutton(
            message_ctrl_frame, text=LABEL_SIMPLE_MODE, variable=self.simple_mode
        ).pack(side=tk.LEFT)
        
        ttk.Button(message_ctrl_frame, text=BTN_CLEAR_MSG, command=self.clear_messages).pack(
            side=tk.RIGHT, padx=WIDGET_PADX)

    def create_button_frame(self, parent):
        btn_frame = ttk.Frame(parent)
        self._grid_widget(btn_frame, 4, 0, columnspan=2)
        
        self.find_only_btn = ttk.Button(btn_frame, text=BTN_FIND_ONLY, command=self.start_find_only)
        self.find_only_btn.pack(side=tk.LEFT, padx=BUTTON_PADX)
        
        self.replace_btn = ttk.Button(btn_frame, text=BTN_REPLACE, command=self.start_replace)
        self.replace_btn.pack(side=tk.LEFT, padx=BUTTON_PADX)
        
        self.stop_btn = ttk.Button(btn_frame, text=BTN_STOP, command=self.stop_processing, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=BUTTON_PADX)

    def create_status_bar(self, parent):
        self.status_var = tk.StringVar(value=STATUS_READY)
        status_bar = ttk.Label(parent, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self._grid_widget(status_bar, 5, 0, columnspan=2, sticky=tk.W+tk.E, pady=0)

    def browse_folder(self):
        if folder := filedialog.askdirectory():
            self.folder_path.set(folder)

    def add_rule(self):
        result = RuleDialog(self.root, DLG_TITLE_ADD_RULE).result
        if not result:
            return
        if result["use_regex"]:
            try:
                re.compile(result["find"])
            except re.error as e:
                messagebox.showerror(PROMPT_ERROR, MSG_INVALID_REGEX.format(e))
                return
        self.replace_rules.append(result)
        self.update_rules_tree()
        self._compile_rules()

    def edit_rule(self):
        if not (selected := self.rules_tree.selection()):
            messagebox.showinfo(PROMPT_INFO, PROMPT_SELECT_RULE_EDIT)
            return
            
        index = int(self.rules_tree.item(selected[0])["tags"][0])
        if (dialog := RuleDialog(self.root, DLG_TITLE_EDIT_RULE, self.replace_rules[index])).result:
            self.replace_rules[index] = dialog.result
            self.update_rules_tree()
            self._compile_rules()

    def delete_rule(self):
        if not (selected := self.rules_tree.selection()):
            messagebox.showinfo(PROMPT_INFO, PROMPT_SELECT_RULE_DELETE)
            return
            
        if messagebox.askyesno(PROMPT_CONFIRM, PROMPT_CONFIRM_DELETE):
            index = int(self.rules_tree.item(selected[0])["tags"][0])
            del self.replace_rules[index]
            self.update_rules_tree()
            self._compile_rules()

    def update_rules_tree(self):
        for item in self.rules_tree.get_children():
            self.rules_tree.delete(item)
            
        for i, rule in enumerate(self.replace_rules):
            self.rules_tree.insert(
                "", tk.END, 
                values=(rule["alias"], rule["find"], rule["replace"], "是" if rule.get("use_regex", False) else "否"), 
                tags=(i,)
            )

    def _compile_rules(self):
        """预编译所有规则的正则表达式，提升匹配效率"""
        self.compiled_rules = []
        for rule in self.replace_rules:
            use_regex = rule.get("use_regex", False)
            try:
                pattern = re.compile(rule["find"]) if use_regex else re.compile(re.escape(rule["find"]))
            except re.error as e:
                raise re.error(f"{rule.get('alias', '')}: {e}") from e
            self.compiled_rules.append((pattern, rule["replace"], use_regex))

    def save_rules(self):
        if not self.replace_rules:
            messagebox.showinfo(PROMPT_INFO, PROMPT_NO_RULES_TO_SAVE)
            return
            
        if file_path := filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        ):
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(self.replace_rules, f, ensure_ascii=False, indent=2)
                self.add_message(MSG_RULES_SAVED.format(file_path))
            except IOError as e:
                self.add_message(MSG_SAVE_RULES_FAILED_IO.format(str(e)))
            except (TypeError, ValueError) as e:
                self.add_message(MSG_SAVE_RULES_FAILED_JSON.format(str(e)))

    def load_rules(self):
        if not (file_path := filedialog.askopenfilename(
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")])):
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (IOError, OSError, UnicodeDecodeError) as e:
            self.add_message(MSG_LOAD_RULES_FAILED_IO.format(str(e)))
            return
        except json.JSONDecodeError as e:
            self.add_message(MSG_LOAD_RULES_FAILED_JSON.format(str(e)))
            return

        if not isinstance(data, list):
            self.add_message(MSG_INVALID_RULES_FORMAT.format("规则文件必须是一个数组"))
            return

        validated_rules = []
        for index, rule in enumerate(data):
            if (not isinstance(rule, dict) or "find" not in rule or "replace" not in rule
                    or not isinstance(rule["find"], str) or not isinstance(rule["replace"], str)):
                self.add_message(MSG_INVALID_RULES_FORMAT.format(f"第 {index + 1} 条规则缺少 find/replace 字段"))
                return
            if not rule["find"]:
                self.add_message(MSG_INVALID_RULES_FORMAT.format(f"第 {index + 1} 条规则的查找内容为空"))
                return
            if rule.get("use_regex", False):
                try:
                    re.compile(rule["find"])
                except re.error as e:
                    self.add_message(MSG_INVALID_REGEX.format(e))
                    return
            validated_rules.append({
                "alias": str(rule.get("alias", f"规则{index + 1}")),
                "find": rule["find"],
                "replace": rule["replace"],
                "use_regex": bool(rule.get("use_regex", False))
            })

        self.replace_rules = validated_rules
        self.update_rules_tree()
        self._compile_rules()
        self.add_message(MSG_RULES_LOADED.format(file_path))

    def add_message(self, message, force=False):
        if self._simple_mode and not force:
            return
        self._schedule_ui(self._append_message, message)

    def clear_messages(self):
        self.message_text.config(state=tk.NORMAL)
        self.message_text.delete(1.0, tk.END)
        self.message_text.config(state=tk.DISABLED)

    def detect_encoding(self, file_path):
        for encoding in self.supported_encodings[1:]:  # 排除"自动检测"
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read(1024)
                return encoding
            except UnicodeDecodeError:
                continue
                
        return "utf-8"  # 默认编码

    def _get_read_encoding(self, file_path) -> str:
        if self._read_encoding == "自动检测":
            encoding = self.detect_encoding(file_path)
            self.add_message(MSG_ENCODING_DETECTED.format(file_path, encoding))
            return encoding
        return self._read_encoding

    def _get_write_encoding(self, original_encoding) -> str:
        return self._write_encoding if self._write_encoding != "保持原有编码" else original_encoding

    def read_file_with_encoding(self, file_path):
        try:
            encoding = self._get_read_encoding(file_path)
            with codecs.open(file_path, 'r', encoding=encoding, errors='replace') as f:
                return f.read(), encoding
        except IOError as e:
            raise Exception(f"读取文件失败（I/O错误）: {str(e)}")
        except UnicodeDecodeError as e:
            raise Exception(f"读取文件失败（编码错误）: {str(e)}")

    def write_file_with_encoding(self, file_path, content, original_encoding):
        encoding = self._get_write_encoding(original_encoding)
        # 先编码再写文件：编码失败时不会先把原文件截断
        try:
            encoded = content.encode(encoding)
        except UnicodeEncodeError as e:
            raise Exception(f"写入文件失败（编码错误）: {str(e)}")
        except LookupError as e:
            raise Exception(f"写入文件失败（未知编码）: {str(e)}")
        try:
            with open(file_path, 'wb') as f:
                f.write(encoded)
            return True
        except IOError as e:
            raise Exception(f"写入文件失败（I/O错误）: {str(e)}")

    def _enumerate_files(self, folder, pattern, recursive):
        files = []
        if recursive:
            for root_dir, _, _ in os.walk(folder):
                files.extend(glob.glob(os.path.join(root_dir, pattern)))
        else:
            files = glob.glob(os.path.join(folder, pattern))
        return files

    def _process_content(self, content: str, replace_mode: bool) -> Tuple[str, int, bool]:
        modified, total_matches, current_content = False, 0, content
        
        for pattern, replace_str, use_regex in self.compiled_rules:
            if (matches := len(pattern.findall(current_content))) > 0:
                total_matches += matches
                if replace_mode:
                    # 非正则模式下的替换内容按字面处理，避免反斜杠被当作转义序列
                    replacement = replace_str if use_regex else (lambda m: replace_str)
                    new_content = pattern.sub(replacement, current_content)
                    if new_content != current_content:
                        current_content, modified = new_content, True
        
        return current_content, total_matches, modified

    def process_file(self, file_path, replace_mode=True):
        try:
            content, original_encoding = self.read_file_with_encoding(file_path)
            new_content, matches, modified = self._process_content(content, replace_mode)
            
            if not self._simple_mode:
                if matches > 0:
                    self.add_message(MSG_FILE_MATCHES_FOUND.format(file_path, matches))
                    if replace_mode and modified:
                        self.add_message(MSG_FILE_REPLACED.format(file_path))
                else:
                    self.add_message(MSG_FILE_NO_MATCHES.format(file_path))
            
            if replace_mode and modified:
                self.write_file_with_encoding(file_path, new_content, original_encoding)
                
            return (True, matches, modified, None)
        except Exception as e:
            error_msg = MSG_FILE_PROCESS_ERROR.format(file_path, str(e))
            self.add_message(error_msg, force=True)
            return (False, 0, False, error_msg)

    def process_files(self, folder, pattern, recursive, replace_mode):
        total_files, processed, processed_successfully = 0, 0, 0
        total_matches, replaced_files, failed_files = 0, 0, []
        aborted = False

        try:
            if not folder or not os.path.isdir(folder):
                self._schedule_ui(messagebox.showerror, PROMPT_ERROR, PROMPT_INVALID_FOLDER)
                return

            if not pattern:
                self._schedule_ui(messagebox.showerror, PROMPT_ERROR, PROMPT_ENTER_FILTER)
                return

            try:
                files = self._enumerate_files(folder, pattern, recursive)
            except Exception as e:
                self._schedule_ui(messagebox.showerror, PROMPT_ERROR,
                                  MSG_FILE_PROCESS_ERROR.format(folder, str(e)))
                return

            total_files = len(files)
            self.add_message(MSG_TOTAL_FILES_FOUND.format(total_files), force=True)

            if total_files == 0:
                self._schedule_ui(messagebox.showinfo, PROMPT_INFO, PROMPT_NO_FILES_FOUND)
                return

            if self._simple_mode:
                self.add_message(MSG_START_PROCESSING, force=True)

            for file_path in files:
                if not self.running:
                    aborted = True
                    self.add_message(MSG_OPERATION_ABORTED, force=True)
                    break

                processed += 1
                self._schedule_ui(self._set_status, STATUS_PROCESSING.format(processed, total_files))

                success, matches, modified, error = self.process_file(file_path, replace_mode)
                total_matches += matches

                if success:
                    processed_successfully += 1
                    if replace_mode and modified:
                        replaced_files += 1
                else:
                    failed_files.append((file_path, error))
        finally:
            self.running = False
            self._schedule_ui(self._finish_processing, replace_mode, processed, total_files,
                              processed_successfully, replaced_files, total_matches,
                              failed_files, aborted)

    def _finish_processing(self, replace_mode, processed, total_files, processed_successfully,
                           replaced_files, total_matches, failed_files, aborted):
        if total_files == 0:
            self._reset_ui()
            return

        self.add_message(MSG_PROCESSING_SUMMARY, force=True)
        if aborted:
            self.add_message(MSG_OPERATION_TERMINATED.format(processed, total_files), force=True)
            if replace_mode:
                self.add_message(MSG_ALREADY_REPLACED_FILES.format(replaced_files), force=True)
        else:
            self.add_message(MSG_REPLACE_COMPLETE.format(processed) if replace_mode else MSG_FIND_COMPLETE.format(processed), force=True)
            if replace_mode:
                self.add_message(MSG_REPLACED_FILES.format(replaced_files), force=True)

        self.add_message(MSG_SUCCESSFUL_FILES.format(processed_successfully), force=True)
        self.add_message(MSG_TOTAL_MATCHES.format(total_matches), force=True)

        if failed_files:
            self.add_message(MSG_FAILED_FILES.format(len(failed_files)), force=True)
            if not self._simple_mode:
                for file, error in failed_files:
                    self.add_message(f"  - {file}: {error}", force=True)

        self._reset_ui()

    def stop_processing(self):
        if self.running:
            self.running = False
            self.add_message(MSG_ABORTING_OPERATION, force=True)
            self.status_var.set(STATUS_TERMINATING)

    def start_operation(self, replace_mode):
        if replace_mode and not messagebox.askyesno(PROMPT_CONFIRM, PROMPT_CONFIRM_REPLACE):
            return
        self.start_processing(replace_mode)

    def start_find_only(self):
        self.start_operation(replace_mode=False)

    def start_replace(self):
        self.start_operation(replace_mode=True)

    def start_processing(self, replace_mode):
        if not self.replace_rules:
            messagebox.showinfo(PROMPT_INFO, PROMPT_NO_RULES)
            return

        try:
            self._compile_rules()
        except re.error as e:
            messagebox.showerror(PROMPT_ERROR, MSG_INVALID_REGEX.format(e))
            return

        folder = self.folder_path.get()
        pattern = self.file_filter_pattern.get()
        recursive = self.recursive_var.get()

        self.running = True
        self._set_busy(True)
        self.status_var.set(STATUS_WORKING)
        self.add_message(MSG_START_PROCESS, force=True)

        threading.Thread(
            target=self.process_files,
            args=(folder, pattern, recursive, replace_mode),
            daemon=True
        ).start()


if __name__ == "__main__":
    root = tk.Tk()
    app = BatchTextReplacer(root)
    root.mainloop()
