import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional, Any, Tuple

from zhkj_plugins.wrap import singleton


# -------------------------- 通用异步任务管理器（支持嵌套进度和参数传递） --------------------------
@dataclass
class TaskInfo:
    """任务信息数据类（结构化存储任务状态）"""
    task_id: str
    progress: int = 0  # 0-100
    status: str = "pending"  # pending/running/finished/failed/timeout
    step: str = ""  # 当前步骤描述
    result: Optional[Any] = None  # 任务结果
    error: Optional[str] = None  # 错误信息
    create_time: float = field(default_factory=time.time)
    update_time: float = field(default_factory=time.time)


class NestedProgressCallback:
    """嵌套进度回调类"""

    def __init__(self, parent_callback: Callable[[int, str], None],
                 start_percent: int, end_percent: int, parent_step: str = ""):
        """
        :param parent_callback: 父进度回调函数
        :param start_percent: 子进度开始的百分比
        :param end_percent: 子进度结束的百分比
        :param parent_step: 父步骤描述
        """
        self.parent_callback = parent_callback
        self.start_percent = start_percent
        self.end_percent = end_percent
        self.parent_step = parent_step
        self.range_size = end_percent - start_percent

    def __call__(self, progress: int, step: str = ""):
        """更新嵌套进度"""
        progress = max(0, min(100, progress))  # 确保进度在0-100之间

        # 计算在总进度中的位置
        total_progress = self.start_percent + int(self.range_size * progress / 100)

        # 构建完整的步骤描述
        full_step = self.parent_step
        if step:
            if full_step:
                full_step += f" > {step}"
            else:
                full_step = step

        # 调用父回调
        self.parent_callback(total_progress, full_step)

    def create_sub_callback(self, sub_start: int, sub_end: int, sub_step: str = ""):
        """创建子进度回调（支持多级嵌套）"""
        # 计算在父进度范围内的起始和结束位置
        absolute_start = self.start_percent + int(self.range_size * sub_start / 100)
        absolute_end = self.start_percent + int(self.range_size * sub_end / 100)

        # 构建步骤描述
        full_step = self.parent_step
        if sub_step:
            if full_step:
                full_step += f" > {sub_step}"
            else:
                full_step = sub_step

        return NestedProgressCallback(
            self.parent_callback, absolute_start, absolute_end, full_step
        )


@singleton
class AsyncTaskManager:
    """通用异步任务进度管理器（支持嵌套进度和参数传递）"""

    def __init__(self, timeout: int = 3600):
        self.timeout = timeout  # 任务超时时间（秒）
        self.tasks: Dict[str, TaskInfo] = {}  # 任务存储（task_id -> TaskInfo）
        self.lock = threading.Lock()  # 线程安全锁

    def create_task(self, task_func: Callable, *args, **kwargs) -> str:
        """
        创建并启动异步任务

        :param task_func: 任务执行函数
                        第一个参数必须是 progress_callback 函数
                        其余参数通过 *args 和 **kwargs 传递
        :param args: 传递给任务函数的位置参数
        :param kwargs: 传递给任务函数的关键字参数
        :return: task_id
        """
        task_id = str(uuid.uuid4())

        # 初始化任务信息
        with self.lock:
            self.tasks[task_id] = TaskInfo(
                task_id=task_id,
                step="初始化任务..."
            )

        # 定义进度回调函数
        def progress_callback(progress: int, step: str = ""):
            """进度回调：外部任务通过此函数更新进度"""
            progress = max(0, min(100, progress))
            with self.lock:
                if task_id in self.tasks and self.tasks[task_id].status == "running":
                    self.tasks[task_id].progress = progress
                    self.tasks[task_id].step = step
                    self.tasks[task_id].update_time = time.time()

        # 异步执行任务
        def _run_task():
            try:
                # 标记任务为运行中
                with self.lock:
                    if task_id in self.tasks:
                        self.tasks[task_id].status = "running"
                        self.tasks[task_id].update_time = time.time()

                # 执行任务（传入进度回调和所有其他参数）
                result = task_func(*args, progress_callback=progress_callback, **kwargs)

                # 任务成功完成
                with self.lock:
                    if task_id in self.tasks:
                        self.tasks[task_id].status = "finished"
                        self.tasks[task_id].result = result
                        self.tasks[task_id].step = "任务完成"
                        self.tasks[task_id].progress = 100
                        self.tasks[task_id].update_time = time.time()

            except Exception as e:
                # 任务失败
                error_msg = str(e)
                with self.lock:
                    if task_id in self.tasks:
                        self.tasks[task_id].status = "failed"
                        self.tasks[task_id].error = error_msg
                        self.tasks[task_id].step = f"执行失败: {error_msg[:50]}..."
                        self.tasks[task_id].update_time = time.time()

            finally:
                # 清理超时任务
                self._clean_timeout_tasks()

        # 启动线程执行任务
        threading.Thread(target=_run_task, daemon=True).start()
        return task_id

    def create_nested_callback(self, parent_callback: Callable[[int, str], None],
                               start_percent: int, end_percent: int, parent_step: str = "") -> NestedProgressCallback:
        """
        创建嵌套进度回调
        :param parent_callback: 父进度回调
        :param start_percent: 子进度开始百分比
        :param end_percent: 子进度结束百分比
        :param parent_step: 父步骤描述
        :return: 嵌套进度回调对象
        """
        return NestedProgressCallback(parent_callback, start_percent, end_percent, parent_step)

    def get_task_progress(self, task_id: str) -> Optional[TaskInfo]:
        """查询任务进度"""
        with self.lock:
            # 先清理超时任务
            self._clean_timeout_tasks()
            # 返回任务信息
            task = self.tasks.get(task_id)
            return task

    def _clean_timeout_tasks(self):
        """清理超时任务"""
        now = time.time()
        timeout_tasks = [
            task_id for task_id, task in self.tasks.items()
            if now - task.create_time > self.timeout
               and task.status not in ("running", "finished")
        ]
        for task_id in timeout_tasks:
            self.tasks[task_id].status = "timeout"
            self.tasks[task_id].step = "任务超时"
            self.tasks[task_id].update_time = now


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
