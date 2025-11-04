import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional, Any, Tuple

from zhkj_plugins.wrap import singleton

logger = logging.getLogger(__name__)

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional, Any, List
from zhkj_plugins.wrap import singleton


@dataclass
class TaskInfo:
    task_id: str
    progress: int = 0  # 0-100
    status: str = "pending"  # pending/running/finished/failed/timeout
    step: str = ""  # 当前步骤描述
    result: Optional[Any] = None  # 任务结果
    error: Optional[str] = None  # 错误信息
    create_time: float = field(default_factory=time.time)
    update_time: float = field(default_factory=time.time)


@singleton
class AsyncTaskManager:
    def __init__(self, timeout: int = 3600):
        self.timeout = timeout  # 任务默认超时时间（秒）
        self.tasks: Dict[str, TaskInfo] = {}  # 任务存储：task_id -> TaskInfo
        self.lock = threading.Lock()  # 线程安全锁

    # -------------------------- 原有方法（不变） --------------------------
    def create_task(self, task_func: Callable, *args, **kwargs) -> str:
        task_id = str(uuid.uuid4())
        with self.lock:
            self.tasks[task_id] = TaskInfo(task_id=task_id, step="初始化任务...")

        def progress_callback(progress: int, step: str = ""):
            progress = max(0, min(100, progress))
            with self.lock:
                if task_id in self.tasks and self.tasks[task_id].status == "running":
                    self.tasks[task_id].progress = progress
                    self.tasks[task_id].step = step
                    self.tasks[task_id].update_time = time.time()

        def _run_task():
            try:
                with self.lock:
                    if task_id in self.tasks:
                        self.tasks[task_id].status = "running"
                        self.tasks[task_id].update_time = time.time()
                result = task_func(*args, progress_callback=progress_callback, **kwargs)
                with self.lock:
                    if task_id in self.tasks:
                        self.tasks[task_id].status = "finished"
                        self.tasks[task_id].result = result
                        self.tasks[task_id].step = "任务完成"
                        self.tasks[task_id].progress = 100
                        self.tasks[task_id].update_time = time.time()
            except Exception as e:
                error_msg = str(e)
                with self.lock:
                    if task_id in self.tasks:
                        self.tasks[task_id].status = "failed"
                        self.tasks[task_id].error = error_msg
                        self.tasks[task_id].step = f"执行失败: {error_msg[:50]}..."
                        self.tasks[task_id].update_time = time.time()
            finally:
                self._clean_timeout_tasks()

        threading.Thread(target=_run_task, daemon=True).start()
        return task_id

    def get_task_progress(self, task_id: str) -> Optional[TaskInfo]:
        with self.lock:
            self._clean_timeout_tasks()
            return self.tasks.get(task_id)

    def _clean_timeout_tasks(self):
        now = time.time()
        timeout_tasks = [
            tid for tid, task in self.tasks.items()
            if now - task.create_time > self.timeout and task.status not in ("running", "finished")
        ]
        for tid in timeout_tasks:
            self.tasks[tid].status = "timeout"
            self.tasks[tid].step = "任务超时"
            self.tasks[tid].update_time = now

    def wait_for_done(self, task_id: str, check_interval: float = 0.5, wait_timeout: Optional[float] = None,
                      show_progress: bool = True) -> TaskInfo:
        task_info = self.get_task_progress(task_id)
        if not task_info:
            raise ValueError(f"任务ID不存在：{task_id}")

        start_time = time.time()
        print(f"开始等待任务完成（任务ID：{task_id}），检查间隔：{check_interval}秒")

        while True:
            task_info = self.get_task_progress(task_id)
            if not task_info:
                raise ValueError(f"任务ID {task_id} 已被清理，无法继续等待")

            if show_progress:
                print(f"\r[任务 {task_id[:8]}] {task_info.progress}% | {task_info.status} | {task_info.step}",
                      end="", flush=True)

            if task_info.status in ("finished", "failed", "timeout"):
                if show_progress:
                    print(f"\n任务结束 | 最终状态：{task_info.status} | 耗时：{time.time() - start_time:.1f}秒")
                return task_info

            if wait_timeout is not None and (time.time() - start_time) > wait_timeout:
                raise TimeoutError(
                    f"等待任务 {task_id} 超时（超时时间：{wait_timeout}秒），"
                    f"当前状态：{task_info.status} | 进度：{task_info.progress}%"
                )

            time.sleep(check_interval)

    # -------------------------- 新增：清理方法 --------------------------
    def clean_finished_tasks(self, keep_time: float = 300) -> int:
        """
        清理“已完成/失败/超时”的任务（默认保留5分钟内的任务，避免刚结束就被清理）
        Args:
            keep_time: 保留时间（秒），超过该时间的已结束任务才会被清理
        Returns:
            int: 实际清理的任务数量
        """
        with self.lock:  # 线程安全：加锁避免并发修改
            now = time.time()
            # 筛选需要清理的任务：状态是结束态 + 超过保留时间
            tasks_to_clean = [
                task_id for task_id, task in self.tasks.items()
                if task.status in ("finished", "failed", "timeout")  # 仅清理已结束的任务
                   and (now - task.update_time) > keep_time  # 超过保留时间
            ]

            # 执行清理
            for task_id in tasks_to_clean:
                task = self.tasks[task_id]
                logger.info(f"清理已结束任务：{task_id}（状态：{self.tasks[task_id].status}，结束时间：{task.update_time}）")
                del self.tasks[task_id]

            # 记录清理结果
            cleaned_count = len(tasks_to_clean)
            logger.info(
                f"已完成任务清理完成 | 总结束任务数：{len([t for t in self.tasks.values() if t.status in ('finished', 'failed', 'timeout')])} | 清理数量：{cleaned_count}")
            return cleaned_count

    def clean_specific_task(self, task_id: str, force: bool = False) -> bool:
        """
        指定任务ID清理（默认不允许清理“运行中”的任务，避免数据混乱）
        Args:
            task_id: 要清理的任务ID
            force: 是否强制清理（True：即使任务正在运行也清理；False：仅清理非运行中任务）
        Returns:
            bool: 清理结果（True：清理成功；False：任务不存在或不允许清理）
        """
        with self.lock:  # 线程安全：加锁确保任务状态不被并发修改
            # 1. 检查任务是否存在
            if task_id not in self.tasks:
                logger.warning(f"指定清理的任务不存在：{task_id}，清理失败")
                return False

            # 2. 检查任务状态，判断是否允许清理
            task_info = self.tasks[task_id]
            if not force and task_info.status == "running":
                logger.error(f"任务 {task_id} 正在运行中，不允许非强制清理（如需清理请设置 force=True）")
                return False

            # 3. 执行清理
            del self.tasks[task_id]
            logger.info(f"指定任务清理成功 | 任务ID：{task_id} | 清理时状态：{task_info.status} | 是否强制：{force}")
            return True


# -------------------------- 使用示例 --------------------------
def complex_task_with_params(progress_callback, data_source: str, model_name: str, epochs: int = 5, **kwargs):
    """
    带参数的复杂任务示例
    """
    progress_callback(0, f"开始处理数据源: {data_source}")

    # 使用传入的参数
    progress_callback(10, f"配置模型: {model_name}")
    time.sleep(1)

    # 数据加载阶段 (10-40%)
    data_callback = manager.create_nested_callback(progress_callback, 10, 40, "数据加载")

    data_callback(0, "连接数据源")
    time.sleep(0.5)

    # 模拟加载不同数据源
    if data_source == "database":
        data_callback(50, "执行SQL查询")
        time.sleep(1)
    elif data_source == "file":
        data_callback(50, "读取文件")
        time.sleep(0.8)
    else:
        data_callback(50, "获取数据")
        time.sleep(0.5)

    data_callback(100, "数据加载完成")

    # 训练阶段 (40-90%)
    training_callback = manager.create_nested_callback(progress_callback, 40, 90, f"训练模型 {model_name}")

    for epoch in range(epochs):
        epoch_callback = training_callback.create_sub_callback(
            epoch * 100 // epochs, (epoch + 1) * 100 // epochs, f"第{epoch + 1}轮"
        )

        for batch in range(10):
            epoch_callback(batch * 10, f"批次{batch + 1}")
            time.sleep(0.05)

        epoch_callback(100, f"第{epoch + 1}轮完成")

    training_callback(100, "训练完成")

    # 评估阶段 (90-100%)
    progress_callback(90, "评估模型")
    time.sleep(1)
    progress_callback(100, "任务完成")

    # 返回结果，包含传入的参数信息
    return {
        "data_source": data_source,
        "model_name": model_name,
        "epochs": epochs,
        "additional_params": kwargs,
        "accuracy": 0.95,
        "loss": 0.1
    }


def simple_processing_task(progress_callback, input_data: list, processing_option: str = "default"):
    """
    简单处理任务示例
    """
    total_items = len(input_data)

    for i, item in enumerate(input_data):
        progress = (i + 1) * 100 // total_items
        progress_callback(progress, f"处理 {processing_option}: {item}")
        time.sleep(0.2)

    return {
        "processed_items": total_items,
        "processing_option": processing_option,
        "result": f"成功处理了 {total_items} 个数据项"
    }


# 使用示例
if __name__ == "__main__":
    manager = AsyncTaskManager()

    # 示例1: 创建带参数的复杂任务
    print("=== 示例1: 复杂任务 ===")
    task_id1 = manager.create_task(
        complex_task_with_params,
        data_source="database",
        model_name="resnet50",
        epochs=3,
        batch_size=32,
        learning_rate=0.001
    )
    print(f"复杂任务已创建: {task_id1}")

    # 示例2: 创建简单处理任务
    print("\n=== 示例2: 简单任务 ===")
    task_id2 = manager.create_task(
        simple_processing_task,
        input_data=["item1", "item2", "item3", "item4", "item5"],
        processing_option="fast_mode"
    )
    print(f"简单任务已创建: {task_id2}")

    # 监控任务1进度
    print("\n监控复杂任务进度:")
    while True:
        task_info = manager.get_task_progress(task_id1)
        if not task_info:
            print("任务不存在")
            break

        print(f"进度: {task_info.progress}% | 状态: {task_info.status} | 步骤: {task_info.step}")

        if task_info.status in ("finished", "failed", "timeout"):
            if task_info.status == "finished":
                print(f"任务完成! 结果: {task_info.result}")
            else:
                print(f"任务失败: {task_info.error}")
            break

        time.sleep(0.5)
