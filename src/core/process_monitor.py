import psutil
import time
import logging
import subprocess
import os
from ..utils.config import Config
import threading

class ProcessMonitor:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            with self._lock:
                if not hasattr(self, '_initialized'):
                    self.monitored_processes = {}
                    self.running = False
                    self.monitor_thread = None
                    self._initialized = True
                    logging.info("进程监控器已初始化")

    def start_monitoring(self, app_config):
        """启动一个新的监控进程"""
        try:
            if not os.path.exists(app_config['path']):
                logging.error(f"进程路径不存在: {app_config['path']}")
                return False

            process_name = app_config['name']
            
            # 检查是否已经在监控此进程
            if process_name in self.monitored_processes:
                logging.info(f"进程 {process_name} 已在监控中")
                return True

            # 检查进程是否已经在运行
            if self.is_process_running(process_name):
                return self.add_to_monitoring(app_config)

            self.monitored_processes[process_name] = {
                'path': app_config['path'],
                'check_interval': app_config['check_interval'],
                'restart_interval': app_config['restart_interval'],
                'minimize_to_tray': app_config['minimize_to_tray'],
                'last_check': 0,  # 初始化最后检查时间
                'last_restart': 0  # 初始化最后重启时间
            }
            
            # 启动进程
            self.start_process(app_config['path'], app_config['minimize_to_tray'])
            
            # 如果监控线程未运行，启动它
            if not self.running:
                self.start_monitor_thread()
            
            return True
            
        except Exception as e:
            logging.error(f"启动监控失败: {str(e)}")
            return False

    def start_monitor_thread(self):
        """启动监控线程"""
        if not self.running:
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()

    def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                self.monitor()
                time.sleep(0.1)  # 短暂休眠以避免CPU使用率过高
            except Exception as e:
                logging.error(f"监控循环出错: {str(e)}")
                time.sleep(1)  # 出错时等待较长时间

    def stop_monitoring(self, process_name):
        """停止监控特定进程"""
        if process_name in self.monitored_processes:
            logging.info(f"停止监控进程: {process_name}")
            self.monitored_processes.pop(process_name)

    def stop_all(self, clear_config=True):
        """停止所有监控"""
        try:
            self.running = False
            
            # 停止所有被监控的进程
            for process_name in list(self.monitored_processes.keys()):
                self.stop_monitoring(process_name)
            
            if clear_config:
                self.monitored_processes.clear()
            
        except Exception as e:
            logging.error(f"停止监控失败: {str(e)}")

    def is_process_running(self, process_name):
        """检查进程是否正在运行"""
        try:
            for proc in psutil.process_iter(['name']):
                if proc.info['name'].lower() == process_name.lower():
                    return True
            return False
        except Exception as e:
            logging.error(f"检查进程状态失败: {str(e)}")
            return False

    def start_process(self, process_path, minimize_to_tray=False):
        """启动指定的进程"""
        try:
            # 检查进程是否已经在运行
            process_name = os.path.basename(process_path)
            if self.is_process_running(process_name):
                logging.info(f"进程 {process_name} 已在运行，跳过启动")
                return True

            # 根据launch_mode决定启动方式
            if minimize_to_tray:  # 托盘启动
                # 以托盘方式启动（全隐藏窗口）
                si = subprocess.STARTUPINFO()
                si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                si.wShowWindow = subprocess.SW_HIDE  # 使用 SW_HIDE (0) 来隐藏窗口
                process = subprocess.Popen(
                    [process_path],  # 使用列表形式传递命令
                    startupinfo=si,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:  # 正常启动
                # 正常启动进程
                process = subprocess.Popen([process_path])

            if process_name in self.monitored_processes:
                self.monitored_processes[process_name]['last_restart'] = time.time()
            logging.info(f"成功启动进程: {process_name} {'(托盘启动)' if minimize_to_tray else '(正常启动)'}")
            return True
        except Exception as e:
            logging.error(f"启动进程失败: {str(e)}")
            return False

    def monitor(self):
        """监控所有注册的进程"""
        try:
            current_time = time.time()
            
            # 遍历所有注册的进程
            for process_name, info in list(self.monitored_processes.items()):
                try:
                    # 检查是否需要检查进程状态（按照监听间隔）
                    if current_time - info.get('last_check', 0) < info.get('check_interval', 1):
                        continue
                    
                    # 更新最后检查时间
                    info['last_check'] = current_time
                    
                    # 检查进程是否在运行
                    process_running = False
                    for proc in psutil.process_iter(['name']):
                        if proc.info['name'].lower() == process_name.lower():
                            process_running = True
                            break
                    
                    if not process_running:
                        logging.info(f"检测到进程未运行: {process_name}，准备重新启动")
                        # 如果进程未运行，立即启动
                        minimize_to_tray = info['minimize_to_tray']
                        self.start_process(info['path'], minimize_to_tray)
                        info['last_restart'] = current_time
                        
                    logging.debug(f"监控进程 {process_name}: 运行状态={process_running}, "
                                f"上次检查={info['last_check']}, "
                                f"检查间隔={info['check_interval']}")
                    
                except Exception as e:
                    logging.error(f"监控进程 {process_name} 时出错: {str(e)}")
                
        except Exception as e:
            logging.error(f"监控过程出错: {str(e)}")

    def reload_config(self):
        """重新加载配置"""
        try:
            # 获取新的配置
            config = Config()
            apps = config.get_monitored_apps()
            
            if config.get_app_monitor_enabled():
                # 停止所有当前监控
                self.stop_all(clear_config=False)
                self.monitored_processes.clear()
                
                # 重新启动监控
                for app in apps:
                    if app.get('appenabled', False):
                        self.start_monitoring(app)
                        logging.info(f"重新启动监控: {app['name']}")
            else:
                self.stop_all(clear_config=True)
                
        except Exception as e:
            logging.error(f"重新加载配置失败: {str(e)}")

    def add_to_monitoring(self, app_config):
        """将已运行的进程添加到监控列表"""
        try:
            process_name = app_config['name']
            
            # 检查是否已经在监控此进程
            if process_name in self.monitored_processes:
                logging.info(f"进程 {process_name} 已在监控中")
                return True

            # 添加到监控列表但不启动进程
            self.monitored_processes[process_name] = {
                'path': app_config['path'],
                'check_interval': app_config['check_interval'],
                'restart_interval': app_config['restart_interval'],
                'last_check': 0,
                'last_restart': time.time(),
                'minimize_to_tray': app_config['minimize_to_tray']
            }
            
            # 如果监控线程未运行，启动它
            if not self.running:
                self.start_monitor_thread()
            
            return True
            
        except Exception as e:
            logging.error(f"添加进程到监控失败: {str(e)}")
            return False