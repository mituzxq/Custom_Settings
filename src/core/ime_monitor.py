import keyboard
import logging
import threading
import time
import ctypes
from ..utils.config import Config

# 加载需要的 DLL
imm32 = ctypes.windll.imm32
user32 = ctypes.windll.user32

class IMEMonitor:
    def __init__(self, tray_manager):
        logging.info("初始化IMEMonitor")
        self.config = Config()
        self.tray_manager = tray_manager
        self.enabled = self.config.get_ime_conversion_enabled()
        logging.info(f"IME转换功能初始状态: {self.enabled}")
        self.running = False
        self.monitor_thread = None
        self.last_conversion_time = 0  # 添加时间戳记录
        
        # 更新托盘状态
        self.tray_manager.update_ime_status(self.enabled)
        
        # 如果功能已启用，立即启动监控
        if self.enabled:
            logging.info("IME转换功能已启用，开始监控")
            self.start_monitoring()
        else:
            logging.info("IME转换功能未启用")
    
    def toggle_ime_conversion(self, enabled):
        """切换输入法转换功能"""
        try:
            logging.info(f"切换IME转换功能: {enabled}")
            self.enabled = enabled
            self.config.set_ime_conversion_enabled(enabled)
            self.tray_manager.update_ime_status(enabled)
            
            if enabled and not self.running:
                logging.info("启动IME监控")
                self.start_monitoring()
            elif not enabled and self.running:
                logging.info("停止IME监控")
                self.stop_monitoring()
                
            logging.info(f"IME转换功能已{'启用' if enabled else '禁用'}")
        except Exception as e:
            logging.error(f"切换IME转换功能失败: {str(e)}", exc_info=True)
    
    def start_monitoring(self):
        """启动监控"""
        try:
            if not self.running:
                self.running = True
                self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
                self.monitor_thread.start()
                logging.info("IME监控线程已启动")
            else:
                logging.info("IME监控已在运行中")
        except Exception as e:
            logging.error(f"启动IME监控失败: {str(e)}", exc_info=True)
    
    def stop_monitoring(self):
        """停止监控"""
        try:
            logging.info("正在停止IME监控")
            self.running = False
            if self.monitor_thread:
                self._safe_unhook_all()  # 使用安全的钩子移除方法
                self.monitor_thread.join(timeout=1)
                logging.info("IME监控线程已停止")
        except Exception as e:
            logging.error(f"停止IME监控失败: {str(e)}")
    
    def _monitor_loop(self):
        """监控循环"""
        try:
            # 获取源按键
            source_key = self.config.get_source_key()
            
            # 注册键盘钩子
            self.keyboard_hooks = []  # 存储当前类注册的钩子
            
            # 使用 try-except 包装每个钩子的注册
            try:
                self.keyboard_hooks.append(
                    keyboard.on_press_key(source_key, self._handle_keypress, suppress=True)
                )

                # 定义需要注册的按键
                keys_to_register = ['ctrl', 'alt', 'shift', 'win']
                for key in keys_to_register:
                    self.keyboard_hooks.append(
                        keyboard.on_press_key(key, self._on_keyboard_press)
                    )
                    self.keyboard_hooks.append(
                        keyboard.on_release_key(key, self._on_keyboard_release)
                    )

            except Exception as e:
                logging.error(f"注册键盘钩子失败: {str(e)}")
                self.running = False
                return
            
            while self.running:
                time.sleep(0.1)
            
            # 安全地移除钩子
            self._safe_unhook_all()
            
        except Exception as e:
            logging.error(f"IME监控循环出错: {str(e)}", exc_info=True)
            self.running = False
            self._safe_unhook_all()
    
    def _safe_unhook_all(self):
        """安全地移除所有钩子"""
        if hasattr(self, 'keyboard_hooks'):
            for hook in self.keyboard_hooks:
                try:
                    if hook in keyboard._hooks:  # 检查钩子是否仍然存在
                        keyboard.unhook(hook)
                except Exception as e:
                    logging.error(f"移除钩子失败: {str(e)}")
            self.keyboard_hooks.clear()
    
    def _on_keyboard_press(self, event):
        """处理Shift键按下事件"""
        self.keyboard_pressed = True
    
    def _on_keyboard_release(self, event):
        """处理Shift键释放事件"""
        self.keyboard_pressed = False
    
    def _is_chinese_ime(self):
        """检查当前是否为中文输入法状态"""
        try:
            # 获取当前窗口句柄
            hwnd = user32.GetForegroundWindow()
            # 获取输入法上下文
            ime_hwnd = imm32.ImmGetDefaultIMEWnd(hwnd)
            
            if ime_hwnd:
                # 获取输入法状态
                result = user32.SendMessageW(ime_hwnd, 0x0283, 0x0005, 0)
                
                # 检查输入法开启状态
                is_ime_open = user32.SendMessageW(ime_hwnd, 0x0283, 0x0001, 0) != 0
                
                # 只要输入法是开启的就返回True
                return is_ime_open
            return False
        except Exception as e:
            logging.error(f"检查输入法状态失败: {str(e)}", exc_info=True)
            return False
    
    def _handle_keypress(self, event):
        """处理按键事件"""
        try:
            
            if not self.enabled:
                logging.info("IME转换功能未启用，不处理按键")
                return True
                
            if event.event_type != keyboard.KEY_DOWN:
                logging.info("非按下事件，不处理")
                return True

            # 检查是否正在按住Shift键
            if hasattr(self, 'keyboard_pressed') and self.keyboard_pressed:
                return True  # 让系统处理原始按键

            # 检查是否为中文输入法状态
            try:
                if self._is_chinese_ime():
                    # 获取目标字符
                    target_char = self.config.get_target_char()
                    keyboard.write(target_char)  # 输入目标字符
                    return False  # 阻止原始按键事件
                else:
                    pass
            except Exception as e:
                logging.error(f"检查输入法状态失败: {str(e)}")
                return True  # 出错时让系统处理原始按键
                
            return True

        except Exception as e:
            logging.error(f"处理按键事件失败: {str(e)}")
            # 出错时让系统处理原始按键，避免按键卡死
            return True