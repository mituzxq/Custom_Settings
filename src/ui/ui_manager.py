import tkinter as tk
from tkinter import Toplevel, filedialog, messagebox
from PIL import Image, ImageTk, ImageEnhance
import uuid
import pyautogui
import pytesseract
import logging
from ..utils.config import (
    Config,
    DARK_THEME
)
from ..utils.utils import safe_destroy
from ..core.screenshot import ScreenshotTaker

class OptionsWindow:
    def __init__(self, root, img, screenshot_queue=None):
        self.root = root
        self.img = img
        self.screenshot_queue = screenshot_queue
        self.options_root = None
        self.config = Config()
        self.setup_window()

    def setup_window(self):
        try:
            self.options_root = Toplevel(self.root)
            self.options_root.title("截图选项")
            self.options_root.configure(bg=DARK_THEME['BG'])
            self.options_root.attributes("-topmost", True)

            # 创建主容器框架
            main_container = tk.Frame(self.options_root, bg=DARK_THEME['BG'])
            main_container.pack(expand=True, fill="both")

            # 创建图片显示的滚动容器
            canvas_container = tk.Frame(main_container, bg=DARK_THEME['BG'])
            canvas_container.pack(expand=True, fill="both", padx=10, pady=(10, 5))

            # 创建画布和滚动条
            canvas = tk.Canvas(canvas_container, bg=DARK_THEME['BG'], highlightthickness=0)
            scrollbar_y = tk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview)
            
            # 配置画布滚动
            canvas.configure(
                yscrollcommand=scrollbar_y.set
            )

            # 创建框架来放置图片
            image_frame = tk.Frame(canvas, bg=DARK_THEME['BG'])
            canvas.create_window((0, 0), window=image_frame, anchor="nw")

            # 计算适当的图片显示尺寸
            screen_width = self.options_root.winfo_screenwidth()
            screen_height = self.options_root.winfo_screenheight()
            max_width = int(screen_width * 0.9)
            max_height = int(screen_height * 0.9)

            # 调整图片大小
            img_width, img_height = self.img.size
            scale = min(max_width/img_width, max_height/img_height)
            
            if scale < 1:  # 只有当图片需要缩小时才调整大小
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                display_img = self.img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            else:
                display_img = self.img

            # 显示图片
            self.img_display = ImageTk.PhotoImage(display_img)
            img_label = tk.Label(image_frame, image=self.img_display, bg=DARK_THEME['BG'])
            img_label.image = self.img_display
            img_label.pack(expand=True)

            # 创建按钮框架并放在底部
            button_frame = tk.Frame(main_container, bg=DARK_THEME['BG'])
            button_frame.pack(side="bottom", fill="x", padx=10, pady=10)

            # 创建一个内部框架来容纳按钮，实现居中效果
            inner_button_frame = tk.Frame(button_frame, bg=DARK_THEME['BG'])
            inner_button_frame.pack(expand=True)  # 使用expand=True来居中

            # 按钮样式
            button_style = {
                'bg': DARK_THEME['BUTTON_BG'],
                'fg': DARK_THEME['BUTTON_FG'],
                'activebackground': DARK_THEME['BUTTON_ACTIVE_BG'],
                'activeforeground': DARK_THEME['BUTTON_FG'],
                'relief': 'flat',
                'padx': 15,
                'pady': 8,
                'font': ('Microsoft YaHei UI', 10)
            }

            # 创建按钮
            buttons = [
                ("重新截取", self.retake),
                ("文字提取", self.extract_text),
                ("保存", self.save),
                ("取消", self.cancel)
            ]

            for text, command in buttons:
                button = tk.Button(
                    inner_button_frame,  # 改为使用inner_button_frame
                    text=text,
                    command=command,
                    **button_style
                )
                button.pack(side="left", padx=10)
                
                button.bind('<Enter>', lambda e, btn=button: 
                    btn.configure(bg=DARK_THEME['BUTTON_ACTIVE_BG']))
                button.bind('<Leave>', lambda e, btn=button: 
                    btn.configure(bg=DARK_THEME['BUTTON_BG']))

            # 配置滚动区域
            def configure_scroll_region(event):
                canvas.configure(scrollregion=canvas.bbox("all"))
                
                # 设置最小显示区域
                min_width = min(img_label.winfo_reqwidth(), max_width)
                min_height = min(img_label.winfo_reqheight(), max_height)
                canvas.configure(width=min_width, height=min_height)
                
                # 根据内容决定是否显示滚动条
                if img_label.winfo_reqheight() > max_height:
                    scrollbar_y.pack(side="right", fill="y")
                
                canvas.pack(side="left", expand=True, fill="both")

            image_frame.bind('<Configure>', configure_scroll_region)

            # 添加鼠标滚轮支持
            def on_mousewheel(event):
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            canvas.bind_all("<MouseWheel>", on_mousewheel)

            # 调整窗口位置
            self.options_root.update_idletasks()
            width = min(self.options_root.winfo_reqwidth(), max_width + 50)  # 添加一些边距
            height = min(self.options_root.winfo_reqheight(), max_height + 100)  # 为按钮预留空间
            x = (screen_width // 2) - (width // 2)
            y = (screen_height // 2) - (height // 2)
            self.options_root.geometry(f"{width}x{height}+{x}+{y}")

            # ESC键关闭窗口
            self.options_root.bind('<Key>', lambda e: self.cancel() if e.keysym == 'Escape' else None)
            self.options_root.protocol("WM_DELETE_WINDOW", self.cancel)

            # 绑定 Ctrl + S 以保存
            self.options_root.bind('<Control-s>', lambda e: self.save())

            # 添加进度条显示
            self.progress_var = tk.StringVar()
            progress_label = tk.Label(
                main_container,
                textvariable=self.progress_var,
                bg=DARK_THEME['BG'],
                fg=DARK_THEME['BUTTON_FG']
            )
            progress_label.pack()

        except Exception as e:
            logging.error(f"显示选项窗口出错: {str(e)}")
            messagebox.showerror("错误", "显示选项窗口失败")

    def retake(self):
        """重新截图"""
        safe_destroy(self.options_root)
        if self.screenshot_queue:
            screenshot_taker = ScreenshotTaker(self.screenshot_queue)
            screenshot_taker.take_screenshot()
        else:
            logging.error("没有可用的截图队列")

    def extract_text(self):
        """提取文字"""
        try:
            # 检查Tesseract路径
            tesseract_path = self.config.get_tesseract_path()
            
            if not tesseract_path:
                logging.warning("未设置Tesseract路径")
                messagebox.showerror(
                    "错误",
                    "未设置Tesseract路径，无法使用文字识别功能"
                )
                return
            
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            
            # 优化图片预处理
            width, height = self.img.size
            # 获取屏幕分辨率
            screen_width, screen_height = pyautogui.size()
            max_img_px = width * height
            max_screen_px = screen_width * screen_height
            if max_img_px >= max_screen_px * 0.7:
                scale_factor = 1
            else:
                scale_factor = 2
            
            enlarged_img = self.img.resize((width * scale_factor, height * scale_factor), Image.Resampling.LANCZOS)
            
            # 转换为灰度图并增强
            gray_image = enlarged_img.convert('L')
            enhancer = ImageEnhance.Contrast(gray_image)
            enhanced_image = enhancer.enhance(2.5)
            brightness = ImageEnhance.Brightness(enhanced_image)
            enhanced_image = brightness.enhance(1.2)
            
            # OCR配置
            custom_config = r'''--oem 3 
                --psm 6 
                -c preserve_interword_spaces=1
            '''
            
            # OCR识别
            text = pytesseract.image_to_string(
                enhanced_image,
                lang='chi_sim+eng+equ',
                config=custom_config
            )
            
            # 清理文本
            lines = []
            for line in text.splitlines():
                line = line.strip()
                if line and not line.isspace():
                    line = ' '.join(line.split())
                    lines.append(line)
            text = '\n'.join(lines)
            
            # 复制到剪贴板
            self.root.clipboard_clear()
            self.root.clipboard_append(text)

            # 显示文本窗口
            text_window = Toplevel(self.options_root)
            text_window.title("提取的文字")
            text_window.configure(bg=DARK_THEME['BG'])
            text_window.attributes("-topmost", True)
            
            text_area = tk.Text(
                text_window, 
                wrap="word", 
                bg=DARK_THEME['BG'], 
                fg=DARK_THEME['BUTTON_FG'],
                insertbackground=DARK_THEME['BUTTON_FG'],
                font=('Microsoft YaHei UI', 12),
                padx=10,
                pady=10
            )
            text_area.pack(expand=True, fill="both", padx=10, pady=10)
            text_area.insert("1.0", text)
            
            # 设置文本窗口大小和位置
            text_window.update_idletasks()

            window_width = min(text_window.winfo_screenwidth() * 0.8, 800)
            window_height = min(text_window.winfo_screenheight() * 0.8, 600)
            x = (text_window.winfo_screenwidth() // 2) - (window_width // 2)
            y = (text_window.winfo_screenheight() // 2) - (window_height // 2)
            text_window.geometry(f"{int(window_width)}x{int(window_height)}+{int(x)}+{int(y)}")
            
            text_window.protocol("WM_DELETE_WINDOW", self.cancel)
            
        except Exception as e:
            logging.error(f"文字提取失败: {str(e)}")
            messagebox.showerror("错误", f"文字提取失败: {str(e)}")

    def save(self):
        """保存图片"""
        try:
            # 临时取消置顶，以便文件对话框显示在前面
            self.options_root.attributes("-topmost", False)
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                initialfile=str(uuid.uuid4())[:8],
                filetypes=[
                    ("PNG 图片", "*.png"),
                    ("JPEG 图片", "*.jpg;*.jpeg"),
                    ("WebP 图片", "*.webp"),
                    ("所有文件", "*.*")
                ]
            )
            
            # 恢复置顶
            self.options_root.attributes("-topmost", True)
            self.options_root.lift()
            
            if file_path:
                file_ext = file_path.lower().split('.')[-1]
                save_params = {}
                if file_ext in ['jpg', 'jpeg']:
                    save_params['quality'] = 95
                elif file_ext == 'webp':
                    save_params['quality'] = 90
                    save_params['method'] = 6
                
                self.img.save(file_path, **save_params)
                safe_destroy(self.options_root)
        except Exception as e:
            logging.error(f"保存图片失败: {str(e)}")
            messagebox.showerror("错误", f"保存失败: {str(e)}")

    def cancel(self):
        """取消操作"""
        safe_destroy(self.options_root)