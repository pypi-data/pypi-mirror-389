from typing import Callable, Optional

from . import PluginManager
from .plugin_manager.models import VersionInfo, PluginConfig
from .task_progress_manager import AsyncTaskManager


def progress_bar_callback(downloaded: int, total: int, speed: float) -> None:
    """显示文本进度条和百分比"""
    if total == 0:
        # 无法获取总大小，只显示已下载字节数
        print(f"\r已下载：{downloaded / 1024:.2f} KB | 速度：{speed:.2f} KB/s", end="")
        return

    # 计算百分比
    percent = (downloaded / total) * 100
    # 进度条长度（20个字符）
    bar_length = 20
    filled_length = int(bar_length * percent // 100)
    bar = "=" * filled_length + " " * (bar_length - filled_length)

    # 格式化显示（总大小转为 MB/KB）
    total_size = total / (1024 * 1024) if total >= 1024 * 1024 else total / 1024
    total_unit = "MB" if total >= 1024 * 1024 else "KB"
    downloaded_size = downloaded / (1024 * 1024) if total >= 1024 * 1024 else downloaded / 1024

    # 显示格式：[=====     ] 50%  1.2/2.4 MB  100.5 KB/s
    print(
        f"\r[{bar}] {percent:.1f}%  "
        f"{downloaded_size:.2f}/{total_size:.2f} {total_unit}  "
        f"速度：{speed:.2f} KB/s",
        end=""
    )


class PluginBase:
    def __init__(self, plugin_name: str, plugin_manager: PluginManager):
        self.name = plugin_name
        self.plugin_manager = plugin_manager

    def install(self, progress_callback: Optional[Callable[[int, int, float], None]] = progress_bar_callback):
        return self.plugin_manager.install_plugin(self.name, progress_callback=progress_callback)

    def async_install(self) -> str:
        return AsyncTaskManager().create_task(self.install)

    def async_install_progress(self, task_id: str):
        return AsyncTaskManager().get_task_progress(task_id=task_id)

    def uninstall(self):
        return self.plugin_manager.uninstall_plugin(self.name)

    def start(self, wait_for_ready: bool = True, timeout: int = 30, success_indicator=None):
        return self.plugin_manager.start_plugin(self.name, wait_for_ready, timeout, success_indicator=success_indicator)

    def stop(self):
        return self.plugin_manager.stop_plugin(self.name)

    def is_running(self):
        return self.plugin_manager.is_plugin_running(self.name)

    def is_installed(self):
        return self.plugin_manager.is_plugin_installed(self.name)

    def info(self):
        return self.plugin_manager.plugin_info(self.name)

    def version(self):
        info = self.info()
        if not info:
            return None
        return info.current_version

    def check_update(self):
        return self.plugin_manager.check_plugin_update(self.name)

    def package(self, plugin_dir: str, plugin_config: PluginConfig = None):
        return self.plugin_manager.package_plugin(self.name, plugin_dir, plugin_config)

    def update(self,
               version_info: VersionInfo,
               progress_callback: Optional[Callable[[int, int, float], None]] = None):
        return self.plugin_manager.update_plugin(self.name, version_info, progress_callback)

    def upgrade(self,
                progress_callback: Optional[Callable[[int, int, float], None]] = None):
        has_new_version, version_info = self.check_update()
        if not has_new_version:
            print("暂无可更新版本")
            return True

        return self.update(version_info, progress_callback=progress_callback)

    def list(self):
        return self.plugin_manager.list_plugins()
