"""基于Redis的信号量。

核心算法来自redis官网：
https://redis.io/ebook/part-2-core-concepts/chapter-6-application-components-in-redis/6-3-counting-semaphores/6-3-2-fair-semaphores/

"""

import uuid
import time


def acquire_fair_semaphore(conn, semaphore, limit, timeout=10):
    """获取一个信息量。

    @parameter: conn redis连接实例
    @parameter: semaphore 信号量名称
    @parameter: limit 信号量最大值
    @parameter: timeout 信号量锁定过期时间
    """
    identifier = str(uuid.uuid4())
    czset = semaphore + ":owner"
    ctr = semaphore + ":counter"
    now = time.time()
    pipeline = conn.pipeline(True)
    pipeline.zremrangebyscore(semaphore, "-inf", now - timeout)
    pipeline.zinterstore(czset, {czset: 1, semaphore: 0})
    pipeline.incr(ctr)
    counter = pipeline.execute()[-1]
    pipeline.zadd(semaphore, {identifier: now})
    pipeline.zadd(czset, {identifier: counter})
    pipeline.zrank(czset, identifier)
    if pipeline.execute()[-1] < limit:
        return identifier
    pipeline.zrem(semaphore, identifier)
    pipeline.zrem(czset, identifier)
    pipeline.execute()
    return None


def release_fair_semaphore(conn, semaphore, identifier):
    """释放一个信号量。"""
    if identifier is None:
        # 0表示实际不需要释放
        return 0
    pipeline = conn.pipeline(True)
    pipeline.zrem(semaphore, identifier)
    pipeline.zrem(semaphore + ":owner", identifier)
    return pipeline.execute()[0]
