import redis
import json

redis_client = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)

def set_to_redis_hash(key, field, value):
    redis_client.hset(key, field, json.dumps(value))

def get_from_redis_hash(key, field):
    value = redis_client.hget(key, field)
    return json.loads(value) if value else None

def get_all_from_redis_hash(hash_name):
    data = redis_client.hgetall(hash_name)
    return {key.decode(): value.decode() for key, value in data.items()}

def remove_from_redis_hash(hash_name, key):
    redis_client.hdel(hash_name, key)