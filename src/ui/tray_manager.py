import pystray
from PIL import Image
import os
import logging
from .config_window import ConfigWindow
from ..utils.config import Config, save_config
import tkinter as tk
import threading
import queue
import tkinter.messagebox as messagebox
from ..utils.autostart import set_auto_start, check_auto_start
from ..utils import get_resource_path

class TrayManager:
    def __init__(self, screenshot_enabled_callback, ime_conversion_callback, app_monitor_callback=None):
        # 修改图标加载路径
        icon_path = get_resource_path(os.path.join('src', 'assets', 'icon.png'))
        image = Image.open(icon_path)
        
        self.screenshot_enabled = True  # 截图功能默认启用
        self.ime_enabled = False  # 输入法转换默认禁用
        
        # 初始化配置
        self.config = Config()
        
        # 从配置中读取应用监听状态
        self.app_monitor_enabled = self.config.get_app_monitor_enabled()
        
        # 从配置中读取自启动状态
        self.auto_start = self.config.get_auto_start()
        
        # 保存配置窗口引用
        self.config_window = None
        self.config_root = None
        self.root = None
        
        # 添加窗口创建队列
        self.window_queue = queue.Queue()
        
        # 创建主窗口
        self.root = tk.Tk()
        self.root.withdraw()
        
        # 启动窗口检查定时器
        self.root.after(100, self.check_window_queue)
        
        # 创建菜单项
        menu = (
            pystray.MenuItem(
                "启用OCR",
                lambda item: self._toggle_screenshot(screenshot_enabled_callback),
                checked=lambda item: self.screenshot_enabled
            ),
            pystray.MenuItem(
                "按键替换",
                lambda item: self._toggle_ime(ime_conversion_callback),
                checked=lambda item: self.ime_enabled
            ),
            pystray.MenuItem(
                "应用监听",
                lambda item: self._toggle_app_monitor(app_monitor_callback) if app_monitor_callback else None,
                checked=lambda item: self.app_monitor_enabled
            ),
            pystray.MenuItem(
                "开机自启",
                self._toggle_auto_start,
                checked=lambda item: self.auto_start
            ),
            pystray.MenuItem(
                "配置",
                self._show_config
            ),
            pystray.MenuItem(
                "退出",
                self._quit
            )
        )
        
        # 创建托盘图标
        self.icon = pystray.Icon(
            "custom_settings_Bymy",
            image,
            "截图工具",
            pystray.Menu(*menu)
        )
        
        logging.info("托盘管理器初始化完成")
    
    def check_window_queue(self):
        """检查是否需要创建新窗口"""
        try:
            if not self.window_queue.empty():
                # 只处理队列中的最新一个请求
                while not self.window_queue.empty():
                    self.window_queue.get()
                self._create_config_window()
        except Exception as e:
            logging.error(f"检查窗口队列失败: {str(e)}")
        finally:
            if self.root and self.root.winfo_exists():
                self.root.after(100, self.check_window_queue)
    
    def _quit(self, item):
        """退出程序"""
        try:
            logging.info("开始退出程序")
            # 停止图标
            self.icon.stop()
            
            # 清理窗口
            if self.config_window:
                try:
                    self.config_window.window.destroy()
                except:
                    pass
            
            if self.root:
                try:
                    self.root.quit()
                    self.root.destroy()
                except:
                    pass
            
            # 强制退出程序
            logging.info("程序退出")
            os._exit(0)
            
        except Exception as e:
            logging.error(f"退出程序失败: {str(e)}")
            os._exit(1)
    
    def _show_config(self, item):
        """显示配置窗口"""
        try:
            # 如果配置窗口已经存在，就显示它
            if self.config_window and self.config_window.window:
                self.config_window.window.deiconify()
                self.config_window.window.lift()
                return
            
            # 将创建窗口的请求加入队列
            self.window_queue.put(True)
            
        except Exception as e:
            logging.error(f"请求创建配置窗口失败: {str(e)}")
    
    def _create_config_window(self):
        """在主线程中创建配置窗口"""
        try:
            # 创建配置窗口
            self.config_window = ConfigWindow(self.root, self.config)
            
            # 确保窗口显示
            if self.config_window and self.config_window.window:
                # 设置窗口在屏幕中央
                window = self.config_window.window
                window.update_idletasks()
                width = window.winfo_width()
                height = window.winfo_height()
                x = (window.winfo_screenwidth() // 2) - (width // 2)
                y = (window.winfo_screenheight() // 2) - (height // 2)
                window.geometry(f'+{x}+{y}')
                
                # 显示窗口
                window.deiconify()
                window.lift()
                window.focus_force()
            
            # 设置窗口关闭处理
            def on_window_close():
                if self.config_window:
                    self.config_window.window.destroy()
                    self.config_window = None
            
            # 绑定窗口关闭事件
            if self.config_window and self.config_window.window:
                self.config_window.window.protocol("WM_DELETE_WINDOW", on_window_close)
            
        except Exception as e:
            logging.error(f"创建配置窗口失败: {str(e)}", exc_info=True)
            if self.config_window:
                self.config_window = None
    
    def _toggle_screenshot(self, callback):
        """切换截图功能状态"""
        self.screenshot_enabled = not self.screenshot_enabled
        callback(self.screenshot_enabled)
        self.icon.update_menu()
        logging.info(f"截图功能状态: {'启用' if self.screenshot_enabled else '禁用'}")
    
    def _toggle_ime(self, callback):
        """切换输入法转换状态"""
        self.ime_enabled = not self.ime_enabled
        callback(self.ime_enabled)
        self.icon.update_menu()
        logging.info(f"输入法转换状态: {'启用' if self.ime_enabled else '禁用'}")
    
    def update_ime_status(self, enabled):
        """更新输入法转换状态"""
        self.ime_enabled = enabled
        self.icon.update_menu()
        logging.info(f"更新输入法转换状态: {'启用' if enabled else '禁用'}")
    
    def update_screenshot_status(self, enabled):
        """更新截图功能状态"""
        self.screenshot_enabled = enabled
        self.icon.update_menu()
        logging.info(f"更新截图功能状态: {'启用' if enabled else '禁用'}")
    
    def _toggle_app_monitor(self, callback):
        """切换应用监听状态"""
        try:
            # 切换状态前先检查是否有配置的应用
            apps = self.config.get_monitored_apps()
            if not apps and not self.app_monitor_enabled:
                messagebox.showwarning("提示", "请先在配置中添加需要监听的应用")
                return
            
            # 切换总开关状态
            self.app_monitor_enabled = not self.app_monitor_enabled
            
            # 保持原有配置完全不变，只修改总开关状态
            current_config = self.config.config_data.get('app_monitor', {})
            current_config['enabled'] = self.app_monitor_enabled
            
            # 确保不丢失任何配置
            self.config.config_data['app_monitor'] = current_config
            
            # 保存配置
            save_config(self.config.config_data)
            
            # 更新托盘菜单
            self.icon.update_menu()
            logging.info(f"应用监听状态: {'启用' if self.app_monitor_enabled else '禁用'}")
            
            # 直接调用回调函数
            if callback:
                callback(self.app_monitor_enabled)
                
        except Exception as e:
            logging.error(f"切换应用监听状态失败: {str(e)}")
    
    def update_app_monitor_status(self, enabled):
        """更新应用监听状态"""
        self.app_monitor_enabled = enabled
        self.icon.update_menu()
        logging.info(f"更新应用监听状态: {'启用' if enabled else '禁用'}")
    
    def set_app_monitor_callback(self, callback):
        """设置应用监听回调函数"""
        self.app_monitor_callback = callback
    
    def run(self):
        """运行托盘图标"""
        logging.info("托盘图标开始运行")
        
        try:
            # 确保在主线程中运行
            if threading.current_thread() is threading.main_thread():
                # 设置定时器更新窗口
                def update_root():
                    try:
                        if self.root and self.root.winfo_exists():
                            self.root.update()
                        if self.icon and self.icon._running:
                            self.root.after(100, update_root)
                    except Exception as e:
                        logging.error(f"更新窗口失败: {str(e)}")
                        if self.icon and self.icon._running:
                            self.root.after(100, update_root)
                
                # 启动更新定时器
                self.root.after(100, update_root)
                
                # 运行托盘图标
                self.icon.run()
            else:
                logging.error("托盘必须在主线程中运行")
                raise RuntimeError("托盘必须在主线程中运行")
                
        except Exception as e:
            logging.error(f"托盘管理器运行失败: {str(e)}")
            self._cleanup()
            raise
    
    def _cleanup(self):
        """清理资源"""
        try:
            if hasattr(self, 'icon') and self.icon:
                try:
                    self.icon.stop()
                except:
                    pass
            
            if hasattr(self, 'root') and self.root:
                try:
                    self.root.quit()
                    self.root.destroy()
                except:
                    pass
            
            if hasattr(self, 'update_thread') and self.update_thread:
                try:
                    self.update_thread.join(timeout=1)
                except:
                    pass
                
        except Exception as e:
            logging.error(f"清理托盘资源失败: {str(e)}")
    
    def _recreate_icon(self):
        """重新创建托盘图标"""
        try:
            if hasattr(self, 'icon'):
                try:
                    self.icon.stop()
                except:
                    pass
            
            # 加载图标图像
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'icon.png')
            image = Image.open(icon_path)
            
            # 创建新的托盘图标
            self.icon = pystray.Icon(
                "custom_settings_Bymy",
                image,
                "截图工具",
                self.icon.menu if hasattr(self, 'icon') else None
            )
            logging.info("托盘图标已重新创建")
        except Exception as e:
            logging.error(f"重新创建托盘图标失败: {str(e)}")
    
    def _toggle_auto_start(self, item):
        """切换自启动状态"""
        try:
            # 保存当前状态以便恢复
            original_state = self.auto_start
            
            # 尝试切换状态
            self.auto_start = not self.auto_start
            
            try:
                if set_auto_start(self.auto_start):
                    try:
                        # 更新配置
                        self.config.set_auto_start(self.auto_start)
                        # 更新菜单
                        self.icon.update_menu()
                        logging.info(f"自启动已{'启用' if self.auto_start else '禁用'}")
                    except Exception as e:
                        logging.error(f"更新配置或菜单失败: {str(e)}")
                        raise
                else:
                    raise Exception("设置自启动失败")
                    
            except Exception as e:
                # 恢复原始状态
                self.auto_start = original_state
                self.icon.update_menu()
                logging.error(f"切换自启动失败: {str(e)}")
                messagebox.showerror("错误", "设置自启动失败，请检查权限或以管理员身份运行")
                
        except Exception as e:
            logging.error(f"处理自启动切换失败: {str(e)}")
            # 确保状态一致性
            try:
                actual_state = check_auto_start()
                self.auto_start = actual_state
                self.icon.update_menu()
            except:
                pass