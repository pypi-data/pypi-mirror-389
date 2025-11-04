import os
import redis
from rq import Worker, Queue
from datetime import datetime
import os
import redis
from rq import Worker, Queue
from datetime import datetime

import multiprocessing
# 检查是否在macOS上
if os.name == 'posix' and 'darwin' in os.sys.platform:
    # 尝试设置 'spawn' 启动方式
    multiprocessing.set_start_method('spawn', force=True)


from digital_life.redis_ import get_redis_client
conn = get_redis_client(username = os.getenv("redis_username"), 
                        password = os.getenv("redis_password"), 
                        host = os.getenv("redis_host"), 
                        port = os.getenv("redis_port"),
                        db = 22,
                        decode_responses = False)


if __name__ == '__main__':
    # 打印 Worker 启动信息
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting RQ Worker...")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Connected to Redis: {os.getenv("redis_host")}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Listening on queue: 'default'")
    
    worker = Worker(queues=[Queue('default', connection=conn)], connection=conn)
    worker.work()

