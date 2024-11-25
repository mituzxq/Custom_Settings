import os
import sys
import winreg
import logging

def get_startup_path():
    """获取程序路径"""
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后的路径
        return sys.executable
    else:
        # 开发环境下的路径
        return os.path.abspath(sys.argv[0])

def set_auto_start(enabled):
    """设置开机自启动"""
    try:
        app_path = get_startup_path()
        app_name = "CustomSettingsByMY"
        
        try:
            # 打开注册表项
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_ALL_ACCESS
            )
        except Exception as e:
            logging.error(f"打开注册表失败: {str(e)}")
            return False
            
        try:
            if enabled:
                # 添加自启动
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{app_path}"')
                logging.info(f"已添加自启动注册表项: {app_path}")
            else:
                # 删除自启动
                try:
                    winreg.DeleteValue(key, app_name)
                    logging.info("已删除自启动注册表项")
                except WindowsError:
                    # 如果项不存在，忽略错误
                    pass
        except Exception as e:
            logging.error(f"修改注册表失败: {str(e)}")
            return False
        finally:
            try:
                winreg.CloseKey(key)
            except:
                pass
                
        return True
        
    except Exception as e:
        logging.error(f"设置自启动失败: {str(e)}")
        return False

def check_auto_start():
    """检查是否已设置自启动"""
    key = None
    try:
        app_name = "CustomSettingsByMY"
        
        try:
            # 打开注册表项
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ
            )
        except Exception as e:
            logging.error(f"打开注册表失败: {str(e)}")
            return False
            
        try:
            value, _ = winreg.QueryValueEx(key, app_name)
            return True
        except WindowsError:
            return False
        except Exception as e:
            logging.error(f"读取注册表值失败: {str(e)}")
            return False
            
    except Exception as e:
        logging.error(f"检查自启动状态失败: {str(e)}")
        return False
    finally:
        if key:
            try:
                winreg.CloseKey(key)
            except:
                pass 