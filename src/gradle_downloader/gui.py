"""
图形用户界面模块
使用 tkinter 实现现代化的 GUI
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import os
import sys
from typing import Optional, Callable
import logging

from .core import RepositoryManager
from .decompiler import JavaDecompiler
from .utils import setup_logging, validate_dependency_format, ProgressTracker
from .config import config_manager

logger = logging.getLogger(__name__)

class ModernButton(ttk.Button):
    """现代化按钮组件"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.configure(style='Modern.TButton')

class StatusBar(ttk.Frame):
    """状态栏组件"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        
        self.progress_var = tk.DoubleVar()
        
        # 状态标签
        self.status_label = ttk.Label(self, textvariable=self.status_var)
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # 进度条
        self.progress_bar = ttk.Progressbar(
            self, variable=self.progress_var, 
            length=200, mode='determinate'
        )
        self.progress_bar.pack(side=tk.RIGHT, padx=5)
    
    def set_status(self, message: str):
        """设置状态消息"""
        self.status_var.set(message)
    
    def set_progress(self, current: int, total: int):
        """设置进度"""
        if total > 0:
            progress = (current / total) * 100
            self.progress_var.set(progress)
        else:
            self.progress_var.set(0)
    
    def reset_progress(self):
        """重置进度条"""
        self.progress_var.set(0)

class DownloadTab(ttk.Frame):
    """下载标签页"""
    
    def __init__(self, parent, status_callback: Callable[[str], None] = None):
        super().__init__(parent)
        self.status_callback = status_callback
        self.repo_manager = RepositoryManager()
        self.decompiler = JavaDecompiler()
        
        self.create_widgets()
    
    def create_widgets(self):
        """创建界面组件"""
        # 依赖输入区域
        input_frame = ttk.LabelFrame(self, text="依赖信息", padding=10)
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(input_frame, text="依赖:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.dependency_var = tk.StringVar()
        self.dependency_entry = ttk.Entry(
            input_frame, textvariable=self.dependency_var, width=50
        )
        self.dependency_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(input_frame, text="格式: group:artifact:version").grid(
            row=1, column=1, sticky=tk.W, pady=2
        )
        
        # 仓库选择
        ttk.Label(input_frame, text="仓库:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.repo_var = tk.StringVar()
        repo_frame = ttk.Frame(input_frame)
        repo_frame.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=2)
        
        self.repo_combo = ttk.Combobox(repo_frame, textvariable=self.repo_var, state="readonly")
        self.repo_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(
            repo_frame, text="全部", command=self.select_all_repos
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(
            repo_frame, text="刷新", command=self.refresh_repos
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        # 初始化仓库列表
        self.refresh_repos()
        
        # 输出目录
        ttk.Label(input_frame, text="输出目录:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.output_dir_var = tk.StringVar(value="downloads")
        output_frame = ttk.Frame(input_frame)
        output_frame.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=2)
        
        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_dir_var)
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(
            output_frame, text="浏览", command=self.browse_output_dir
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        input_frame.columnconfigure(1, weight=1)
        
        # 选项区域
        options_frame = ttk.LabelFrame(self, text="选项", padding=10)
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.sources_only_var = tk.BooleanVar()
        ttk.Checkbutton(
            options_frame, text="仅下载源码（不反编译）", 
            variable=self.sources_only_var
        ).pack(anchor=tk.W)
        
        self.force_decompile_var = tk.BooleanVar()
        ttk.Checkbutton(
            options_frame, text="强制反编译（即使有源码）", 
            variable=self.force_decompile_var
        ).pack(anchor=tk.W)
        
        # 按钮区域
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.download_button = ModernButton(
            button_frame, text="下载", command=self.start_download
        )
        self.download_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, text="搜索", command=self.open_search_dialog
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, text="清除", command=self.clear_fields
        ).pack(side=tk.LEFT, padx=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(self, text="日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=10, state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def browse_output_dir(self):
        """浏览输出目录"""
        directory = filedialog.askdirectory(
            title="选择输出目录",
            initialdir=self.output_dir_var.get()
        )
        if directory:
            self.output_dir_var.set(directory)
    
    def clear_fields(self):
        """清除输入字段"""
        self.dependency_var.set("")
        self.output_dir_var.set("downloads")
        self.sources_only_var.set(False)
        self.force_decompile_var.set(False)
        
        # 重置仓库选择
        if hasattr(self, 'repo_var'):
            self.repo_var.set("全部仓库")
        
        # 清除日志
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def log_message(self, message: str, level: str = "INFO"):
        """添加日志消息"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{level}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def start_download(self):
        """开始下载（在新线程中执行）"""
        dependency = self.dependency_var.get().strip()
        
        if not dependency:
            messagebox.showerror("错误", "请输入依赖信息")
            return
        
        if not validate_dependency_format(dependency):
            messagebox.showerror("错误", "无效的依赖格式\n支持格式: group:artifact:version")
            return
        
        # 禁用下载按钮
        self.download_button.config(state=tk.DISABLED)
        
        # 在新线程中执行下载
        thread = threading.Thread(target=self.download_worker)
        thread.daemon = True
        thread.start()
    
    def download_worker(self):
        """下载工作线程"""
        try:
            dependency = self.dependency_var.get().strip()
            output_dir = self.output_dir_var.get().strip()
            sources_only = self.sources_only_var.get()
            force_decompile = self.force_decompile_var.get()
            
            # 根据选择的仓库创建仓库管理器
            selected_repo = getattr(self, 'repo_var', None)
            if selected_repo and selected_repo.get() and selected_repo.get() != "全部仓库":
                repo_manager = RepositoryManager(repository_names=[selected_repo.get()])
                self.log_message(f"使用仓库: {selected_repo.get()}")
            else:
                repo_manager = RepositoryManager()
                self.log_message("使用全部仓库")
            
            self.log_message(f"开始下载: {dependency}")
            
            if self.status_callback:
                self.status_callback("正在下载...")
            
            # 尝试下载源码
            if not force_decompile:
                sources_path = repo_manager.download_sources(
                    dependency, output_dir, self.progress_callback
                )
                
                if sources_path:
                    self.log_message(f"源码下载成功: {sources_path}", "SUCCESS")
                    messagebox.showinfo("成功", f"源码下载成功!\n{sources_path}")
                    return
            
            if sources_only:
                self.log_message("未找到源码 JAR，跳过反编译", "WARNING")
                messagebox.showwarning("警告", "未找到源码 JAR")
                return
            
            # 下载二进制包
            self.log_message("正在下载二进制包...")
            binary_path = repo_manager.download_binary(
                dependency, output_dir, self.progress_callback
            )
            
            if not binary_path:
                self.log_message("未找到二进制 JAR", "ERROR")
                messagebox.showerror("错误", "未找到二进制 JAR")
                return
            
            # 检查 Java 环境
            if not self.decompiler.check_java_available():
                self.log_message("需要安装 Java 才能使用反编译功能", "ERROR")
                messagebox.showerror("错误", "需要安装 Java 才能使用反编译功能")
                return
            
            # 反编译
            self.log_message("正在反编译...")
            sources_path = self.decompiler.decompile_and_package(
                binary_path, output_dir, self.decompile_progress_callback
            )
            
            if sources_path:
                self.log_message(f"反编译完成: {sources_path}", "SUCCESS")
                messagebox.showinfo("成功", f"反编译完成!\n{sources_path}")
            else:
                self.log_message("反编译失败", "ERROR")
                messagebox.showerror("错误", "反编译失败")
        
        except Exception as e:
            self.log_message(f"下载失败: {e}", "ERROR")
            messagebox.showerror("错误", f"下载失败: {e}")
        
        finally:
            # 重新启用下载按钮
            self.download_button.config(state=tk.NORMAL)
            if self.status_callback:
                self.status_callback("就绪")
    
    def progress_callback(self, current: int, total: int):
        """下载进度回调"""
        # 这里可以更新 GUI 的进度条
        pass
    
    def decompile_progress_callback(self, current: int, total: int, message: str):
        """反编译进度回调"""
        if message:
            self.log_message(f"反编译进度: {message}")
    
    def open_search_dialog(self):
        """打开搜索对话框"""
        SearchDialog(self, self.on_search_result)
    
    def on_search_result(self, dependency: str):
        """搜索结果回调"""
        self.dependency_var.set(dependency)
    
    def refresh_repos(self):
        """刷新仓库列表"""
        try:
            repositories = config_manager.list_repositories()
            repo_names = list(repositories.keys())
            repo_names.insert(0, "全部仓库")
            
            self.repo_combo['values'] = repo_names
            if not self.repo_var.get() or self.repo_var.get() not in repo_names:
                self.repo_var.set("全部仓库")
        except Exception as e:
            self.log_message(f"刷新仓库列表失败: {e}", "ERROR")
    
    def select_all_repos(self):
        """选择全部仓库"""
        self.repo_var.set("全部仓库")

class SearchDialog:
    """搜索对话框"""
    
    def __init__(self, parent, callback: Callable[[str], None]):
        self.parent = parent
        self.callback = callback
        self.repo_manager = RepositoryManager()
        
        self.create_dialog()
    
    def create_dialog(self):
        """创建对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("搜索 Maven 构件")
        self.dialog.geometry("600x400")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # 搜索输入
        search_frame = ttk.Frame(self.dialog)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.search_button = ttk.Button(
            search_frame, text="搜索", command=self.search
        )
        self.search_button.pack(side=tk.RIGHT)
        
        # 结果列表
        self.tree = ttk.Treeview(
            self.dialog, columns=('group', 'artifact', 'version', 'description'),
            show='headings'
        )
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 列标题
        self.tree.heading('group', text='Group')
        self.tree.heading('artifact', text='Artifact')
        self.tree.heading('version', text='Version')
        self.tree.heading('description', text='Description')
        
        # 列宽
        self.tree.column('group', width=150)
        self.tree.column('artifact', width=150)
        self.tree.column('version', width=100)
        self.tree.column('description', width=200)
        
        # 按钮
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(
            button_frame, text="选择", command=self.select_item
        ).pack(side=tk.LEFT)
        
        ttk.Button(
            button_frame, text="取消", command=self.dialog.destroy
        ).pack(side=tk.RIGHT)
        
        # 绑定双击事件
        self.tree.bind('<Double-1>', lambda e: self.select_item())
        
        # 绑定回车键
        self.search_entry.bind('<Return>', lambda e: self.search())
        self.search_entry.focus()
    
    def search(self):
        """执行搜索"""
        query = self.search_var.get().strip()
        if not query:
            return
        
        # 清除现有结果
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 禁用搜索按钮
        self.search_button.config(state=tk.DISABLED, text="搜索中...")
        
        # 在新线程中搜索
        thread = threading.Thread(target=self.search_worker, args=(query,))
        thread.daemon = True
        thread.start()
    
    def search_worker(self, query: str):
        """搜索工作线程"""
        try:
            results = self.repo_manager.search_artifact(query, 20)
            
            # 在主线程中更新 GUI
            self.dialog.after(0, self.update_results, results)
        
        except Exception as e:
            self.dialog.after(0, self.search_error, str(e))
    
    def update_results(self, results):
        """更新搜索结果"""
        for result in results:
            self.tree.insert('', tk.END, values=(
                result.get('group', ''),
                result.get('artifact', ''),
                result.get('version', ''),
                result.get('description', '')[:50] + '...' if len(result.get('description', '')) > 50 else result.get('description', '')
            ))
        
        # 重新启用搜索按钮
        self.search_button.config(state=tk.NORMAL, text="搜索")
    
    def search_error(self, error: str):
        """搜索错误处理"""
        messagebox.showerror("搜索错误", f"搜索失败: {error}")
        self.search_button.config(state=tk.NORMAL, text="搜索")
    
    def select_item(self):
        """选择项目"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        values = item['values']
        
        if len(values) >= 3:
            dependency = f"{values[0]}:{values[1]}:{values[2]}"
            self.callback(dependency)
            self.dialog.destroy()

class DecompileTab(ttk.Frame):
    """反编译标签页"""
    
    def __init__(self, parent, status_callback: Callable[[str], None] = None):
        super().__init__(parent)
        self.status_callback = status_callback
        self.decompiler = JavaDecompiler()
        
        self.create_widgets()
    
    def create_widgets(self):
        """创建界面组件"""
        # 文件选择区域
        file_frame = ttk.LabelFrame(self, text="JAR 文件", padding=10)
        file_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.jar_path_var = tk.StringVar()
        jar_entry_frame = ttk.Frame(file_frame)
        jar_entry_frame.pack(fill=tk.X)
        
        self.jar_entry = ttk.Entry(jar_entry_frame, textvariable=self.jar_path_var)
        self.jar_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(
            jar_entry_frame, text="浏览", command=self.browse_jar_file
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        # 输出目录
        ttk.Label(file_frame, text="输出目录:").pack(anchor=tk.W, pady=(10, 2))
        self.output_dir_var = tk.StringVar(value="decompiled")
        output_entry_frame = ttk.Frame(file_frame)
        output_entry_frame.pack(fill=tk.X)
        
        self.output_entry = ttk.Entry(output_entry_frame, textvariable=self.output_dir_var)
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(
            output_entry_frame, text="浏览", command=self.browse_output_dir
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        # 按钮区域
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.decompile_button = ModernButton(
            button_frame, text="反编译", command=self.start_decompile
        )
        self.decompile_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, text="清除", command=self.clear_fields
        ).pack(side=tk.LEFT, padx=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(self, text="日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=10, state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def browse_jar_file(self):
        """浏览 JAR 文件"""
        filename = filedialog.askopenfilename(
            title="选择 JAR 文件",
            filetypes=[("JAR files", "*.jar"), ("All files", "*.*")]
        )
        if filename:
            self.jar_path_var.set(filename)
    
    def browse_output_dir(self):
        """浏览输出目录"""
        directory = filedialog.askdirectory(
            title="选择输出目录",
            initialdir=self.output_dir_var.get()
        )
        if directory:
            self.output_dir_var.set(directory)
    
    def clear_fields(self):
        """清除输入字段"""
        self.jar_path_var.set("")
        self.output_dir_var.set("decompiled")
        
        # 清除日志
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def log_message(self, message: str, level: str = "INFO"):
        """添加日志消息"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{level}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def start_decompile(self):
        """开始反编译"""
        jar_path = self.jar_path_var.get().strip()
        
        if not jar_path:
            messagebox.showerror("错误", "请选择 JAR 文件")
            return
        
        if not os.path.exists(jar_path):
            messagebox.showerror("错误", "JAR 文件不存在")
            return
        
        # 禁用反编译按钮
        self.decompile_button.config(state=tk.DISABLED)
        
        # 在新线程中执行反编译
        thread = threading.Thread(target=self.decompile_worker)
        thread.daemon = True
        thread.start()
    
    def decompile_worker(self):
        """反编译工作线程"""
        try:
            jar_path = self.jar_path_var.get().strip()
            output_dir = self.output_dir_var.get().strip()
            
            self.log_message(f"开始反编译: {jar_path}")
            
            if self.status_callback:
                self.status_callback("正在反编译...")
            
            # 检查 Java 环境
            if not self.decompiler.check_java_available():
                self.log_message("需要安装 Java 才能使用反编译功能", "ERROR")
                messagebox.showerror("错误", "需要安装 Java 才能使用反编译功能")
                return
            
            # 反编译
            success = self.decompiler.extract_sources_to_directory(
                jar_path, output_dir, self.progress_callback
            )
            
            if success:
                self.log_message(f"反编译完成: {output_dir}", "SUCCESS")
                messagebox.showinfo("成功", f"反编译完成!\n输出目录: {output_dir}")
            else:
                self.log_message("反编译失败", "ERROR")
                messagebox.showerror("错误", "反编译失败")
        
        except Exception as e:
            self.log_message(f"反编译失败: {e}", "ERROR")
            messagebox.showerror("错误", f"反编译失败: {e}")
        
        finally:
            # 重新启用反编译按钮
            self.decompile_button.config(state=tk.NORMAL)
            if self.status_callback:
                self.status_callback("就绪")
    
    def progress_callback(self, current: int, total: int, message: str):
        """进度回调"""
        if message:
            self.log_message(f"进度: {message}")

class MainWindow:
    """主窗口"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Gradle File Downloader")
        self.root.geometry("800x600")
        
        # 初始化核心组件
        self.repo_manager = RepositoryManager()
        self.decompiler = JavaDecompiler()
        
        self.create_widgets()
        setup_logging("INFO")
    
    def create_widgets(self):
        """创建界面组件"""
        # 创建标签页
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 下载标签页
        self.download_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.download_frame, text="下载源码")
        self.create_download_tab()
        
        # 反编译标签页
        self.decompile_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.decompile_frame, text="反编译 JAR")
        self.create_decompile_tab()
        
        # 仓库管理标签页
        self.repo_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.repo_frame, text="仓库管理")
        self.create_repo_tab()
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT)
    
    def create_download_tab(self):
        """创建下载标签页"""
        frame = self.download_frame
        
        # 依赖输入区域
        input_frame = ttk.LabelFrame(frame, text="依赖信息", padding=10)
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(input_frame, text="依赖:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.dependency_var = tk.StringVar()
        self.dependency_entry = ttk.Entry(
            input_frame, textvariable=self.dependency_var, width=50
        )
        self.dependency_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        
        ttk.Label(input_frame, text="格式: group:artifact:version").grid(
            row=1, column=1, sticky=tk.W, pady=2
        )
        
        # 仓库选择
        ttk.Label(input_frame, text="仓库:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.repo_var = tk.StringVar()
        repo_frame = ttk.Frame(input_frame)
        repo_frame.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=2)
        
        self.repo_combo = ttk.Combobox(repo_frame, textvariable=self.repo_var, state="readonly")
        self.repo_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(
            repo_frame, text="全部", command=self.select_all_repos
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(
            repo_frame, text="刷新", command=self.refresh_repos
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        # 初始化仓库列表
        self.refresh_repos()
        
        # 输出目录
        ttk.Label(input_frame, text="输出目录:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.output_dir_var = tk.StringVar(value="downloads")
        output_frame = ttk.Frame(input_frame)
        output_frame.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=2)
        
        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_dir_var)
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(
            output_frame, text="浏览", command=self.browse_output_dir
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        input_frame.columnconfigure(1, weight=1)
        
        # 选项区域
        options_frame = ttk.LabelFrame(frame, text="选项", padding=10)
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.sources_only_var = tk.BooleanVar()
        ttk.Checkbutton(
            options_frame, text="仅下载源码（不反编译）", 
            variable=self.sources_only_var
        ).pack(anchor=tk.W)
        
        # 按钮区域
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.download_button = ModernButton(
            button_frame, text="下载", command=self.start_download
        )
        self.download_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, text="清除", command=self.clear_download_fields
        ).pack(side=tk.LEFT, padx=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(frame, text="日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.download_log_text = scrolledtext.ScrolledText(
            log_frame, height=10, state=tk.DISABLED
        )
        self.download_log_text.pack(fill=tk.BOTH, expand=True)
    
    def create_decompile_tab(self):
        """创建反编译标签页"""
        frame = self.decompile_frame
        
        # 文件选择区域
        file_frame = ttk.LabelFrame(frame, text="JAR 文件", padding=10)
        file_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(file_frame, text="JAR 文件:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.jar_path_var = tk.StringVar()
        jar_entry_frame = ttk.Frame(file_frame)
        jar_entry_frame.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        
        self.jar_entry = ttk.Entry(jar_entry_frame, textvariable=self.jar_path_var)
        self.jar_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(
            jar_entry_frame, text="浏览", command=self.browse_jar_file
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        # 输出目录
        ttk.Label(file_frame, text="输出目录:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.decompile_output_var = tk.StringVar(value="decompiled")
        decompile_output_frame = ttk.Frame(file_frame)
        decompile_output_frame.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=2)
        
        self.decompile_output_entry = ttk.Entry(decompile_output_frame, textvariable=self.decompile_output_var)
        self.decompile_output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(
            decompile_output_frame, text="浏览", command=self.browse_decompile_output_dir
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        file_frame.columnconfigure(1, weight=1)
        
        # 按钮区域
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.decompile_button = ModernButton(
            button_frame, text="反编译", command=self.start_decompile
        )
        self.decompile_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame, text="清除", command=self.clear_decompile_fields
        ).pack(side=tk.LEFT, padx=5)
        
        # 日志区域
        log_frame = ttk.LabelFrame(frame, text="日志", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.decompile_log_text = scrolledtext.ScrolledText(
            log_frame, height=10, state=tk.DISABLED
        )
        self.decompile_log_text.pack(fill=tk.BOTH, expand=True)
    
    def create_repo_tab(self):
        """创建仓库管理标签页"""
        frame = self.repo_frame
        
        # 仓库列表区域
        list_frame = ttk.LabelFrame(frame, text="已配置的仓库", padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建TreeView来显示仓库列表
        columns = ("name", "url")
        self.repo_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)
        
        # 设置列标题和宽度
        self.repo_tree.heading("name", text="仓库名称")
        self.repo_tree.heading("url", text="仓库URL")
        self.repo_tree.column("name", width=200)
        self.repo_tree.column("url", width=400)
        
        # 滚动条
        repo_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.repo_tree.yview)
        self.repo_tree.configure(yscrollcommand=repo_scrollbar.set)
        
        self.repo_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        repo_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 操作区域
        action_frame = ttk.LabelFrame(frame, text="仓库操作", padding=10)
        action_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 添加仓库区域
        add_frame = ttk.Frame(action_frame)
        add_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(add_frame, text="仓库名称:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.new_repo_name_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.new_repo_name_var, width=20).grid(row=0, column=1, padx=5)
        
        ttk.Label(add_frame, text="仓库URL:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.new_repo_url_var = tk.StringVar()
        ttk.Entry(add_frame, textvariable=self.new_repo_url_var, width=40).grid(row=0, column=3, padx=5)
        
        ttk.Button(add_frame, text="添加仓库", command=self.add_repository).grid(row=0, column=4, padx=5)
        
        # 管理按钮区域
        button_frame = ttk.Frame(action_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="删除选中仓库", command=self.remove_selected_repository).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="重置为默认仓库", command=self.reset_repositories).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="刷新列表", command=self.refresh_repository_list).pack(side=tk.LEFT, padx=5)
        
        # 初始化仓库列表
        self.refresh_repository_list()
    
    def refresh_repos(self):
        """刷新下载标签页的仓库下拉列表"""
        try:
            repositories = config_manager.list_repositories()
            repo_names = list(repositories.keys())
            repo_names.insert(0, "全部仓库")
            
            self.repo_combo['values'] = repo_names
            if not self.repo_var.get() or self.repo_var.get() not in repo_names:
                self.repo_var.set("全部仓库")
        except Exception as e:
            self.log_download_message(f"刷新仓库列表失败: {e}", "ERROR")
    
    def select_all_repos(self):
        """选择全部仓库"""
        self.repo_var.set("全部仓库")
    
    def refresh_repository_list(self):
        """刷新仓库管理标签页的仓库列表"""
        # 清空现有列表
        for item in self.repo_tree.get_children():
            self.repo_tree.delete(item)
        
        # 获取仓库列表并填充
        try:
            repositories = config_manager.list_repositories()
            for name, url in repositories.items():
                self.repo_tree.insert("", tk.END, values=(name, url))
        except Exception as e:
            messagebox.showerror("错误", f"获取仓库列表失败: {e}")
    
    def add_repository(self):
        """添加新仓库"""
        name = self.new_repo_name_var.get().strip()
        url = self.new_repo_url_var.get().strip()
        
        if not name:
            messagebox.showerror("错误", "请输入仓库名称")
            return
        
        if not url:
            messagebox.showerror("错误", "请输入仓库URL")
            return
        
        # 检查URL格式
        if not (url.startswith("http://") or url.startswith("https://")):
            messagebox.showerror("错误", "仓库URL必须以http://或https://开头")
            return
        
        try:
            if config_manager.add_repository(name, url):
                messagebox.showinfo("成功", f"成功添加仓库: {name}")
                self.new_repo_name_var.set("")
                self.new_repo_url_var.set("")
                self.refresh_repository_list()
                self.refresh_repos()  # 同时刷新下载标签页的仓库列表
            else:
                messagebox.showerror("错误", f"添加仓库失败: {name}")
        except Exception as e:
            messagebox.showerror("错误", f"添加仓库时发生错误: {e}")
    
    def remove_selected_repository(self):
        """删除选中的仓库"""
        selection = self.repo_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请先选择要删除的仓库")
            return
        
        item = self.repo_tree.item(selection[0])
        repo_name = item['values'][0]
        
        if messagebox.askyesno("确认删除", f"确定要删除仓库 '{repo_name}' 吗？"):
            try:
                if config_manager.remove_repository(repo_name):
                    messagebox.showinfo("成功", f"成功删除仓库: {repo_name}")
                    self.refresh_repository_list()
                    self.refresh_repos()  # 同时刷新下载标签页的仓库列表
                else:
                    messagebox.showerror("错误", f"删除仓库失败: {repo_name}")
            except Exception as e:
                messagebox.showerror("错误", f"删除仓库时发生错误: {e}")
    
    def reset_repositories(self):
        """重置为默认仓库"""
        if messagebox.askyesno("确认重置", "确定要重置所有仓库配置为默认值吗？\n这将删除所有自定义仓库！"):
            try:
                if config_manager.reset_to_defaults():
                    messagebox.showinfo("成功", "成功重置仓库配置")
                    self.refresh_repository_list()
                    self.refresh_repos()  # 同时刷新下载标签页的仓库列表
                else:
                    messagebox.showerror("错误", "重置仓库配置失败")
            except Exception as e:
                messagebox.showerror("错误", f"重置仓库配置时发生错误: {e}")
    
    def browse_output_dir(self):
        """浏览输出目录"""
        directory = filedialog.askdirectory(
            title="选择输出目录",
            initialdir=self.output_dir_var.get()
        )
        if directory:
            self.output_dir_var.set(directory)
    
    def browse_jar_file(self):
        """浏览 JAR 文件"""
        filename = filedialog.askopenfilename(
            title="选择 JAR 文件",
            filetypes=[("JAR files", "*.jar"), ("All files", "*.*")]
        )
        if filename:
            self.jar_path_var.set(filename)
    
    def browse_decompile_output_dir(self):
        """浏览反编译输出目录"""
        directory = filedialog.askdirectory(
            title="选择输出目录",
            initialdir=self.decompile_output_var.get()
        )
        if directory:
            self.decompile_output_var.set(directory)
    
    def clear_download_fields(self):
        """清除下载字段"""
        self.dependency_var.set("")
        self.output_dir_var.set("downloads")
        self.sources_only_var.set(False)
        
        # 重置仓库选择
        if hasattr(self, 'repo_var'):
            self.repo_var.set("全部仓库")
        
        # 清除日志
        self.download_log_text.config(state=tk.NORMAL)
        self.download_log_text.delete(1.0, tk.END)
        self.download_log_text.config(state=tk.DISABLED)
    
    def clear_decompile_fields(self):
        """清除反编译字段"""
        self.jar_path_var.set("")
        self.decompile_output_var.set("decompiled")
        
        # 清除日志
        self.decompile_log_text.config(state=tk.NORMAL)
        self.decompile_log_text.delete(1.0, tk.END)
        self.decompile_log_text.config(state=tk.DISABLED)
    
    def log_download_message(self, message: str, level: str = "INFO"):
        """添加下载日志消息"""
        self.download_log_text.config(state=tk.NORMAL)
        self.download_log_text.insert(tk.END, f"[{level}] {message}\n")
        self.download_log_text.see(tk.END)
        self.download_log_text.config(state=tk.DISABLED)
    
    def log_decompile_message(self, message: str, level: str = "INFO"):
        """添加反编译日志消息"""
        self.decompile_log_text.config(state=tk.NORMAL)
        self.decompile_log_text.insert(tk.END, f"[{level}] {message}\n")
        self.decompile_log_text.see(tk.END)
        self.decompile_log_text.config(state=tk.DISABLED)
    
    def start_download(self):
        """开始下载"""
        dependency = self.dependency_var.get().strip()
        
        if not dependency:
            messagebox.showerror("错误", "请输入依赖信息")
            return
        
        if not validate_dependency_format(dependency):
            messagebox.showerror("错误", "无效的依赖格式\n支持格式: group:artifact:version")
            return
        
        # 禁用下载按钮
        self.download_button.config(state=tk.DISABLED)
        
        # 在新线程中执行下载
        thread = threading.Thread(target=self.download_worker)
        thread.daemon = True
        thread.start()
    
    def download_worker(self):
        """下载工作线程"""
        try:
            dependency = self.dependency_var.get().strip()
            output_dir = self.output_dir_var.get().strip()
            sources_only = self.sources_only_var.get()
            
            # 根据选择的仓库创建仓库管理器
            selected_repo = getattr(self, 'repo_var', None)
            if selected_repo and selected_repo.get() and selected_repo.get() != "全部仓库":
                repo_manager = RepositoryManager(repository_names=[selected_repo.get()])
                self.log_download_message(f"使用仓库: {selected_repo.get()}")
            else:
                repo_manager = RepositoryManager()
                self.log_download_message("使用全部仓库")
            
            self.log_download_message(f"开始下载: {dependency}")
            self.status_var.set("正在下载...")
            
            # 尝试下载源码
            sources_path = repo_manager.download_sources(dependency, output_dir)
            
            if sources_path:
                self.log_download_message(f"源码下载成功: {sources_path}", "SUCCESS")
                messagebox.showinfo("成功", f"源码下载成功!\n{sources_path}")
                return
            
            if sources_only:
                self.log_download_message("未找到源码 JAR，跳过反编译", "WARNING")
                messagebox.showwarning("警告", "未找到源码 JAR")
                return
            
            # 下载二进制包
            self.log_download_message("正在下载二进制包...")
            binary_path = repo_manager.download_binary(dependency, output_dir)
            
            if not binary_path:
                self.log_download_message("未找到二进制 JAR", "ERROR")
                messagebox.showerror("错误", "未找到二进制 JAR")
                return
            
            # 检查 Java 环境
            if not self.decompiler.check_java_available():
                self.log_download_message("需要安装 Java 才能使用反编译功能", "ERROR")
                messagebox.showerror("错误", "需要安装 Java 才能使用反编译功能")
                return
            
            # 反编译
            self.log_download_message("正在反编译...")
            sources_path = self.decompiler.decompile_and_package(binary_path, output_dir)
            
            if sources_path:
                self.log_download_message(f"反编译完成: {sources_path}", "SUCCESS")
                messagebox.showinfo("成功", f"反编译完成!\n{sources_path}")
            else:
                self.log_download_message("反编译失败", "ERROR")
                messagebox.showerror("错误", "反编译失败")
        
        except Exception as e:
            self.log_download_message(f"下载失败: {e}", "ERROR")
            messagebox.showerror("错误", f"下载失败: {e}")
        
        finally:
            # 重新启用下载按钮
            self.download_button.config(state=tk.NORMAL)
            self.status_var.set("就绪")
    
    def start_decompile(self):
        """开始反编译"""
        jar_path = self.jar_path_var.get().strip()
        
        if not jar_path:
            messagebox.showerror("错误", "请选择 JAR 文件")
            return
        
        if not os.path.exists(jar_path):
            messagebox.showerror("错误", "JAR 文件不存在")
            return
        
        # 禁用反编译按钮
        self.decompile_button.config(state=tk.DISABLED)
        
        # 在新线程中执行反编译
        thread = threading.Thread(target=self.decompile_worker)
        thread.daemon = True
        thread.start()
    
    def decompile_worker(self):
        """反编译工作线程"""
        try:
            jar_path = self.jar_path_var.get().strip()
            output_dir = self.decompile_output_var.get().strip()
            
            self.log_decompile_message(f"开始反编译: {jar_path}")
            self.status_var.set("正在反编译...")
            
            # 检查 Java 环境
            if not self.decompiler.check_java_available():
                self.log_decompile_message("需要安装 Java 才能使用反编译功能", "ERROR")
                messagebox.showerror("错误", "需要安装 Java 才能使用反编译功能")
                return
            
            # 反编译
            success = self.decompiler.extract_sources_to_directory(jar_path, output_dir)
            
            if success:
                self.log_decompile_message(f"反编译完成: {output_dir}", "SUCCESS")
                messagebox.showinfo("成功", f"反编译完成!\n输出目录: {output_dir}")
            else:
                self.log_decompile_message("反编译失败", "ERROR")
                messagebox.showerror("错误", "反编译失败")
        
        except Exception as e:
            self.log_decompile_message(f"反编译失败: {e}", "ERROR")
            messagebox.showerror("错误", f"反编译失败: {e}")
        
        finally:
            # 重新启用反编译按钮
            self.decompile_button.config(state=tk.NORMAL)
            self.status_var.set("就绪")
    
    def run(self):
        """运行应用程序"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            pass

def launch_gui():
    """启动图形界面"""
    app = MainWindow()
    app.run()

if __name__ == "__main__":
    launch_gui() 