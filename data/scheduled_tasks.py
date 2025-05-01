from datetime import datetime
import threading
from data.telegram_text import telegram
scheduled_tasks = {}


def schedule_task(task_id, task_name, execution_time, chat_id):
    global scheduled_tasks
    if task_id in scheduled_tasks:
        scheduled_tasks[task_id].cancel()
    delay = (execution_time - datetime.now()).total_seconds()
    print(execution_time - datetime.now(), delay)
    if delay < 0:
        print("Указанное время уже прошло!")
        return
    task = threading.Timer(delay, telegram, args=(chat_id, f'Дедлайн задачи "{task_name} закончился!"'))
    task.start()
    scheduled_tasks[task_id] = task
    print(f"Задача {task_id} запланирована на {execution_time}")


def cancel_task(task_id):
    global scheduled_tasks
    if task_id in scheduled_tasks:
        scheduled_tasks[task_id].cancel()
        del scheduled_tasks[task_id]
        print(f"Задача {task_id} отменена")
    else:
        print(f"Задача {task_id} не найдена")
