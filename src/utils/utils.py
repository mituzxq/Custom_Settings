import logging
import os
from datetime import datetime
import sys

def setup_logging():
    """设置日志配置"""
    # 创建日志目录
    log_dir = os.path.join(os.path.expanduser('~'), '.custom_settings_byMY', 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 生成日志文件名（按日期）
    log_file = os.path.join(log_dir, f'app_{datetime.now().strftime("%Y%m%d")}.log')
    
    # 配置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),  # 文件处理器
            logging.StreamHandler()  # 控制台处理器
        ]
    )

def global_exception_handler(exc_type, exc_value, exc_traceback):
    """全局异常处理器"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logging.error("未捕获的异常:", exc_info=(exc_type, exc_value, exc_traceback))

def safe_destroy(window):
    """安全地销毁窗口"""
    try:
        window.destroy()
    except:
        pass 

def cleanup_old_logs(config):
    """清理旧日志文件"""
    try:
        log_dir = os.path.join(os.path.expanduser('~'), '.custom_settings_byMY', 'logs')
        if not os.path.exists(log_dir):
            return

        retention_days = config.get_log_retention_days()
        current_time = datetime.now()
        deleted_count = 0
        
        logging.info(f"开始清理日志文件，保留天数: {retention_days} 天")
        
        for file in os.listdir(log_dir):
            if not file.endswith('.log'):
                continue
                
            file_path = os.path.join(log_dir, file)
            file_time = datetime.fromtimestamp(os.path.getctime(file_path))
            days_old = (current_time - file_time).days
            
            if days_old > retention_days:
                try:
                    os.remove(file_path)
                    deleted_count += 1
                    logging.info(f"已删除过期日志文件: {file} (已存在 {days_old} 天)")
                except Exception as e:
                    logging.error(f"删除日志文件失败: {file}, {str(e)}")
        
        if deleted_count > 0:
            logging.info(f"共清理 {deleted_count} 个过期日志文件")
        else:
            logging.info("没有需要清理的日志文件")
                    
    except Exception as e:
        logging.error(f"清理日志文件失败: {str(e)}") 