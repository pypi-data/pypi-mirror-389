# redis-fair-semaphore

基于Redis的信号量。

## Install

```shell
pip install redis-fair-semaphore
```

## 使用方法

```python
import redis
from redis_fair_semaphore import acquire_fair_semaphore
from redis_fair_semaphore import release_fair_semaphore

conn = redis.from_url("redis://redis/0")


def test():
    sem_id = acquire_fair_semaphore(conn, "test_sem_name", 10)
    try:
        if sem_id:
            print("Acquired...")
        else:
            print("NOT acquired...")
    finally:
        release_fair_semaphore(conn, "test_sem_name", sem_id)


if __name__ == "__main__":
    test()
```

## 版本记录

### v0.1.0

- 版本首发。

### v0.1.1

- Doc update.
