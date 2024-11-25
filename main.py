import logging
import sys
import tkinter as tk
import threading
import queue
import keyboard
from tkinter import messagebox
import os
from tkinter import filedialog
import time

from src.utils import (
    setup_logging,
    global_exception_handler,
    cleanup_old_logs,
    Config,
    save_config
)
from src.core import ScreenshotTaker, IMEMonitor, ProcessMonitor
from src.ui import OptionsWindow, TrayManager
from src.utils.autostart import check_auto_start

class MainApplication:
    instance = None
    _config = None

    @classmethod
    def get_config(cls):
        if cls._config is None:
            cls._config = Config()
        return cls._config

    def __init__(self):
        """初始化主应用程序"""
        MainApplication.instance = self
        try:
            # 设置日志
            setup_logging()
            logging.info("程序启动")
            
            # 设置全局异常处理
            sys.excepthook = global_exception_handler
            
            # 检查必要的目录和文件
            self._check_required_files()
            
            # 创建主窗口（保持隐藏）
            try:
                self.root = tk.Tk()
                self.root.withdraw()
                logging.info("主窗口已创建")
            except Exception as e:
                logging.error(f"创建主窗口失败: {str(e)}")
                raise
            
            # 初始化配置
            try:
                self.config = self.get_config()
                logging.info("配置已加载")
                
                # 检查 Tesseract 路径
                self._check_tesseract_path()
                
            except Exception as e:
                logging.error(f"加载配置失败: {str(e)}")
                raise
            
            # 初始化截图功能
            try:
                self.screenshot_queue = queue.Queue()
                self.screenshot_taker = ScreenshotTaker(self.screenshot_queue)
                logging.info("截图功能已初始化")
            except Exception as e:
                logging.error(f"初始化截图功能失败: {str(e)}")
                raise
            
            # 初始化进程监控
            try:
                self.process_monitor = ProcessMonitor()
                
                # 将应用监控启动逻辑移到单独的方法中
                self._start_app_monitoring()
                
            except Exception as e:
                logging.error(f"初始化进程监控失败: {str(e)}")
                raise
            
            # 初始化托盘
            try:
                self.tray_manager = TrayManager(
                    screenshot_enabled_callback=self.toggle_screenshot,
                    ime_conversion_callback=self.toggle_ime_conversion,
                    app_monitor_callback=self.toggle_app_monitor
                )
                
                # 初始化输入法监控
                self.ime_monitor = IMEMonitor(self.tray_manager)
                logging.info("输入法监控已初始化")
                
            except Exception as e:
                logging.error(f"初始化失败: {str(e)}")
                raise
            
            # 初始化快捷键状态
            self.hotkey_registered = False
            
            # 清理旧日志文件
            cleanup_old_logs(self.config)
            
            # 同步自启动状态
            try:
                actual_auto_start = check_auto_start()
                if actual_auto_start != self.config.get_auto_start():
                    try:
                        self.config.set_auto_start(actual_auto_start)
                        logging.info(f"已同步自启动状态: {actual_auto_start}")
                    except Exception as e:
                        logging.error(f"更新自启动配置失败: {str(e)}")
            except Exception as e:
                logging.error(f"检查自启动状态失败: {str(e)}")
                # 不中断初始化流程，继续运行
            
        except Exception as e:
            logging.error(f"初始化失败: {str(e)}", exc_info=True)
            try:
                self._cleanup()
            except:
                pass
            # 尝试继续运行
            messagebox.showwarning("警告", "程序初始化部分失败，部分功能可能无法使用")

    def _check_required_files(self):
        """检查必要的文件和目录"""
        try:
            # 检查assets目录
            assets_dir = os.path.join(os.path.dirname(__file__), 'src', 'assets')
            if not os.path.exists(assets_dir):
                os.makedirs(assets_dir)
                logging.info(f"创建assets目录: {assets_dir}")
            
            # 检查图标文件
            icon_path = os.path.join(assets_dir, 'icon.png')
            if not os.path.exists(icon_path):
                logging.error(f"找不到图标文件: {icon_path}")
                raise FileNotFoundError(f"找不到图标文件: {icon_path}")
                
            logging.info("必要文件检查完成")
        except Exception as e:
            logging.error(f"检查必要文件失败: {str(e)}")
            raise

    def _check_tesseract_path(self):
        """检查 Tesseract 路径并在必要时请求用户选择"""
        tesseract_path = self.config.get_tesseract_path()
        
        if not tesseract_path or not os.path.exists(tesseract_path):
            logging.info("未设置 Tesseract 路径或路径无效，请求用户选择")
            
            response = messagebox.askyesno(
                "Tesseract 设置",
                "未检测到 Tesseract-OCR，是否现在设置？\n"
                "设置后才能使用文字识别功能。\n\n"
                "选择 tesseract.exe 文件的位置\n"
                "通常在 Tesseract-OCR 安装目录下"
            )
            
            if response:
                file_path = filedialog.askopenfilename(
                    title="选择 Tesseract 程序",
                    filetypes=[
                        ("Tesseract 程序", "tesseract.exe"),
                        ("所有文件", "*.*")
                    ]
                )
                
                if file_path:
                    if os.path.basename(file_path).lower() == 'tesseract.exe':
                        self.config.set_tesseract_path(file_path)
                        logging.info(f"已设置 Tesseract 路径: {file_path}")
                        messagebox.showinfo(
                            "设置成功",
                            "Tesseract 路径设置成功！\n"
                            "现在可以使用文字识别功能了。"
                        )
                    else:
                        logging.warning("选择的文件不是 tesseract.exe")
                        messagebox.showerror(
                            "误",
                            "请选择正确的 Tesseract 程序文件 (tesseract.exe)"
                        )
                else:
                    logging.info("用户取消选择 Tesseract 路径")
                    messagebox.showinfo(
                        "提示",
                        "未设置 Tesseract 路径，文字识别功能将不可用。\n"
                        "您可以稍后通过重启程序重新设置。"
                    )
            else:
                logging.info("用户选择跳过 Tesseract 设置")
                messagebox.showinfo(
                    "提示",
                    "未设置 Tesseract 路径，文字识别功能将不可用。\n"
                    "您可以稍后通过重启程序重新设置。"
                )

    def start(self):
        """启动应用程序"""
        try:
            logging.info("开始启动应用程序")
            
            # 启动截图队列监听
            self.root.after(100, self.display_options_from_queue)
            
            try:
                self.toggle_screenshot(True)
                logging.info("截图功能已启用")
            except Exception as e:
                logging.error(f"启用截图功能失败: {str(e)}")
                messagebox.showwarning("警告", "截图功能启动失败，请稍后重试")
            
            # 在子线程中运行托盘
            def run_tray():
                try:
                    self.tray_manager.icon.run()
                except Exception as e:
                    logging.error(f"托盘运行失败: {str(e)}")
                    # 如果托盘运行失败，尝试重新启动
                    time.sleep(1)
                    run_tray()
            
            tray_thread = threading.Thread(target=run_tray, daemon=True)
            tray_thread.start()
            
            # 设置窗口更新定时器
            def update_windows():
                try:
                    if self.root and self.root.winfo_exists():
                        self.root.update()
                    self.root.after(100, update_windows)
                except Exception as e:
                    logging.error(f"更新窗口失败: {str(e)}")
                    if self.root and self.root.winfo_exists():
                        self.root.after(100, update_windows)
            
            # 启动窗口更新
            self.root.after(100, update_windows)
            
            # 主线程运行 Tkinter 主循环
            self.root.mainloop()
                
        except Exception as e:
            logging.error(f"启动失败: {str(e)}", exc_info=True)
            messagebox.showerror("错误", "程序启动败，将尝试重新启动")
            try:
                self.root.after(1000, self.start)  # 尝试重新启动
            except:
                sys.exit(1)  # 如果重启也失败，则退出

    def display_options_from_queue(self):
        """处理截图队列"""
        try:
            while not self.screenshot_queue.empty():
                try:
                    img = self.screenshot_queue.get_nowait()  # 使用非阻塞方式获取
                    if img:
                        # 确保在主线程中创建窗口
                        def show_options():
                            try:
                                options_window = OptionsWindow(self.root, img, self.screenshot_queue)
                                # 确保窗口显示在前面
                                if hasattr(options_window, 'options_root') and options_window.options_root:
                                    options_window.options_root.lift()
                                    options_window.options_root.focus_force()
                                    # 设置窗口位置
                                    screen_width = self.root.winfo_screenwidth()
                                    screen_height = self.root.winfo_screenheight()
                                    window_width = options_window.options_root.winfo_width()
                                    window_height = options_window.options_root.winfo_height()
                                    x = (screen_width - window_width) // 2
                                    y = (screen_height - window_height) // 2
                                    options_window.options_root.geometry(f"+{x}+{y}")
                            except Exception as e:
                                logging.error(f"创建选项窗口失败: {str(e)}")
                        
                        # 使用 after_idle 确保在主线程中创建窗口
                        self.root.after_idle(show_options)
                        
                except queue.Empty:
                    break
                except Exception as e:
                    logging.error(f"处理单个截图失败: {str(e)}")
                    messagebox.showerror("错误", "处理截图失")
            
            # 继续监听队列
            if self.root and self.root.winfo_exists():
                self.root.after(100, self.display_options_from_queue)
                
        except Exception as e:
            logging.error(f"处理截图队列失败: {str(e)}")
            # 出错后延长重试时间，避免频繁报错//、
            if self.root and self.root.winfo_exists():
                self.root.after(1000, self.display_options_from_queue)

    def toggle_screenshot(self, enabled):
        """切换截图功能"""
        try:
            logging.info(f"切换截图功能: {enabled}")
            if enabled:
                if not self.hotkey_registered:
                    keyboard.add_hotkey('ctrl+alt+w', self.screenshot_taker.take_screenshot)
                    self.hotkey_registered = True
                    logging.info("截图快捷键已注册")
            else:
                if self.hotkey_registered:
                    keyboard.remove_hotkey('ctrl+alt+w')
                    self.hotkey_registered = False
                    logging.info("截图快捷键已移除")
                
            # 更新托盘状态
            self.tray_manager.update_screenshot_status(enabled)
            
        except Exception as e:
            logging.error(f"切换截图功能失败: {str(e)}")
            # 出错时尝试重新注册快捷键
            try:
                keyboard.remove_hotkey('ctrl+alt+w')
                if enabled:
                    keyboard.add_hotkey('ctrl+alt+w', self.screenshot_taker.take_screenshot)
                self.hotkey_registered = enabled
                logging.info(f"快捷键重置成功，状态: {enabled}")
            except Exception as e2:
                logging.error(f"重置快捷键失败: {str(e2)}")

    def toggle_ime_conversion(self, enabled):
        """切换输入法转换功能"""
        try:
            # 保存当前的截图快捷键状态
            screenshot_enabled = self.hotkey_registered
            
            # 切换输入法转换功能
            self.ime_monitor.toggle_ime_conversion(enabled)
            
            # 如果截图功能之前是启用的，重新注册截图快捷键
            if screenshot_enabled:
                self.toggle_screenshot(True)
                
        except Exception as e:
            logging.error(f"切换输入法转换失败: {str(e)}")

    def toggle_app_monitor(self, enabled):
        """切换应用监听功能"""
        try:
            logging.info(f"切换应用监听功能: {enabled}")
            # 只修改启用状态，不清空应用列表
            if 'app_monitor' not in self.config.config_data:
                self.config.config_data['app_monitor'] = {'enabled': False, 'apps': []}
            self.config.config_data['app_monitor']['enabled'] = enabled
            save_config(self.config.config_data)
            
            if enabled:
                # 启动应用监听
                apps = self.config.get_monitored_apps()
                if apps:
                    # 先停止所有监控
                    self.process_monitor.stop_all()
                    # 重新启动所启用的应用监听
                    for app in apps:
                        if app.get('enabled', True):
                            # 使用配置中的所有设置启动监控
                            self.process_monitor.start_monitoring(app)
                            logging.info(f"启动应用监控: {app['name']}")
                    logging.info("已启动应用监听")
                else:
                    logging.info("没有需要监听的应用")
                    # 如果没有配置的应用，自动关闭功能
                    self.tray_manager.update_app_monitor_status(False)
            else:
                # 停止所有监控，但不清空配置
                self.process_monitor.stop_all()
                logging.info("已停止所有应用监听")
                
        except Exception as e:
            logging.error(f"切换应用监听功能失败: {str(e)}")

    def restart_application(self):
        """重启应用程序"""
        try:
            # 获取当前程序路径
            import sys
            import subprocess
            program = sys.executable
            script = os.path.abspath(sys.argv[0])
            
            # 在主线程中执行重启
            def do_restart():
                try:
                    # 先启动新进程
                    subprocess.Popen([program, script])
                    
                    # 然后清理当前进程
                    try:
                        # 停止所有监控
                        if hasattr(self, 'process_monitor'):
                            self.process_monitor.stop_all()
                        
                        # 停止托盘图标
                        if hasattr(self, 'tray_manager'):
                            self.tray_manager.icon.stop()
                        
                        # 销毁所有窗口
                        if hasattr(self, 'root') and self.root:
                            # 销毁所有子窗口
                            for widget in self.root.winfo_children():
                                if isinstance(widget, tk.Toplevel):
                                    widget.destroy()
                            # 退出主循环并销毁主窗口
                            self.root.quit()
                            self.root.destroy()
                        
                        # 清除类实例引用
                        MainApplication.instance = None
                    except:
                        pass
                    
                    # 强制退出当前进程
                    os._exit(0)
                    
                except Exception as e:
                    logging.error(f"重启程序失败: {str(e)}")
                    messagebox.showerror("错误", "重启程序失败，请手动重启")
                    sys.exit(1)
            
            # 使用 after 方法确保在主线程中执行重启
            if self.root and self.root.winfo_exists():
                self.root.after(100, do_restart)
            else:
                do_restart()
                
        except Exception as e:
            logging.error(f"重启程序失败: {str(e)}")
            messagebox.showerror("错误", "重启程序失败，请手动重启")
            sys.exit(1)

    def _cleanup(self):
        """清理资源"""
        try:
            # 停止所有监控
            if hasattr(self, 'process_monitor'):
                self.process_monitor.stop_all()
            
            # 停止托盘图标
            if hasattr(self, 'tray_manager'):
                self.tray_manager.icon.stop()
            
            # 销毁所有窗口
            if hasattr(self, 'root') and self.root:
                # 销毁所有子窗口
                for widget in self.root.winfo_children():
                    if isinstance(widget, tk.Toplevel):
                        widget.destroy()
                # 退出主循环并销毁主窗口
                self.root.quit()
                self.root.destroy()
            
            # 清除类实例引用
            MainApplication.instance = None
        except:
            pass

    def _start_app_monitoring(self):
        """启动应用监控"""
        try:
            if self.config.get_app_monitor_enabled():
                apps = self.config.get_monitored_apps()
                for app in apps:
                    # 检查进程是否已经在运行
                    process_name = app['name']
                    if not self.process_monitor.is_process_running(process_name):
                        self.process_monitor.start_monitoring(app)
                        logging.info(f"启动应用监控: {app['name']}")
                    else:
                        # 如果进程已经在运行，只添加到监控列表
                        self.process_monitor.add_to_monitoring(app)
                        logging.info(f"添加已运行的进程到监控: {app['name']}")
        except Exception as e:
            logging.error(f"启动应用监控失败: {str(e)}")
            raise

def main():
    """程序入口点"""
    try:
        app = MainApplication()
        app.start()
    except Exception as e:
        logging.error(f"程序运行失败: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main() 