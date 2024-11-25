import os
import json
import logging
import threading

# 深色主题颜色常量
DARK_THEME = {
    'BG': '#2b2b2b',
    'BUTTON_BG': '#3c3f41',
    'BUTTON_FG': '#ffffff',
    'BUTTON_ACTIVE_BG': '#4c4f51',
    'CANVAS_BG': '#1e1e1e'
}

# 浅色主题颜色常量（仅用于配置窗口）
LIGHT_THEME = {
    'BG': '#ffffff',
    'BUTTON_BG': '#f0f0f0',
    'BUTTON_FG': '#000000',
    'BUTTON_ACTIVE_BG': '#e0e0e0',
    'CANVAS_BG': '#f5f5f5'
}

# 用户配置文件路径
CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.custom_settings_byMY')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')

# 默认配置
DEFAULT_CONFIG = {
    'screenshot_enabled': True,
    'tesseract_path': '',    # 用于存储 Tesseract 路径
    'ime_conversion_enabled': False,  # 添加输入法转换功能的开关
    'key_conversion': {
        'source_key': '/',
        'target_char': '、'
    },
    'log_retention_days': 7,  # 添加日志保存天数配置
    'auto_start': False,  # 添加自启动配置
    'app_monitor': {
        'enabled': False,  # 应用监听功能
        'apps': [  # 格式: [{'path': '路径', 'name': '进程名', 'check_interval': 1, 'restart_interval': 60, 'minimize_to_tray': False}]
            # 示例：
            # {
            #     'path': 'D:/Programs/App/app.exe',  # 应用程序路径
            #     'name': 'app.exe',                  # 进程名称
            #     'check_interval': 1,                # 监听间隔（秒）
            #     'restart_interval': 60,             # 重启间隔（秒）
            #     'minimize_to_tray': False           # 是否托盘启动
            # }
        ]
    }
}

class Config:
    _instance = None
    _initialized = False
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if not self._initialized:
            with self._lock:
                if not self._initialized:  # 双重检查锁定
                    logging.info("开始初始化Config类")
                    self._config_lock = threading.Lock()
                    self.config_data = load_config()
                    self._initialized = True
    
    def get_tesseract_path(self):
        """获取 Tesseract 路径"""
        return self.config_data.get('tesseract_path', '')
    
    def set_tesseract_path(self, path):
        """设置 Tesseract 路径"""
        self.config_data['tesseract_path'] = path
        save_config(self.config_data)
    
    def get_ime_conversion_enabled(self):
        """获取输入法转换功能状态"""
        return self.config_data.get('ime_conversion_enabled', False)
    
    def set_ime_conversion_enabled(self, enabled):
        """设置输入法转换功能状态"""
        self.config_data['ime_conversion_enabled'] = enabled
        save_config(self.config_data)
    
    def get_source_key(self):
        """获取源按键"""
        return self.config_data.get('key_conversion', {}).get('source_key', '/')
    
    def get_target_char(self):
        """获取目标字符"""
        return self.config_data.get('key_conversion', {}).get('target_char', '、')
    
    def set_key_conversion(self, source_key, target_char):
        """设置按键转换配置"""
        self.config_data['key_conversion'] = {
            'source_key': source_key,
            'target_char': target_char
        }
        save_config(self.config_data)
    
    def get_log_retention_days(self):
        """获取日志保存天数"""
        return self.config_data.get('log_retention_days', 7)
    
    def set_log_retention_days(self, days):
        """设置日志保存天数"""
        self.config_data['log_retention_days'] = days
        save_config(self.config_data)
    
    def get_monitored_apps(self):
        """获取所有监听的应用列表"""
        with self._config_lock:
            return self.config_data.get('app_monitor', {}).get('apps', [])
    
    def get_app_monitor_enabled(self):
        """获取应用监听功能的启用状态"""
        with self._config_lock:
            return self.config_data.get('app_monitor', {}).get('enabled', False)
    
    def set_app_monitor_enabled(self, enabled):
        """设置应用监听功能的启用状态"""
        with self._config_lock:
            if 'app_monitor' not in self.config_data:
                self.config_data['app_monitor'] = DEFAULT_CONFIG['app_monitor'].copy()
            self.config_data['app_monitor']['enabled'] = enabled
            self.save()
            logging.info(f"应用监听功能状态已更新: {'启用' if enabled else '禁用'}")
    
    def add_monitored_app(self, app_path, check_interval=1, restart_interval=60, minimize_to_tray=False):
        """添加监听应用
        
        Args:
            app_path: 应用程序路径
            check_interval: 监听间隔（秒）
            restart_interval: 重启间隔（秒）
            minimize_to_tray: 是否托盘启动
        """
        with self._config_lock:
            try:
                if not os.path.exists(app_path):
                    logging.error(f"应用路径不存在: {app_path}")
                    return False

                if 'app_monitor' not in self.config_data:
                    self.config_data['app_monitor'] = DEFAULT_CONFIG['app_monitor'].copy()

                apps = self.config_data['app_monitor']['apps']
                process_name = os.path.basename(app_path)

                # 检查是否已存在
                for app in apps:
                    if app['path'] == app_path:
                        logging.info(f"应用已存在: {app_path}")
                        return False

                # 添加新应用
                new_app = {
                    'path': app_path,
                    'name': process_name,
                    'check_interval': max(1, check_interval),  # 确保最小间隔为1秒
                    'restart_interval': max(0, restart_interval),  # 允许0表示不重启
                    'minimize_to_tray': bool(minimize_to_tray)
                }
                
                apps.append(new_app)
                self.save()
                logging.info(f"已添加监听应用: {process_name}")
                return True

            except Exception as e:
                logging.error(f"添加监听应用失败: {str(e)}")
                return False
    
    def update_monitored_app(self, app_path, **kwargs):
        """更新监听应用的配置"""
        with self._config_lock:
            try:
                if 'app_monitor' not in self.config_data:
                    logging.error("应用监听配置不存在")
                    return False

                # 查找并更新应用配置
                updated = False
                for app in self.config_data['app_monitor']['apps']:
                    if app['path'] == app_path:
                        # 记录更新前的值
                        old_values = {k: app.get(k) for k in kwargs.keys()}
                        
                        # 更新各个字段
                        if 'check_interval' in kwargs:
                            app['check_interval'] = max(1, int(kwargs['check_interval']))
                        if 'restart_interval' in kwargs:
                            app['restart_interval'] = max(0, int(kwargs['restart_interval']))
                        if 'minimize_to_tray' in kwargs:
                            app['minimize_to_tray'] = bool(kwargs['minimize_to_tray'])
                        
                        # 更新进程名（以防路径改变）
                        app['name'] = os.path.basename(app_path)
                        
                        # 记录更新后的值
                        new_values = {k: app.get(k) for k in kwargs.keys()}
                        
                        # 记录具体的更改
                        changes = []
                        for key in kwargs:
                            if old_values[key] != new_values[key]:
                                changes.append(f"{key}: {old_values[key]} -> {new_values[key]}")
                        
                        if changes:
                            logging.info(f"更新应用配置 - {app['name']}: {', '.join(changes)}")
                        
                        updated = True
                        break

                if not updated:
                    logging.error(f"未找到应用: {app_path}")
                    return False

                self.save()
                return True

            except Exception as e:
                logging.error(f"更新监听应用配置失败: {str(e)}")
                return False
    
    def remove_monitored_app(self, app_path):
        """移除监听应用"""
        with self._config_lock:
            try:
                if 'app_monitor' not in self.config_data:
                    return False

                original_length = len(self.config_data['app_monitor']['apps'])
                self.config_data['app_monitor']['apps'] = [
                    app for app in self.config_data['app_monitor']['apps'] 
                    if app['path'] != app_path
                ]

                if len(self.config_data['app_monitor']['apps']) < original_length:
                    self.save()
                    logging.info(f"已移除监听应用: {app_path}")
                    return True
                else:
                    logging.info(f"未找到要移除的应用: {app_path}")
                    return False

            except Exception as e:
                logging.error(f"移除监听应用失败: {str(e)}")
                return False
    
    def get_app_config(self, app_path):
        """获取指定应用的配置"""
        with self._config_lock:
            try:
                if 'app_monitor' in self.config_data:
                    for app in self.config_data['app_monitor']['apps']:
                        if app['path'] == app_path:
                            return app.copy()  # 返回配置的副本
                return None
            except Exception as e:
                logging.error(f"获取应用配置失败: {str(e)}")
                return None
    
    def clear_monitored_apps(self):
        """清空所有监听的应用"""
        with self._config_lock:
            try:
                if 'app_monitor' in self.config_data:
                    self.config_data['app_monitor']['apps'] = []
                    self.save()
                    logging.info("已清空所有监听应用")
                    return True
                return False
            except Exception as e:
                logging.error(f"清空监听应用失败: {str(e)}")
                return False
    
    def save(self):
        """线程安全的保存方法"""
        with self._config_lock:
            try:
                if not os.path.exists(CONFIG_DIR):
                    os.makedirs(CONFIG_DIR)
                    logging.info(f"创建配置目录: {CONFIG_DIR}")
                
                # 保存前的数据验证和日志
                if 'app_monitor' in self.config_data:
                    apps = self.config_data['app_monitor']['apps']
                    logging.info(f"准备保存应用监控配置，共 {len(apps)} 个应用")
                    for app in apps:
                        old_values = {
                            'minimize_to_tray': app.get('minimize_to_tray'),
                            'check_interval': app.get('check_interval'),
                            'restart_interval': app.get('restart_interval')
                        }
                        
                        # 强制转换数据类型
                        app['minimize_to_tray'] = bool(app.get('minimize_to_tray', False))
                        app['check_interval'] = max(1, int(app.get('check_interval', 1)))
                        app['restart_interval'] = max(0, int(app.get('restart_interval', 60)))
                        
                        # 记录值的变化
                        changes = []
                        if old_values['minimize_to_tray'] != app['minimize_to_tray']:
                            changes.append(f"minimize_to_tray: {old_values['minimize_to_tray']} -> {app['minimize_to_tray']}")
                        if old_values['check_interval'] != app['check_interval']:
                            changes.append(f"check_interval: {old_values['check_interval']} -> {app['check_interval']}")
                        if old_values['restart_interval'] != app['restart_interval']:
                            changes.append(f"restart_interval: {old_values['restart_interval']} -> {app['restart_interval']}")
                        
                        if changes:
                            logging.info(f"应用 {app['name']} 配置更新: {', '.join(changes)}")
                
                # 写入前记录配置内容
                logging.info("准备写入配置文件...")
                logging.debug(f"配置内容: {self.config_data}")
                
                # 写入文件
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self.config_data, f, indent=4, ensure_ascii=False)
                
                # 验证写入结果
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    if saved_config == self.config_data:
                        logging.info("配置文件写入并验证成功")
                    else:
                        logging.error("配置文件验证失败，写入的内容与原始内容不匹配")
                        return False
                
                return True
                
            except Exception as e:
                logging.error(f"保存配置失败: {str(e)}", exc_info=True)
                return False
    
    def set_auto_start(self, enabled):
        """设置自启动状态"""
        try:
            self.config_data['auto_start'] = enabled
            if not save_config(self.config_data):
                logging.error("保存自启动配置失败")
                return False
            return True
        except Exception as e:
            logging.error(f"设置自启动状态失败: {str(e)}")
            return False
    
    def get_auto_start(self):
        """获取自启动状态"""
        try:
            return self.config_data.get('auto_start', False)
        except Exception as e:
            logging.error(f"获取自启动状态失败: {str(e)}")
            return False

def load_config():
    """加载配置文件"""
    try:
        
        if not os.path.exists(CONFIG_DIR):
            logging.info(f"配置目录不存在，创建目录: {CONFIG_DIR}")
            os.makedirs(CONFIG_DIR)
        
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config
            except json.JSONDecodeError as e:
                logging.error(f"配置文件格式错误: {str(e)}")
                return DEFAULT_CONFIG.copy()
            except Exception as e:
                logging.error(f"读取配置文件失败: {str(e)}")
                return DEFAULT_CONFIG.copy()
        else:
            logging.info(f"配置文件不存在，使用默认配置: {DEFAULT_CONFIG}")
            # 创建默认配置文件
            try:
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)
            except Exception as e:
                logging.error(f"创建默认配置文件失败: {str(e)}")
            return DEFAULT_CONFIG.copy()
    except Exception as e:
        logging.error(f"加载配置过程中发生错误: {str(e)}", exc_info=True)
        return DEFAULT_CONFIG.copy()

def save_config(config):
    """保存配置文件"""
    try:
        if not os.path.exists(CONFIG_DIR):
            try:
                os.makedirs(CONFIG_DIR)
                logging.info(f"创建配置目录: {CONFIG_DIR}")
            except Exception as e:
                logging.error(f"创建配置目录失败: {str(e)}")
                return

        logging.info(f"要保存的配置内容: {config}")
        
        try:
            # 确保配置不为空
            if not config:
                logging.error("配置内容为空，使用默认配置")
                config = DEFAULT_CONFIG.copy()
            
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
                logging.info("配置文件写入成功")
            
            # 立即验证写入的内容
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    logging.info(f"验证保存的配置: {saved_config}")
                    if not saved_config:
                        logging.error("保存的配置为空")
            else:
                logging.error("配置文件未成功创建")
                
        except Exception as e:
            logging.error(f"写入配置文件失败: {str(e)}")
            
    except Exception as e:
        logging.error(f"保存配置过程中发生错误: {str(e)}", exc_info=True)
  