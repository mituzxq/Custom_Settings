import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
import time
import os
from ..utils.config import (
    LIGHT_THEME as THEME,
    save_config
)
import copy

class ConfigWindow:
    def __init__(self, root, config):
        self.root = root
        self.config = config
        self.window = None
        self.app_entries = []  # 存储UI组件的临时数据
        self.setup_window()

    def setup_window(self):
        try:
            self.window = tk.Toplevel(self.root)
            self.window.title("配置")
            self.window.configure(bg=THEME['BG'])
            self.window.geometry("700x600")
            self.window.resizable(False, False)

            # 创建主容器，添加内边距
            main_container = tk.Frame(self.window, bg=THEME['BG'])
            main_container.pack(expand=True, fill="both", padx=30, pady=25)

            # 创建标签页控件
            style = ttk.Style()
            
            # 配置标签页整体样式
            style.configure(
                "Custom.TNotebook",
                background=THEME['BG']
            )
            
            # 配置签样式
            style.configure(
                "Custom.TNotebook.Tab",
                background=THEME['BUTTON_BG'],
                foreground=THEME['BUTTON_FG'],
                padding=[25, 12],
                font=('Microsoft YaHei UI', 11)
            )
            
            # 配置选中标签样式
            style.map(
                "Custom.TNotebook.Tab",
                background=[("selected", THEME['BUTTON_ACTIVE_BG'])],
                foreground=[("selected", THEME['BUTTON_FG'])]
            )

            notebook = ttk.Notebook(main_container, style="Custom.TNotebook")
            notebook.pack(expand=True, fill="both")

            # 创建全局设置页
            global_frame = self.create_global_frame(notebook)
            notebook.add(global_frame, text="  全局设置  ", padding=(0, 10, 0, 0))

            # 创建按键替换设置页
            key_frame = self.create_key_frame(notebook)
            notebook.add(key_frame, text="  按键替换  ", padding=(0, 10, 0, 0))

            # 创建应用监听设置页
            monitor_frame = self.create_monitor_frame(notebook)
            notebook.add(monitor_frame, text="  应用监听  ", padding=(0, 10, 0, 0))

            # 增加标签页之间的间距
            notebook.pack(expand=True, fill="both", pady=10)

            # 设置所有子窗口的背景色
            for child in self.window.winfo_children():
                if isinstance(child, tk.Frame):
                    child.configure(bg=THEME['BG'])
                    for subchild in child.winfo_children():
                        if isinstance(subchild, tk.Frame):
                            subchild.configure(bg=THEME['BG'])

        except Exception as e:
            logging.error(f"创建配置窗口失败: {str(e)}")

    def create_global_frame(self, parent):
        """创建全局设置页"""
        # 创建主框架
        frame = tk.Frame(parent, bg=THEME['BG'])
        frame.pack(fill="both", expand=True, padx=35, pady=30)

        # OCR设置区域
        ocr_section = tk.Frame(frame, bg=THEME['BG'])
        ocr_section.pack(fill="x", pady=(0, 45))  # 增加底部间距

        self.create_section_label(ocr_section, "OCR 设置")
        
        ocr_info = tk.Label(
            ocr_section,
            text="设置 Tesseract-OCR 程序路径，用于图片文字识别功能",
            bg=THEME['BG'],
            fg="#666666",
            font=('Microsoft YaHei UI', 9),
            justify="left"
        )
        ocr_info.pack(anchor="w", pady=(5, 15))

        path_frame = tk.Frame(ocr_section, bg=THEME['BG'])
        path_frame.pack(fill="x", pady=(0, 0))

        path_label = tk.Label(
            path_frame,
            text="ocr程序路径：",
            bg=THEME['BG'],
            fg=THEME['BUTTON_FG'],
            font=('Microsoft YaHei UI', 10)
        )
        path_label.pack(side="left", padx=(0, 10))

        self.path_entry = tk.Entry(
            path_frame,
            bg=THEME['BUTTON_BG'],
            fg=THEME['BUTTON_FG'],
            insertbackground=THEME['BUTTON_FG'],
            font=('Microsoft YaHei UI', 10),
            relief="flat",
            bd=1
        )
        self.path_entry.pack(side="left", expand=True, fill="x", padx=(0, 10))
        
        current_path = self.config.get_tesseract_path()
        if current_path:
            self.path_entry.insert(0, current_path)

        browse_button = self.create_button(
            path_frame,
            "浏览",
            self.browse_tesseract
        )
        browse_button.pack(side="right")

        # 日志设置区域
        log_section = tk.Frame(frame, bg=THEME['BG'])
        log_section.pack(fill="x", pady=(0, 35))

        self.create_section_label(log_section, "日志设置")
        
        log_info = tk.Label(
            log_section,
            text="设置日志文件的保存天数，超过指定天数的日志将被自动删除",
            bg=THEME['BG'],
            fg="#666666",
            font=('Microsoft YaHei UI', 9),
            justify="left"
        )
        log_info.pack(anchor="w", pady=(5, 15))

        setting_frame = tk.Frame(log_section, bg=THEME['BG'])
        setting_frame.pack(fill="x")

        log_label = tk.Label(
            setting_frame,
            text="保存天数：",
            bg=THEME['BG'],
            fg=THEME['BUTTON_FG'],
            font=('Microsoft YaHei UI', 10)
        )
        log_label.pack(side="left", padx=(0, 5))

        # 获取当前设置的保存天数
        current_days = self.config.get_log_retention_days()
        self.log_days_var = tk.StringVar(value=str(current_days))
        
        self.log_days_entry = tk.Entry(
            setting_frame,
            textvariable=self.log_days_var,
            bg=THEME['BUTTON_BG'],
            fg=THEME['BUTTON_FG'],
            insertbackground=THEME['BUTTON_FG'],
            font=('Microsoft YaHei UI', 10),
            width=5,
            relief="flat",  # 移除边框
            bd=0  # 移除边框
        )
        self.log_days_entry.pack(side="left", padx=(0, 5))

        if current_days:
            self.log_days_entry.insert(0, current_days)

        tk.Label(
            setting_frame,
            text="天",
            bg=THEME['BG'],
            fg=THEME['BUTTON_FG'],
            font=('Microsoft YaHei UI', 10)
        ).pack(side="left")

        # 显示当前日志文件数
        log_dir = os.path.join(os.path.expanduser('~'), '.custom_settings_byMY', 'logs')
        log_count = len([f for f in os.listdir(log_dir) if f.endswith('.log')]) if os.path.exists(log_dir) else 0
        
        log_count_label = tk.Label(
            setting_frame,
            text=f"（当前共有 {log_count} 个日志文件）",
            bg=THEME['BG'],
            fg="#666666",
            font=('Microsoft YaHei UI', 9)
        )
        log_count_label.pack(side="left", padx=(20, 0))

        # 保存按钮区域
        save_frame = tk.Frame(frame, bg=THEME['BG'])
        save_frame.pack(fill="x", pady=(30, 0))

        save_button = self.create_button(
            save_frame,
            "保存设置",
            self.save_global_settings,
            width=15
        )
        save_button.pack(side="right")

        return frame

    def create_section_label(self, parent, text):
        """创建分节标"""
        label = tk.Label(
            parent,
            text=text,
            bg=THEME['BG'],
            fg=THEME['BUTTON_FG'],
            font=('Microsoft YaHei UI', 13, 'bold')
        )
        label.pack(anchor="w")

    def create_button(self, parent, text, command, width=None):
        """统一样式的按钮"""
        button = tk.Button(
            parent,
            text=text,
            command=command,
            bg=THEME['BUTTON_BG'],
            fg=THEME['BUTTON_FG'],
            activebackground=THEME['BUTTON_ACTIVE_BG'],
            activeforeground=THEME['BUTTON_FG'],
            font=('Microsoft YaHei UI', 10),
            relief="groove",
            padx=25,
            pady=8,
            width=width if width else None,
            bd=1
        )
        
        # 添加鼠标悬停效果
        button.bind('<Enter>', lambda e: button.configure(bg=THEME['BUTTON_ACTIVE_BG']))
        button.bind('<Leave>', lambda e: button.configure(bg=THEME['BUTTON_BG']))
        
        return button

    def save_global_settings(self):
        """保存全局设置"""
        try:
            # 收集所有需要更新的设置
            updates = {}
            
            # 获取Tesseract路径
            tesseract_path = self.path_entry.get().strip()
            if tesseract_path:
                updates['tesseract_path'] = tesseract_path

            # 获取日志保存天数
            try:
                days = int(self.log_days_entry.get())
                if days < 1:
                    raise ValueError("日志保存天数必须大于0")
                updates['log_retention_days'] = days
            except ValueError as e:
                messagebox.showerror("错误", "请输入有效的日志保存天数")
                return

            # 一次性更新所有设置
            try:
                # 更新配置数据
                for key, value in updates.items():
                    self.config.config_data[key] = value
                
                # 只调用一次保存
                if self.config.save():
                    # 立即执行日志清理
                    from ..utils import cleanup_old_logs
                    cleanup_old_logs(self.config)
                    messagebox.showinfo("成功", "设置已保存并生效")
                else:
                    messagebox.showerror("错误", "保存设置失败")
                
            except Exception as e:
                logging.error(f"保存配置失败: {str(e)}")
                messagebox.showerror("错误", f"保存设置失败: {str(e)}")

        except Exception as e:
            logging.error(f"保存全局设置失败: {str(e)}")
            messagebox.showerror("错误", f"保存设置失败: {str(e)}")

    def create_ocr_frame(self, parent):
        """创建OCR设置页"""
        frame = tk.Frame(parent, bg=THEME['BG'])
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Tesseract路径设置
        path_label = tk.Label(
            frame, 
            text="Tesseract径:", 
            bg=THEME['BG'], 
            fg=THEME['BUTTON_FG']
        )
        path_label.pack(anchor="w", pady=(10, 5))

        path_frame = tk.Frame(frame, bg=THEME['BG'])
        path_frame.pack(fill="x", pady=(0, 10))

        self.path_entry = tk.Entry(
            path_frame, 
            bg=THEME['BUTTON_BG'], 
            fg=THEME['BUTTON_FG'],
            insertbackground=THEME['BUTTON_FG']
        )
        self.path_entry.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        # 设置当前路径
        current_path = self.config.get_tesseract_path()
        if current_path:
            self.path_entry.insert(0, current_path)

        browse_button = tk.Button(
            path_frame,
            text="浏览",
            command=self.browse_tesseract,
            bg=THEME['BUTTON_BG'],
            fg=THEME['BUTTON_FG'],
            activebackground=THEME['BUTTON_ACTIVE_BG']
        )
        browse_button.pack(side="right")

        return frame

    def create_key_frame(self, parent):
        """创建按键替换设置页"""
        frame = tk.Frame(parent, bg=THEME['BG'])
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 添说明文本
        info_text = "在 微软 中文输入的状下，将指定按键替换为目标字符\n    其他输入法未测试"
        info_label = tk.Label(
            frame,
            text=info_text,
            bg=THEME['BG'],
            fg=THEME['BUTTON_FG'],
            justify="left",
            wraplength=400
        )
        info_label.pack(anchor="w", pady=(10, 20))

        # 创建按键设置区域
        settings_frame = tk.Frame(frame, bg=THEME['BG'])
        settings_frame.pack(fill="x", padx=10)

        # 源按设置
        source_label = tk.Label(
            settings_frame,
            text="按键:",
            bg=THEME['BG'],
            fg=THEME['BUTTON_FG']
        )
        source_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")

        self.source_entry = tk.Entry(
            settings_frame,
            bg=THEME['BUTTON_BG'],
            fg=THEME['BUTTON_FG'],
            insertbackground=THEME['BUTTON_FG'],
            width=10
        )
        self.source_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.source_entry.insert(0, self.config.get_source_key() or "/")

        # 目标字符设置
        target_label = tk.Label(
            settings_frame,
            text="替换:",
            bg=THEME['BG'],
            fg=THEME['BUTTON_FG']
        )
        target_label.grid(row=0, column=2, padx=5, pady=5, sticky="e")

        self.target_entry = tk.Entry(
            settings_frame,
            bg=THEME['BUTTON_BG'],
            fg=THEME['BUTTON_FG'],
            insertbackground=THEME['BUTTON_FG'],
            width=10
        )
        self.target_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        self.target_entry.insert(0, self.config.get_target_char() or "、")

        # 保存按钮
        save_button = tk.Button(
            settings_frame,
            text="保存设置",
            command=self.save_key_settings,
            bg=THEME['BUTTON_BG'],
            fg=THEME['BUTTON_FG'],
            activebackground=THEME['BUTTON_ACTIVE_BG']
        )
        save_button.grid(row=0, column=4, padx=20, pady=5)

        # 添加提示信息
        tip_text = """
        提示：
        1. 源按键输入单个按键，如: / 或 . 等
        2. 目标字符输入替换后的字符，如: 、 或 。等
        """
        tip_label = tk.Label(
            frame,
            text=tip_text,
            bg=THEME['BG'],
            fg=THEME['BUTTON_FG'],
            justify="left",
            wraplength=400
        )
        tip_label.pack(anchor="w", pady=(20, 10))

        return frame

    def save_key_settings(self):
        """保存按键设置"""
        try:
            source_key = self.source_entry.get().strip()
            target_char = self.target_entry.get().strip()

            if not source_key or not target_char:
                messagebox.showerror("错误", "源按键和目标字符都不能为空")
                return

            if len(source_key) > 1 or len(target_char) > 1:
                messagebox.showerror("错误", "源按键和目标字符都必须是单个字符")
                return

            # 保存设置
            self.config.set_key_conversion(source_key, target_char)
            
            # 重启入法监控以应用新设置
            from main import MainApplication
            if hasattr(MainApplication, 'instance') and MainApplication.instance:
                ime_monitor = MainApplication.instance.ime_monitor
                if ime_monitor:
                    # 如果功能已启用，则重启监控
                    if ime_monitor.enabled:
                        # 保存当前的截图快捷键状态
                        screenshot_enabled = MainApplication.instance.hotkey_registered
                        
                        ime_monitor.stop_monitoring()  # 停止当前监控
                        time.sleep(0.1)  # 短暂延迟确保清理完成
                        ime_monitor.start_monitoring()  # 使用新设置启动监控
                        
                        # 如果截图功能之前是启用的，重新注册截图快键
                        if screenshot_enabled:
                            MainApplication.instance.toggle_screenshot(True)
                        
                        logging.info("已重启输入法监控以应用新设置")
                    else:
                        logging.info("输入法转换功能未启用，重启应用时生效")
            
            messagebox.showinfo("成功", "按键设置已保存并生效")
            logging.info(f"已保存按键设置 - 源按键: {source_key}, 目标字符: {target_char}")

        except Exception as e:
            logging.error(f"保存按键设置失败: {str(e)}")
            messagebox.showerror("错误", f"保存设置失败: {str(e)}")

    def create_monitor_frame(self, parent):
        """创建应用监听设置页"""
        frame = tk.Frame(parent, bg=THEME['BG'])
        frame.pack(fill="both", expand=True, padx=35, pady=30)

        # 添加说明文本
        info_text = "添加需要监听的应用程序，如果检测到程序未运行则自动启动\n重启间隔为0表示不进行重启\n        3. 设置后需要重启程序生效"
        info_label = tk.Label(
            frame,
            text=info_text,
            bg=THEME['BG'],
            fg="#808080",
            font=('Microsoft YaHei UI', 9),
            justify="left",
            wraplength=600
        )
        info_label.pack(anchor="w", pady=(0, 20))

        # 创建应用列表区域（带滚动条）
        list_container = tk.Frame(frame, bg=THEME['BG'])
        list_container.pack(fill="both", expand=True)

        # 创建Canvas和滚动条
        canvas = tk.Canvas(list_container, bg=THEME['BG'], highlightthickness=0)
        scrollbar = tk.Scrollbar(list_container, orient="vertical", command=canvas.yview)
        
        # 创建应用列表框架
        self.apps_frame = tk.Frame(canvas, bg=THEME['BG'])
        
        # 配置Canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.create_window((0, 0), window=self.apps_frame, anchor="nw")
        
        # 更新滚动区域
        def update_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        self.apps_frame.bind('<Configure>', update_scroll_region)

        # 放置Canvas和滚动条
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 按钮区域
        button_frame = tk.Frame(frame, bg=THEME['BG'])
        button_frame.pack(fill="x", pady=(20, 0))

        # 添加按钮
        add_button = self.create_button(
            button_frame,
            "添加",
            self._add_app,
            width=10
        )
        add_button.pack(side="left")

        # 保存按钮
        save_button = self.create_button(
            button_frame,
            "保存设置",
            self._save_monitor_settings,
            width=10
        )
        save_button.pack(side="right")

        # 加载现有应用列表
        self._load_apps_list()

        return frame

    def _save_monitor_settings(self):
        """保存应用监听设置"""
        try:
            apps_config = []

            for entry in self.app_entries:
                try:
                    # 获取当前UI中的值
                    launch_mode_value = entry['launch_mode_combo'].get()  # 直接从下拉框获取值
                    
                    is_tray_launch = launch_mode_value == "托盘启动"
                    
                    current_values = {
                        'path': entry['path'].get().strip(),
                        'check_interval': int(entry['check_interval'].get().strip()),
                        'restart_interval': int(entry['restart_interval'].get().strip())
                    }

                    # 验证输入
                    if not current_values['path']:
                        messagebox.showerror("错误", "应用路径不能为空")
                        return
                    if current_values['check_interval'] < 1:
                        messagebox.showerror("错误", "监听间隔必须大于0秒")
                        return
                    if current_values['restart_interval'] < 0:
                        messagebox.showerror("错误", "重启间隔不能为负数")
                        return

                    # 构建应用配置
                    app_config = {
                        'path': current_values['path'],
                        'name': os.path.basename(current_values['path']),
                        'check_interval': current_values['check_interval'],
                        'restart_interval': current_values['restart_interval'],
                        'minimize_to_tray': is_tray_launch  # 根据下拉框的值设置
                    }
                    
                    # 记录日志
                    logging.info(f"保存应用配置: {app_config['name']}, "
                               f"下拉框值: {launch_mode_value}, "
                               f"minimize_to_tray={app_config['minimize_to_tray']}")
                    
                    apps_config.append(app_config)

                except ValueError:
                    messagebox.showerror("错误", "请输入有效的时间间隔")
                    return

            # 更新配置
            new_config = {
                'enabled': True,  # 总是启用
                'apps': apps_config
            }

            # 保存配置前记录
            logging.debug(f"即将保存的配置: {new_config}")

            # 保存配置
            self.config.config_data['app_monitor'] = new_config
            save_success = self.config.save()
            
            if not save_success:
                logging.error("配置保存失败")
                messagebox.showerror("错误", "配置保存失败")
                return

            # 验证保存的配置
            saved_config = self.config.config_data.get('app_monitor', {})
            logging.debug(f"保存后的配置: {saved_config}")

            # 重新加载进程监控
            from main import MainApplication
            if hasattr(MainApplication, 'instance') and MainApplication.instance:
                if hasattr(MainApplication.instance, 'process_monitor'):
                    MainApplication.instance.process_monitor.reload_config()
                    logging.info("已重新加载进程监控配置")

            messagebox.showinfo("成功", "应用监听设置已保存")

        except Exception as e:
            logging.error(f"保存应用监听设置失败: {str(e)}")
            messagebox.showerror("错误", f"保存设置失败: {str(e)}")

    def _create_app_entry(self, app_data):
        """创建单个应用的设置行"""
        app_frame = tk.Frame(self.apps_frame, bg=THEME['BG'])
        app_frame.pack(fill="x", pady=(0, 15))  # 增加垂直间距

        # 创建内部框架
        inner_frame = tk.Frame(app_frame, bg=THEME['BG'])
        inner_frame.pack(fill="x", padx=5)

        # 第一行：应用路径和浏览按钮
        path_frame = tk.Frame(inner_frame, bg=THEME['BG'])
        path_frame.pack(fill="x", pady=(0, 5))  # 增加与下方的间距

        path_label = tk.Label(
            path_frame,
            text="监听应用：",
            bg=THEME['BG'],
            fg=THEME['BUTTON_FG'],
            font=('Microsoft YaHei UI', 10)
        )
        path_label.pack(side="left")

        path_entry = tk.Entry(
            path_frame,
            bg=THEME['BUTTON_BG'],
            fg=THEME['BUTTON_FG'],
            font=('Microsoft YaHei UI', 10),
            relief="flat",
            bd=1
        )
        path_entry.pack(side="left", expand=True, fill="x", padx=(0, 10))  # 增加右侧间距

        browse_button = self.create_button(
            path_frame,
            "浏览",
            lambda: self._browse_app(path_entry),
            width=8  # 固定按钮宽度
        )
        browse_button.pack(side="left", padx=(0, 10))  # 增加右侧间距

        delete_button = self.create_button(
            path_frame,
            "删除",
            lambda: self._remove_app_entry(app_frame, entry_data),
            width=8  # 固定按钮宽度
        )
        delete_button.pack(side="right")

        # 第二行：设置区域
        settings_frame = tk.Frame(inner_frame, bg=THEME['BG'])
        settings_frame.pack(fill="x", pady=(0, 5))

        # 监听间隔
        interval_frame = tk.Frame(settings_frame, bg=THEME['BG'])
        interval_frame.pack(side="left", padx=(0, 20))  # 增加右侧间距

        interval_label = tk.Label(
            interval_frame,
            text="监听间隔：",
            bg=THEME['BG'],
            fg=THEME['BUTTON_FG'],
            font=('Microsoft YaHei UI', 10)
        )
        interval_label.pack(side="left")

        interval_entry = tk.Entry(
            interval_frame,
            bg=THEME['BUTTON_BG'],
            fg=THEME['BUTTON_FG'],
            font=('Microsoft YaHei UI', 10),
            width=5,
            justify="center",
            relief="solid",
            bd=1
        )
        interval_entry.pack(side="left", padx=(0, 5))

        tk.Label(
            interval_frame,
            text="秒",
            bg=THEME['BG'],
            fg=THEME['BUTTON_FG'],
            font=('Microsoft YaHei UI', 10)
        ).pack(side="left")

        # 重启间隔
        restart_frame = tk.Frame(settings_frame, bg=THEME['BG'])
        restart_frame.pack(side="left", padx=(0, 20))

        restart_label = tk.Label(
            restart_frame,
            text="重启间隔：",
            bg=THEME['BG'],
            fg=THEME['BUTTON_FG'],
            font=('Microsoft YaHei UI', 10)
        )
        restart_label.pack(side="left")

        restart_entry = tk.Entry(
            restart_frame,
            bg=THEME['BUTTON_BG'],
            fg=THEME['BUTTON_FG'],
            font=('Microsoft YaHei UI', 10),
            width=5,
            justify="center",
            relief="solid",
            bd=1
        )
        restart_entry.pack(side="left", padx=(0, 5))

        tk.Label(
            restart_frame,
            text="秒",
            bg=THEME['BG'],
            fg=THEME['BUTTON_FG'],
            font=('Microsoft YaHei UI', 10)
        ).pack(side="left")

        # 启动方式
        launch_frame = tk.Frame(settings_frame, bg=THEME['BG'])
        launch_frame.pack(side="left")

        launch_label = tk.Label(
            launch_frame,
            text="启动方式：",
            bg=THEME['BG'],
            fg=THEME['BUTTON_FG'],
            font=('Microsoft YaHei UI', 10)
        )
        launch_label.pack(side="left")

        # 获取当前配置的启动方式
        minimize_to_tray = app_data.get('minimize_to_tray', False)
        
        # 创建StringVar并设置初始值
        tray_var = tk.StringVar()
        
        # 添加值变化的回调函数
        def on_launch_mode_change(*args):
            current_value = tray_var.get()

        # 绑定变量变化事件
        tray_var.trace_add("write", on_launch_mode_change)

        # 下拉框的选择事件
        def on_combobox_select(event):
            current_value = launch_mode_combo.get()

        launch_mode_combo = ttk.Combobox(
            launch_frame,
            textvariable=tray_var,
            values=["正常启动", "托盘启动"],
            state="readonly",
            width=8,
            font=('Microsoft YaHei UI', 10)
        )
        launch_mode_combo.pack(side="left")
        
        # 绑定下拉框选择事件
        launch_mode_combo.bind('<<ComboboxSelected>>', on_combobox_select)
        
        # 设置初始值
        initial_value = "托盘启动" if minimize_to_tray else "正常启动"
        launch_mode_combo.set(initial_value)
        tray_var.set(initial_value)  # 确保StringVar也被正确设置

        # 创建临时数据结构
        entry_data = {
            'frame': app_frame,
            'path': path_entry,
            'check_interval': interval_entry,
            'restart_interval': restart_entry,
            'minimize_to_tray': tray_var,
            'launch_mode_combo': launch_mode_combo  # 保留对下拉框的引用
        }

        # 设置入框的初始值
        path_entry.insert(0, app_data.get('path', ''))
        interval_entry.insert(0, str(app_data.get('check_interval', 1)))
        restart_entry.insert(0, str(app_data.get('restart_interval', 600)))

        return entry_data

    def _remove_app_entry(self, app_frame, entry_data):
        """从UI中移除应用条目"""
        app_frame.destroy()
        self.app_entries = [e for e in self.app_entries if e['frame'] != app_frame]

    def _browse_app(self, entry):
        """浏览并选择应用程序"""
        file_path = filedialog.askopenfilename(
            title="选择要监听的应用程序",
            filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")]
        )
        
        if file_path:
            entry.delete(0, tk.END)
            entry.insert(0, file_path)

    def _load_apps_list(self):
        """加载应用列表"""
        # 清除现有的应用列表
        for widget in self.apps_frame.winfo_children():
            widget.destroy()
        self.app_entries.clear()

        # 配置加载应用列表
        apps = self.config.get_monitored_apps()
        for app in apps:
            entry = self._create_app_entry(app)
            self.app_entries.append(entry)

    def _add_app(self):
        """添加新的应用监听"""
        try:
            file_path = filedialog.askopenfilename(
                title="选择要监听的应用程序",
                filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")],
                parent=self.window
            )
            
            if file_path:
                # 创建新的应用配置
                app_data = {
                    'path': file_path,
                    'name': os.path.basename(file_path),
                    'check_interval': 1,
                    'restart_interval': 600,  # 修改默认值为600秒（10分钟）
                    'minimize_to_tray': True
                }
                
                # 添加新的监听应用加到UI
                entry = self._create_app_entry(app_data)
                self.app_entries.append(entry)
                
                logging.info(f"已添加新的监听应用到UI: {file_path}")
                
        except Exception as e:
            logging.error(f"添加应用监听失败: {str(e)}")

    def _remove_app(self, app_frame, app_path):
        """删除应用监听"""
        app_frame.destroy()
        self.app_entries = [e for e in self.app_entries if e['frame'] != app_frame]
        self.config.remove_monitored_app(app_path)

    def browse_tesseract(self):
        """浏览并选择Tesseract路径"""
        file_path = filedialog.askopenfilename(
            title="选择Tesseract程序",
            filetypes=[
                ("Tesseract程序", "tesseract.exe"),
                ("所有文件", "*.*")
            ]
        )
        
        if file_path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, file_path)
            self.config.set_tesseract_path(file_path)
            logging.info(f"已更新Tesseract路径: {file_path}")

    def apply_style(self):
        """应用自定义样式"""
        style = ttk.Style()
        style.configure(
            "TNotebook", 
            background=THEME['BG'],
            borderwidth=0
        )
        style.configure(
            "TNotebook.Tab",
            background=THEME['BUTTON_BG'],
            foreground=THEME['BUTTON_FG'],
            padding=[10, 5],
            borderwidth=0
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", THEME['BUTTON_ACTIVE_BG'])],
            foreground=[("selected", THEME['BUTTON_FG'])]
        ) 

    def _on_checkbox_change(self, app_path, option_name, value):
        """处理复选框状态变化"""
        try:
            # 获取当前配置的深拷贝
            new_config = copy.deepcopy(self.config.config_data)
            
            # 更新对应应用的配置
            for app in new_config['app_monitor']['apps']:
                if app['path'] == app_path:
                    # 设置新值
                    app[option_name] = value
                    logging.info(f"更新应用配置 - {app['name']}: {option_name}={value}")
                    break
            
            # 保存配置
            self.config.config_data = new_config
            save_config(new_config)
            
            # 重新加载进程监控配置
            from main import MainApplication
            if hasattr(MainApplication, 'instance') and MainApplication.instance:
                if hasattr(MainApplication.instance, 'process_monitor'):
                    # 先停止所有监控
                    MainApplication.instance.process_monitor.stop_all(clear_config=False)
                    # 重新加载配置并启动监控
                    MainApplication.instance.process_monitor.reload_config()
                
        except Exception as e:
            logging.error(f"更新应用配置失败: {str(e)}")
            messagebox.showerror("错误", f"更新配置失败: {str(e)}")
            # 发生错误时恢复复选框状态
            for entry in self.app_entries:
                if entry['path'].get() == app_path:
                    if option_name == 'appenabled':
                        entry['enabled'].set(not value)
                    elif option_name == 'minimize_to_tray':
                        entry['minimize_to_tray'].set(not value)
                    break