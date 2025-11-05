import redis
import json
import time


def get_redis_client(username, password, host, port,db,decode_responses = True):
    """
    创建一个 Redis 客户端连接，包含阿里云 Redis 的认证信息。
    """
    try:
        r = redis.StrictRedis(
            host=host,
            port=port,                                          
            db=db,                        
            username=username,                                    
            password=password,                                
            decode_responses=decode_responses,                              
            socket_connect_timeout=10                           
        )
        # 尝试进行一次ping操作，验证连接是否成功
        r.ping()
        print("成功连接到阿里云 Redis！")
        return r
    except redis.exceptions.ConnectionError as e:
        print(f"无法连接到阿里云 Redis 服务器: {e}")
        return None
    except redis.exceptions.AuthenticationError as e:
        print(f"Redis 认证失败，请检查用户名和密码: {e}")
        return None
    except Exception as e:
        print(f"连接阿里云 Redis 时发生未知错误: {e}")
        return None


def store_with_expiration(r_client, key, value, expiration_seconds=7200):
    """
    将 key-value 对存储到 Redis，并设置过期时间。
    如果 value 是列表或字典等复杂类型，会先将其序列化为 JSON 字符串。

    Args:
        key (str): 要存储的键。
        value (any): 要存储的值。可以是字符串、数字、列表、字典等。
        expiration_seconds (int): 过期时间（秒）。默认值 7200 秒（2小时）。
    """
    try:
        r = r_client
        # 检查 value 的类型，如果是列表或字典，则序列化为 JSON 字符串
        if isinstance(value, (list, dict)):
            # json.dumps() 将 Python 对象序列化为 JSON 字符串
            # ensure_ascii=False 允许存储非 ASCII 字符（如中文）
            # separators=(',', ':') 紧凑输出，不添加空格
            serialized_value = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
        else:
            # 对于字符串、数字等简单类型，直接使用
            serialized_value = value

        # 使用 set 方法存储 key-value 对，并设置过期时间 (EX参数)
        r.set(key, serialized_value, ex=expiration_seconds)

    except redis.exceptions.ConnectionError as e:
        print(f"无法连接到 Redis 服务器: {e}")
    except Exception as e:
        print(f"发生了一个错误: {e}")

def get_value(r_client,key):
    """
    从 Redis 获取指定 key 的值。
    如果存储的是 JSON 字符串，会尝试反序列化为 Python 对象。

    Args:
        key (str): 要获取的键。

    Returns:
        any or None: 如果键存在，则返回其值（可能已反序列化）；否则返回 None。
    """
    try:
        r = r_client
        retrieved_data = r.get(key) # 获取到的会是字符串 (因为 decode_responses=True)

        if retrieved_data:
            try:
                # 尝试将获取到的字符串反序列化为 Python 对象
                # 如果存储的是普通字符串，json.loads 会抛出异常，此时捕获并返回原始字符串
                deserialized_data = json.loads(retrieved_data)
                return deserialized_data
            except json.JSONDecodeError:
                # 如果不是有效的 JSON 字符串，则返回原始字符串
                return retrieved_data
        else:
            return None
    except redis.exceptions.ConnectionError as e:
        print(f"无法连接到 Redis 服务器: {e}")
        return None
    except Exception as e:
        print(f"发生了一个错误: {e}")
        return None



class RedisDict:
    """
    一个模拟 Python 字典行为的类，底层使用 Redis 存储数据。
    所有存储的键值对都具有一个默认的过期时间。
    """

    def __init__(self, username,password,host='localhost', port=6379, db=0, default_ttl_seconds=2 * 60 * 60, prefix="redis_dict:"):
        """
        初始化 RedisDict 实例。

        Args:
            host (str): Redis 服务器地址。
            port (int): Redis 服务器端口。
            db (int): Redis 数据库索引。
            default_ttl_seconds (int): 默认的键值对过期时间（秒）。
            prefix (str): 所有存储在 Redis 中的键的前缀，用于隔离和管理。
        """
        self._redis = self.get_redis_client(username = username,
                                            password = password,
                                            host= host,
                                            port = port,
                                            db = db,
                                           )
        self._default_ttl_seconds = default_ttl_seconds
        self._prefix = prefix
        
        
    def get_redis_client(self,username, password, host, port,db):
        """
        创建一个 Redis 客户端连接，包含阿里云 Redis 的认证信息。
        """
        try:
            r = redis.StrictRedis(
                host=host,
                port=port,                                          
                db=db,                        
                username=username,                                    
                password=password,                                
                decode_responses=True,                              
                socket_connect_timeout=10                           
            )
            # 尝试进行一次ping操作，验证连接是否成功
            r.ping()
            print("成功连接到阿里云 Redis！")
            return r
        except redis.exceptions.ConnectionError as e:
            print(f"无法连接到阿里云 Redis 服务器: {e}")
            return None
        except redis.exceptions.AuthenticationError as e:
            print(f"Redis 认证失败，请检查用户名和密码: {e}")
            return None
        except Exception as e:
            print(f"连接阿里云 Redis 时发生未知错误: {e}")
            return None

        
    def _get_redis_key(self, key):
        """生成 Redis 中实际存储的键名（带前缀）。"""
        return f"{self._prefix}{key}"

    def __setitem__(self, key, value):
        """
        实现 dict[key] = value。
        存储数据到 Redis，并设置过期时间。复杂类型会被序列化为 JSON。
        """
        redis_key = self._get_redis_key(key)
        
        # 序列化值
        if isinstance(value, (list, dict)):
            serialized_value = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
        else:
            serialized_value = value
        
        try:
            self._redis.set(redis_key, serialized_value, ex=self._default_ttl_seconds)
            print(f"SET: '{key}' (Redis key: '{redis_key}') = '{value}' (serialized) with TTL {self._default_ttl_seconds}s")
        except Exception as e:
            print(f"Error setting key '{key}': {e}")
            raise # 重新抛出异常，保持字典行为

    def __getitem__(self, key):
        """
        实现 value = dict[key]。
        从 Redis 获取数据，并尝试反序列化 JSON。
        如果键不存在或已过期，则抛出 KeyError。
        """
        redis_key = self._get_redis_key(key)
        try:
            retrieved_data = self._redis.get(redis_key)
            if retrieved_data is None:
                raise KeyError(f"Key '{key}' not found or has expired.")
            
            # 尝试反序列化值
            try:
                deserialized_data = json.loads(retrieved_data)
                print(f"GET: '{key}' (Redis key: '{redis_key}') = '{retrieved_data}' (deserialized)")
                return deserialized_data
            except json.JSONDecodeError:
                print(f"GET: '{key}' (Redis key: '{redis_key}') = '{retrieved_data}' (raw string)")
                return retrieved_data # 不是 JSON 格式，返回原始字符串

        except redis.exceptions.ConnectionError as e:
            print(f"Error connecting to Redis: {e}")
            raise
        except Exception as e:
            # 如果是KeyError，则继续抛出，否则包装为KeyError
            if not isinstance(e, KeyError):
                print(f"Error getting key '{key}': {e}")
                raise KeyError(f"Error getting key '{key}': {e}") from e
            raise # Re-raise KeyError

    def __delitem__(self, key):
        """
        实现 del dict[key]。
        从 Redis 删除键。如果键不存在，则抛出 KeyError。
        """
        redis_key = self._get_redis_key(key)
        try:
            deleted_count = self._redis.delete(redis_key)
            if deleted_count == 0:
                raise KeyError(f"Key '{key}' not found (Redis key: '{redis_key}') to delete.")
            print(f"DEL: '{key}' (Redis key: '{redis_key}') deleted.")
        except redis.exceptions.ConnectionError as e:
            print(f"Error connecting to Redis: {e}")
            raise
        except Exception as e:
            if not isinstance(e, KeyError):
                print(f"Error deleting key '{key}': {e}")
                raise KeyError(f"Error deleting key '{key}': {e}") from e
            raise # Re-raise KeyError

    def __contains__(self, key):
        """
        实现 key in dict。
        检查键是否存在于 Redis 中。
        """
        redis_key = self._get_redis_key(key)
        try:
            exists = self._redis.exists(redis_key)
            print(f"CONTAINS: '{key}' (Redis key: '{redis_key}') exists: {bool(exists)}")
            return bool(exists)
        except redis.exceptions.ConnectionError as e:
            print(f"Error connecting to Redis: {e}")
            return False # 连接失败，通常认为不存在
        except Exception as e:
            print(f"Error checking existence for key '{key}': {e}")
            return False

    def __len__(self):
        """
        实现 len(dict)。
        返回当前 RedisDict 实例中所有带前缀的键的数量。
        注意：这会扫描所有以 _prefix 开头的键，在大规模生产环境中慎用，
        因为它可能是一个耗时的操作。
        """
        try:
            # 使用 SCAN 命令迭代获取所有匹配前缀的键
            count = 0
            cursor = '0'
            while cursor != 0:
                cursor, keys = self._redis.scan(cursor=cursor, match=f"{self._prefix}*", count=1000)
                count += len(keys)
            print(f"LEN: Found {count} keys with prefix '{self._prefix}'")
            return count
        except redis.exceptions.ConnectionError as e:
            print(f"Error connecting to Redis: {e}")
            return 0
        except Exception as e:
            print(f"Error calculating length: {e}")
            return 0

    def keys(self):
        """
        模拟 dict.keys()。
        返回一个包含所有 RedisDict 键的视图。
        注意：同 __len__，可能效率低下。
        """
        try:
            keys_list = []
            cursor = '0'
            while cursor != 0:
                cursor, redis_keys = self._redis.scan(cursor=cursor, match=f"{self._prefix}*", count=1000)
                for r_key in redis_keys:
                    # 移除前缀以返回原始逻辑键
                    keys_list.append(r_key[len(self._prefix):])
            print(f"KEYS: Found {len(keys_list)} keys.")
            return keys_list
        except redis.exceptions.ConnectionError as e:
            print(f"Error connecting to Redis: {e}")
            return []
        except Exception as e:
            print(f"Error getting keys: {e}")
            return []

    # 可以继续添加 values(), items() 等，实现方式类似 keys()
    # 但需要获取每个键的值，性能开销更大。

    def set_ttl(self, key, ttl_seconds):
        """
        为某个特定的键设置新的过期时间。
        """
        redis_key = self._get_redis_key(key)
        try:
            if self._redis.exists(redis_key):
                self._redis.expire(redis_key, ttl_seconds)
                print(f"TTL: '{key}' (Redis key: '{redis_key}') updated to {ttl_seconds}s.")
                return True
            else:
                print(f"TTL: Key '{key}' not found, cannot set TTL.")
                return False
        except Exception as e:
            print(f"Error setting TTL for '{key}': {e}")
            return False

    def get_ttl(self, key):
        """
        获取某个键的剩余过期时间（秒）。
        -2 表示键不存在。
        -1 表示键存在但没有设置过期时间（对于本类实现的键，不应出现此情况）。
        """
        redis_key = self._get_redis_key(key)
        try:
            ttl = self._redis.ttl(redis_key)
            print(f"GET_TTL: '{key}' (Redis key: '{redis_key}') remaining TTL: {ttl}s.")
            return ttl
        except Exception as e:
            print(f"Error getting TTL for '{key}': {e}")
            return -2 # 出现错误也视为不存在



# --- 示例用法 ---
if __name__ == "__main__":
    # 初始化 RedisDict，默认过期时间为 2 小时 (7200秒)
    my_redis_dict = RedisDict(default_ttl_seconds=2 * 60 * 60, prefix="my_app_data:")

    # --- 1. 设置键值对 ---
    print("\n--- 1. 设置键值对 ---")
    my_redis_dict["user:1:name"] = "Alice"
    my_redis_dict["user:1:age"] = 30
    my_redis_dict["product:details:101"] = {
        "name": "Laptop Pro",
        "price": 1200.50,
        "features": ["SSD", "16GB RAM"],
        "in_stock": True
    }
    my_redis_dict["shopping:cart:userX"] = ["itemA", "itemB", "itemC"]
    my_redis_dict["simple_string_value"] = "This is a plain string."

    # --- 2. 获取键值对 ---
    print("\n--- 2. 获取键值对 ---")
    print(f"user:1:name: {my_redis_dict['user:1:name']}")
    product_details = my_redis_dict["product:details:101"]
    print(f"product:details:101: {product_details} (Type: {type(product_details)})")
    shopping_cart = my_redis_dict["shopping:cart:userX"]
    print(f"shopping:cart:userX: {shopping_cart} (Type: {type(shopping_cart)})")
    print(f"simple_string_value: {my_redis_dict['simple_string_value']}")

    # 尝试获取一个不存在的键 (会抛出 KeyError)
    try:
        _ = my_redis_dict["non_existent_key"]
    except KeyError as e:
        print(f"Error: {e}")

    # --- 3. 检查键是否存在 ---
    print("\n--- 3. 检查键是否存在 ---")
    print(f"'user:1:name' exists: {'user:1:name' in my_redis_dict}")
    print(f"'non_existent_key' exists: {'non_existent_key' in my_redis_dict}")

    # --- 4. 获取键列表 ---
    print("\n--- 4. 获取所有键 ---")
    all_keys = my_redis_dict.keys()
    print(f"All keys in RedisDict: {all_keys}")
    print(f"Number of keys: {len(my_redis_dict)}")


    # --- 5. 删除键 ---
    print("\n--- 5. 删除键 ---")
    del my_redis_dict["user:1:age"]
    print(f"'user:1:age' exists after deletion: {'user:1:age' in my_redis_dict}")
    try:
        del my_redis_dict["non_existent_key_to_delete"]
    except KeyError as e:
        print(f"Error deleting: {e}")

    # --- 6. 演示过期时间 ---
    print("\n--- 6. 演示过期时间 ---")
    my_redis_dict["short_lived_data"] = "This will expire soon."
    my_redis_dict.set_ttl("short_lived_data", 5) # 设置为 5 秒过期

    print(f"Remaining TTL for 'short_lived_data': {my_redis_dict.get_ttl('short_lived_data')}s")
    print(f"'short_lived_data' exists before sleep: {'short_lived_data' in my_redis_dict}")

    time.sleep(6) # 等待 6 秒，使其过期

    print(f"Remaining TTL for 'short_lived_data' after sleep: {my_redis_dict.get_ttl('short_lived_data')}s")
    print(f"'short_lived_data' exists after sleep: {'short_lived_data' in my_redis_dict}")
    try:
        _ = my_redis_dict["short_lived_data"]
    except KeyError as e:
        print(f"Error: {e}")

    # 获取最初设置的2小时过期键的TTL
    print(f"\nRemaining TTL for 'user:1:name': {my_redis_dict.get_ttl('user:1:name')}s")
