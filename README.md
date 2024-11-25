# Custom Settings

## 主要功能

### 1. 输入法按键替换
- 在中文输入法状态下自动替换指定按键（屏蔽按下'ctrl', 'alt','shift','win'+'/'）
- 支持自定义按键映射规则（如将"/"替换为"、"）
- 针对微软拼音输入法优化
- 支持快速开启/关闭替换功能

### 2. 应用程序监控
- 监控指定程序的运行状态
- 自动重启未运行的程序
- 支持自定义监控间隔和重启间隔
- 支持托盘启动模式
- 可配置多个应用程序同时监控
- 添加或删除配置后重启程序生效

### 3. 屏幕 OCR
- 支持屏幕区域截图
- 集成 Tesseract-OCR 引擎
- 快速识别屏幕文字
- 识别结果默认复制到剪贴板

## 安装说明

### 系统要求
- Windows 7/8/10/11
- Python 3.7+
- Tesseract-OCR 5.0+

### 安装步骤

1. 安装 Python 环境
- 从 [Python官网](https://www.python.org/downloads/) 下载并安装 Python 3.7+
- 确保将 Python 添加到系统环境变量

2. 安装 Tesseract-OCR
- 从 [Tesseract-OCR下载页](https://github.com/UB-Mannheim/tesseract/wiki) 下载安装包
- 安装时记住安装路径，后续需要在程序中配置

3. 安装依赖
- 使用 pip 安装 requirements.txt 中的所有库
- pip install -r requirements.txt

4. 打包为exe程序
- 运行 build.py 文件
- python build.py

### 日志与配置文件
- 用户目录下会生成一个.custom_settings_byMY文件夹
- 程序运行时会在.custom_settings_byMY文件夹下生成一个日志文件，名为 logxxx.log
- 日志文件会记录程序运行时的所有信息，包括错误和警告
- 程序运行时会在.custom_settings_byMY文件夹下生成一个配置文件，名为 config.json
- 配置文件用于存储程序的配置信息，包括输入法按键映射规则、应用程序监控列表等