import PyInstaller.__main__
import os
import shutil

def build_exe():
    """打包程序为exe"""
    try:
        # 清理旧的打包文件
        if os.path.exists('build'):
            shutil.rmtree('build')
        if os.path.exists('dist'):
            shutil.rmtree('dist')
            
        # 获取资源文件路径
        assets_dir = os.path.join('src', 'assets')
        icon_path = os.path.join('src', 'assets', 'icon.png')
        
        # PyInstaller参数
        params = [
            'main.py',  # 主程序入口
            '--name=CustomSettings',  # 程序名称
            '--noconsole',  # 不显示控制台
            '--noconfirm',  # 覆盖已存在的文件
            '--clean',  # 清理临时文件
            f'--add-data={assets_dir}{os.pathsep}src/assets',  # 添加资源文件
            '--hidden-import=PIL._tkinter_finder',  # 添加隐藏导入
            '--hidden-import=pystray._win32',
            '--hidden-import=keyboard',
            '--hidden-import=PIL',
            '--hidden-import=win32gui',
            '--hidden-import=win32con',
            '--hidden-import=win32api',
            '--collect-all=pystray',
            '--onefile',  # 打包成单个文件
            '--version-file=version.txt',
            f'--icon={icon_path}',  # 使用正确的图标路径
        ]
        
        # 执行打包
        PyInstaller.__main__.run(params)
        
        print("打包完成！")
        print(f"可执行文件位置: {os.path.join('dist', 'CustomSettings.exe')}")
        
    except Exception as e:
        print(f"打包失败: {str(e)}")

if __name__ == '__main__':
    build_exe() 