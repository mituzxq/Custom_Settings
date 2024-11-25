import tkinter as tk
from tkinter import Toplevel
import pyautogui
import logging
from io import BytesIO
from win32clipboard import (
    OpenClipboard,
    EmptyClipboard,
    SetClipboardData,
    CloseClipboard,
    CF_DIB
)
from ..utils.config import DARK_THEME
from ..utils.utils import safe_destroy
class ScreenshotTaker:
    def __init__(self, screenshot_queue):
        self.screenshot_queue = screenshot_queue
        self.start_x = 0
        self.start_y = 0
        self.rect = None
        self.root = None
        self.selection_root = None

    def take_screenshot(self):
        """截图功能实现"""
        try:
            # 清理之前的窗口
            self.cleanup()
            
            # 创建新窗口
            try:
                self.root = tk.Tk()
                self.root.withdraw()
                
                # 创建选择窗口
                self.selection_root = Toplevel(self.root)
                self.selection_root.title("截图")
                
                # 设置窗口属性
                self.selection_root.attributes(
                    "-fullscreen", True,
                    "-alpha", 0.3,
                    "-topmost", True
                )
                self.selection_root.overrideredirect(1)  # 无边框
                
                # 确保窗口在最前面
                self.selection_root.lift()
                self.selection_root.focus_force()
                
                # 创建画布
                canvas = tk.Canvas(
                    self.selection_root,
                    cursor="cross",
                    bg=DARK_THEME['CANVAS_BG'],
                    highlightthickness=0
                )
                canvas.pack(fill="both", expand=True)
                
                # 绑定事件
                canvas.bind("<Button-1>", self.on_mouse_down)
                canvas.bind("<B1-Motion>", self.on_mouse_drag)
                canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
                
                # 绑定ESC键退出
                self.selection_root.bind("<Escape>", lambda e: self.cancel_screenshot())
                
                # 进入主循环
                self.root.mainloop()
                
            except tk.TclError as e:
                if "application has been destroyed" in str(e):
                    logging.info("窗口已被销毁，重新创建")
                    self.cleanup()
                    return
                raise
                
        except Exception as e:
            logging.error(f"截图功能出错: {str(e)}")
            self.cleanup()

    def cancel_screenshot(self):
        """取消截图"""
        try:
            if hasattr(self, 'selection_root') and self.selection_root:
                try:
                    self.selection_root.quit()
                except:
                    pass
                try:
                    self.selection_root.destroy()
                except:
                    pass
                self.selection_root = None
                
            if hasattr(self, 'root') and self.root:
                try:
                    self.root.quit()
                except:
                    pass
                try:
                    self.root.destroy()
                except:
                    pass
                self.root = None
                
        except Exception as e:
            logging.error(f"取消截图失败: {str(e)}")

    def cleanup(self):
        """清理资源"""
        try:
            # 先检查并清理图片资源
            if hasattr(self, 'img'):
                try:
                    del self.img
                except Exception as e:
                    logging.error(f"清理图片资源失败: {str(e)}")

            # 检查并清理选择窗口
            if hasattr(self, 'selection_root') and self.selection_root:
                try:
                    self.selection_root.destroy()
                except Exception as e:
                    logging.error(f"销毁选择窗口失败: {str(e)}")
                finally:
                    self.selection_root = None

            # 检查并清理根窗口
            if hasattr(self, 'root') and self.root:
                try:
                    self.root.destroy()
                except Exception as e:
                    logging.error(f"销毁根窗口失败: {str(e)}")
                finally:
                    self.root = None

            # 强制垃圾回收
            try:
                import gc
                gc.collect()
            except Exception as e:
                logging.error(f"垃圾回收失败: {str(e)}")

        except Exception as e:
            logging.error(f"清理资源失败: {str(e)}")
        finally:
            # 确保所有引用都被清除
            for attr in ['img', 'selection_root', 'root', 'rect']:
                if hasattr(self, attr):
                    try:
                        delattr(self, attr)
                    except:
                        pass

    def on_mouse_down(self, event):
        try:
            self.start_x, self.start_y = event.x, event.y
            self.rect = event.widget.create_rectangle(
                self.start_x, self.start_y, 
                self.start_x, self.start_y, 
                outline='#00ff00',
                width=2
            )
        except Exception as e:
            logging.error(f"鼠标按下事件处理出错: {str(e)}")

    def on_mouse_drag(self, event):
        try:
            if self.rect:
                event.widget.coords(
                    self.rect,
                    self.start_x, self.start_y,
                    event.x, event.y
                )
        except Exception as e:
            logging.error(f"鼠标拖动事件处理出错: {str(e)}")

    def on_mouse_up(self, event):
        try:
            # 计算截图区域的宽度和高度
            width = abs(event.x - self.start_x)
            height = abs(event.y - self.start_y)
            
            # 如果截图区域太小，则取消截图
            if width < 5 or height < 5:  # 设置最小阈值为5像素
                self.cancel_screenshot()
                return
            
            # 隐藏选择窗口
            try:
                if self.selection_root:
                    self.selection_root.withdraw()
            except:
                pass
            
            # 截取屏幕
            try:
                img = pyautogui.screenshot(region=(
                    min(self.start_x, event.x), 
                    min(self.start_y, event.y),
                    width, 
                    height
                ))
                
                # 复制到剪贴板
                self._copy_to_clipboard(img)
                
                # 放入队列
                if self.screenshot_queue:
                    self.screenshot_queue.put(img)
                
            except Exception as e:
                logging.error(f"截取屏幕失败: {str(e)}")
            
            # 清理窗口
            self.cleanup()
            
        except Exception as e:
            logging.error(f"鼠标释放事件处理出错: {str(e)}")
            self.cleanup()

    def _copy_to_clipboard(self, img):
        """将图片复制到剪贴板"""
        if img and img.width > 0 and img.height > 0:
            try:
                output = BytesIO()
                img.convert('RGB').save(output, 'BMP')
                data = output.getvalue()[14:]
                output.close()
                
                OpenClipboard()
                EmptyClipboard()
                SetClipboardData(CF_DIB, data)
                CloseClipboard()
                
            except Exception as e:
                logging.error(f"复制到剪贴板失败: {str(e)}") 
