import asyncio
import redis
import json
from utils.utils import flat_list

class Redis:
  def __init__(self):
    self.r = redis.StrictRedis(host='localhost', port=6379, db=0)\

  async def set_dict(self, key, value):
    self.r.set(key, json.dumps(value))

  async def set_many(self, data):
    tasks = [self.set_dict(key, value) for key, value in data.items()]
    return await asyncio.gather(*tasks)

  def keys(self, pattern='*'):
    return [key.decode() for key in self.r.keys(pattern)]
  
  async def get_dict(self, key) -> dict:
    dict = self.r.get(key)
    return json.loads(dict) if dict else None

  def exists(self, key):
    return self.r.exists(key)
  
  async def get_all_by_pattern(self, pattern='*'):
    tasks = [self.get_dict(key) for key in self.keys(pattern)]
    return asyncio.gather(*tasks)
  
  async def append_to_list(self, key, value):
    self.r.rpush(key, value)

  async def get_list_by_pattern(self, key):
    keys = self.keys(f'*{key}*')
    tasks = [self.get_list(key) for key in keys]
    return flat_list(await asyncio.gather(*tasks))

  async def get_list(self, key):
    return [value.decode() for value in self.r.lrange(key, 0, -1)]

  def flush(self):
    self.r.flushall()