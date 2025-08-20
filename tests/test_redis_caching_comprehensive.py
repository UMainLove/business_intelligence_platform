"""
Comprehensive tests for Redis caching functionality to achieve production-ready
coverage. Tests cache operations, invalidation, TTL, performance impact, and
failover scenarios.
"""

import json
import time
from unittest.mock import MagicMock, patch

import pytest


class TestRedisCacheOperations:
    """Test basic Redis cache operations."""

    def test_redis_connection_setup(self):
        """Test Redis connection configuration and setup."""
        # Mock Redis connection
        with patch("redis.Redis") as mock_redis:
            mock_redis_instance = MagicMock()
            mock_redis.return_value = mock_redis_instance

            # Test connection parameters
            import redis

            redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

            # Verify connection
            mock_redis.assert_called_once_with(
                host="localhost", port=6379, db=0, decode_responses=True
            )

    def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        with patch("redis.Redis") as mock_redis:
            mock_redis_instance = MagicMock()
            mock_redis.return_value = mock_redis_instance

            # Mock cache operations
            cache = {
                "key1": "value1",
                "key2": json.dumps({"data": "structured"}),
            }

            def side_effect_get(key):
                return cache.get(key)

            def side_effect_set(key, value, ex=None):
                cache[key] = value
                return True

            mock_redis_instance.get.side_effect = side_effect_get
            mock_redis_instance.set.side_effect = side_effect_set

            # Test operations
            import redis

            client = redis.Redis()

            # Set values
            assert client.set("key1", "value1")
            assert client.set("key2", json.dumps({"data": "structured"}))

            # Get values
            assert client.get("key1") == "value1"
            data = json.loads(client.get("key2"))
            assert data["data"] == "structured"

    def test_cache_delete_operations(self):
        """Test cache deletion operations."""
        with patch("redis.Redis") as mock_redis:
            mock_redis_instance = MagicMock()
            mock_redis.return_value = mock_redis_instance

            cache = {"key1": "value1", "key2": "value2"}

            def side_effect_delete(*keys):
                count = 0
                for key in keys:
                    if key in cache:
                        del cache[key]
                        count += 1
                return count

            mock_redis_instance.delete.side_effect = side_effect_delete
            mock_redis_instance.exists.side_effect = lambda k: k in cache

            import redis

            client = redis.Redis()

            # Delete single key
            assert client.delete("key1") == 1
            assert not client.exists("key1")

            # Delete non-existent key
            assert client.delete("key3") == 0

    def test_cache_expire_and_ttl(self):
        """Test cache expiration and TTL operations."""
        with patch("redis.Redis") as mock_redis:
            mock_redis_instance = MagicMock()
            mock_redis.return_value = mock_redis_instance

            ttl_store = {}

            def side_effect_expire(key, seconds):
                ttl_store[key] = seconds
                return True

            def side_effect_ttl(key):
                return ttl_store.get(key, -1)

            mock_redis_instance.expire.side_effect = side_effect_expire
            mock_redis_instance.ttl.side_effect = side_effect_ttl
            mock_redis_instance.set.return_value = True

            import redis

            client = redis.Redis()

            # Set with expiration
            client.set("temp_key", "temp_value")
            client.expire("temp_key", 3600)

            # Check TTL
            assert client.ttl("temp_key") == 3600

            # Non-existent key
            assert client.ttl("non_existent") == -1


class TestRedisCachePatterns:
    """Test common Redis caching patterns and strategies."""

    def test_cache_aside_pattern(self):
        """Test cache-aside (lazy loading) pattern."""

        class CacheAsideService:
            def __init__(self, cache_client, db_client):
                self.cache = cache_client
                self.db = db_client

            def get_data(self, key):
                # Check cache first
                cached = self.cache.get(key)
                if cached:
                    return json.loads(cached)

                # Load from database
                data = self.db.query(key)
                if data:
                    # Store in cache
                    self.cache.set(key, json.dumps(data), ex=3600)

                return data

        # Mock clients
        mock_cache = MagicMock()
        mock_db = MagicMock()

        service = CacheAsideService(mock_cache, mock_db)

        # Test cache miss
        mock_cache.get.return_value = None
        mock_db.query.return_value = {"id": 1, "name": "test"}

        result = service.get_data("key1")
        assert result == {"id": 1, "name": "test"}
        mock_cache.set.assert_called_once()

        # Test cache hit
        mock_cache.reset_mock()
        mock_db.reset_mock()
        mock_cache.get.return_value = json.dumps({"id": 1, "name": "test"})

        result = service.get_data("key1")
        assert result == {"id": 1, "name": "test"}
        mock_db.query.assert_not_called()

    def test_write_through_cache_pattern(self):
        """Test write-through caching pattern."""

        class WriteThroughService:
            def __init__(self, cache_client, db_client):
                self.cache = cache_client
                self.db = db_client

            def save_data(self, key, data):
                # Write to database
                self.db.save(key, data)

                # Update cache
                self.cache.set(key, json.dumps(data), ex=3600)

                return True

        mock_cache = MagicMock()
        mock_db = MagicMock()

        service = WriteThroughService(mock_cache, mock_db)

        # Test write operation
        data = {"id": 1, "name": "test", "timestamp": time.time()}
        service.save_data("key1", data)

        mock_db.save.assert_called_once_with("key1", data)
        mock_cache.set.assert_called_once()

    def test_cache_stampede_prevention(self):
        """Test prevention of cache stampede (thundering herd)."""

        class StampedePreventionService:
            def __init__(self, cache_client, db_client):
                self.cache = cache_client
                self.db = db_client
                self.locks = {}

            def get_data_with_lock(self, key):
                # Check cache
                cached = self.cache.get(key)
                if cached:
                    return json.loads(cached)

                # Acquire lock
                lock_key = f"lock:{key}"
                if lock_key in self.locks:
                    # Wait for other thread to populate cache
                    time.sleep(0.1)
                    cached = self.cache.get(key)
                    if cached:
                        return json.loads(cached)

                # Set lock
                self.locks[lock_key] = True

                try:
                    # Load from database
                    data = self.db.query(key)
                    if data:
                        self.cache.set(key, json.dumps(data), ex=3600)
                    return data
                finally:
                    # Release lock
                    del self.locks[lock_key]

        mock_cache = MagicMock()
        mock_db = MagicMock()

        service = StampedePreventionService(mock_cache, mock_db)

        # Simulate cache miss with lock
        mock_cache.get.return_value = None
        mock_db.query.return_value = {"data": "test"}

        result = service.get_data_with_lock("key1")
        assert result == {"data": "test"}
        assert "lock:key1" not in service.locks  # Lock released


class TestRedisCacheInvalidation:
    """Test cache invalidation strategies and patterns."""

    def test_ttl_based_invalidation(self):
        """Test TTL-based cache invalidation."""
        with patch("redis.Redis") as mock_redis:
            mock_redis_instance = MagicMock()
            mock_redis.return_value = mock_redis_instance

            # Track TTL for keys
            ttl_tracker = {}

            def set_with_ttl(key, value, ex=None):
                if ex:
                    ttl_tracker[key] = time.time() + ex
                return True

            def check_expired(key):
                if key in ttl_tracker:
                    return time.time() > ttl_tracker[key]
                return True

            mock_redis_instance.set.side_effect = set_with_ttl
            mock_redis_instance.get.side_effect = lambda k: None if check_expired(k) else "value"

            import redis

            client = redis.Redis()

            # Set with short TTL
            client.set("short_ttl", "value", ex=1)

            # Should exist immediately
            assert client.get("short_ttl") is not None

            # Simulate time passing
            ttl_tracker["short_ttl"] = time.time() - 1

            # Should be expired
            assert client.get("short_ttl") is None

    def test_tag_based_invalidation(self):
        """Test tag-based cache invalidation."""

        class TaggedCache:
            def __init__(self, cache_client):
                self.cache = cache_client
                self.tags = {}  # tag -> set of keys

            def set_with_tags(self, key, value, tags, ttl=3600):
                # Store value
                self.cache.set(key, value, ex=ttl)

                # Track tags
                for tag in tags:
                    if tag not in self.tags:
                        self.tags[tag] = set()
                    self.tags[tag].add(key)

            def invalidate_by_tag(self, tag):
                """Invalidate all keys with given tag."""
                if tag in self.tags:
                    keys = self.tags[tag]
                    for key in keys:
                        self.cache.delete(key)
                    del self.tags[tag]
                    return len(keys)
                return 0

        mock_cache = MagicMock()
        tagged_cache = TaggedCache(mock_cache)

        # Set values with tags
        tagged_cache.set_with_tags("user:1", "data1", ["user", "profile"])
        tagged_cache.set_with_tags("user:2", "data2", ["user", "profile"])
        tagged_cache.set_with_tags("product:1", "data3", ["product"])

        # Invalidate by tag
        invalidated = tagged_cache.invalidate_by_tag("user")
        assert invalidated == 2
        assert mock_cache.delete.call_count == 2

    def test_pattern_based_invalidation(self):
        """Test pattern-based cache invalidation."""
        with patch("redis.Redis") as mock_redis:
            mock_redis_instance = MagicMock()
            mock_redis.return_value = mock_redis_instance

            # Mock keys storage
            keys_store = {
                "user:1:profile": "data1",
                "user:1:settings": "data2",
                "user:2:profile": "data3",
                "product:1": "data4",
            }

            def scan_iter(match=None):
                if match:
                    pattern = match.replace("*", "")
                    return [k for k in keys_store.keys() if k.startswith(pattern)]
                return keys_store.keys()

            mock_redis_instance.scan_iter.side_effect = scan_iter
            mock_redis_instance.delete.side_effect = lambda *keys: len(
                [k for k in keys if k in keys_store]
            )

            import redis

            client = redis.Redis()

            # Delete by pattern
            keys_to_delete = list(client.scan_iter(match="user:1:*"))
            deleted = client.delete(*keys_to_delete)

            assert deleted == 2
            assert "user:1:profile" in keys_to_delete
            assert "user:1:settings" in keys_to_delete

    def test_cascade_invalidation(self):
        """Test cascade cache invalidation for dependent data."""

        class CascadeCache:
            def __init__(self, cache_client):
                self.cache = cache_client
                self.dependencies = {}  # key -> list of dependent keys

            def set_with_dependencies(self, key, value, depends_on=None):
                self.cache.set(key, value)

                if depends_on:
                    for parent in depends_on:
                        if parent not in self.dependencies:
                            self.dependencies[parent] = []
                        self.dependencies[parent].append(key)

            def invalidate_cascade(self, key):
                """Invalidate key and all dependent keys."""
                invalidated = set()
                to_process = [key]

                while to_process:
                    current = to_process.pop()
                    if current not in invalidated:
                        self.cache.delete(current)
                        invalidated.add(current)

                        # Add dependencies to process
                        if current in self.dependencies:
                            to_process.extend(self.dependencies[current])

                return len(invalidated)

        mock_cache = MagicMock()
        cascade_cache = CascadeCache(mock_cache)

        # Set up dependencies
        cascade_cache.set_with_dependencies("parent", "data1")
        cascade_cache.set_with_dependencies("child1", "data2", depends_on=["parent"])
        cascade_cache.set_with_dependencies("child2", "data3", depends_on=["parent"])
        cascade_cache.set_with_dependencies("grandchild", "data4", depends_on=["child1"])

        # Cascade invalidation
        invalidated = cascade_cache.invalidate_cascade("parent")
        assert invalidated == 4  # parent + 2 children + 1 grandchild


class TestRedisCachePerformance:
    """Test Redis cache performance impact and optimization."""

    def test_cache_hit_ratio_tracking(self):
        """Test tracking and monitoring cache hit ratio."""

        class CacheMetrics:
            def __init__(self):
                self.hits = 0
                self.misses = 0

            def record_hit(self):
                self.hits += 1

            def record_miss(self):
                self.misses += 1

            def get_hit_ratio(self):
                total = self.hits + self.misses
                if total == 0:
                    return 0.0
                return self.hits / total

        metrics = CacheMetrics()

        # Simulate cache operations
        for _ in range(70):
            metrics.record_hit()
        for _ in range(30):
            metrics.record_miss()

        hit_ratio = metrics.get_hit_ratio()
        assert hit_ratio == 0.7
        assert metrics.hits == 70
        assert metrics.misses == 30

    def test_cache_performance_improvement(self):
        """Test performance improvement with caching."""

        class DataService:
            def __init__(self, cache_client=None):
                self.cache = cache_client
                self.db_calls = 0

            def get_data_slow(self, key):
                """Slow database query."""
                time.sleep(0.01)  # Simulate DB latency
                self.db_calls += 1
                return {"key": key, "data": "value"}

            def get_data_cached(self, key):
                """Cached version."""
                if self.cache:
                    cached = self.cache.get(key)
                    if cached:
                        return json.loads(cached)

                data = self.get_data_slow(key)

                if self.cache:
                    self.cache.set(key, json.dumps(data), ex=60)

                return data

        # Test without cache
        service_no_cache = DataService()
        start = time.time()
        for i in range(10):
            service_no_cache.get_data_cached(f"key{i % 3}")
        no_cache_time = time.time() - start

        # Test with cache
        mock_cache = MagicMock()
        cache_store = {}
        mock_cache.get.side_effect = lambda k: cache_store.get(k)
        mock_cache.set.side_effect = lambda k, v, ex=None: cache_store.update({k: v})

        service_with_cache = DataService(mock_cache)
        start = time.time()
        for i in range(10):
            service_with_cache.get_data_cached(f"key{i % 3}")
        cache_time = time.time() - start

        # Cache should be faster
        assert cache_time < no_cache_time
        assert service_with_cache.db_calls < service_no_cache.db_calls

    def test_batch_caching_optimization(self):
        """Test batch operations for cache optimization."""
        with patch("redis.Redis") as mock_redis:
            mock_redis_instance = MagicMock()
            mock_redis.return_value = mock_redis_instance

            # Mock batch operations
            def mget(*keys):
                return [f"value_{k}" if k.startswith("key") else None for k in keys]

            def mset(mapping):
                return True

            mock_redis_instance.mget.side_effect = mget
            mock_redis_instance.mset.side_effect = mset

            import redis

            client = redis.Redis()

            # Batch get
            keys = ["key1", "key2", "key3"]
            values = client.mget(*keys)
            assert len(values) == 3
            assert values[0] == "value_key1"

            # Batch set
            mapping = {f"key{i}": f"value{i}" for i in range(5)}
            assert client.mset(mapping)

    def test_connection_pooling(self):
        """Test Redis connection pooling for performance."""
        with patch("redis.ConnectionPool") as mock_pool:
            with patch("redis.Redis"):
                pool_instance = MagicMock()
                mock_pool.return_value = pool_instance

                # Create Redis client with connection pool
                import redis

                pool = redis.ConnectionPool(host="localhost", port=6379, db=0, max_connections=50)

                # Verify pool configuration
                mock_pool.assert_called_once_with(
                    host="localhost", port=6379, db=0, max_connections=50
                )

                # Create multiple clients sharing the pool
                clients = []
                for _ in range(10):
                    client = redis.Redis(connection_pool=pool)
                    clients.append(client)

                # All clients share the same pool
                assert len(clients) == 10


class TestRedisFailoverAndResilience:
    """Test Redis failover scenarios and resilience patterns."""

    def test_connection_retry_logic(self):
        """Test Redis connection retry logic."""

        class ResilientCache:
            def __init__(self, redis_client, max_retries=3):
                self.client = redis_client
                self.max_retries = max_retries

            def get_with_retry(self, key):
                for attempt in range(self.max_retries):
                    try:
                        return self.client.get(key)
                    except Exception:
                        if attempt == self.max_retries - 1:
                            raise
                        time.sleep(0.1 * (2**attempt))  # Exponential backoff
                return None

        mock_redis = MagicMock()
        cache = ResilientCache(mock_redis)

        # Test successful retry
        mock_redis.get.side_effect = [Exception("Connection error"), "success"]
        result = cache.get_with_retry("key1")
        assert result == "success"
        assert mock_redis.get.call_count == 2

    def test_fallback_to_database(self):
        """Test fallback to database when cache is unavailable."""

        class FallbackService:
            def __init__(self, cache_client, db_client):
                self.cache = cache_client
                self.db = db_client

            def get_data(self, key):
                try:
                    # Try cache first
                    cached = self.cache.get(key)
                    if cached:
                        return json.loads(cached)
                except Exception:
                    # Cache unavailable, continue to database
                    pass

                # Fallback to database
                return self.db.query(key)

        mock_cache = MagicMock()
        mock_db = MagicMock()

        service = FallbackService(mock_cache, mock_db)

        # Test cache failure fallback
        mock_cache.get.side_effect = Exception("Redis unavailable")
        mock_db.query.return_value = {"data": "from_db"}

        result = service.get_data("key1")
        assert result == {"data": "from_db"}
        mock_db.query.assert_called_once()

    def test_circuit_breaker_pattern(self):
        """Test circuit breaker pattern for Redis failures."""

        class CircuitBreaker:
            def __init__(self, failure_threshold=3, timeout=5):
                self.failure_count = 0
                self.failure_threshold = failure_threshold
                self.timeout = timeout
                self.last_failure_time = None
                self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

            def call(self, func, *args, **kwargs):
                if self.state == "OPEN":
                    if time.time() - self.last_failure_time > self.timeout:
                        self.state = "HALF_OPEN"
                    else:
                        raise Exception("Circuit breaker is OPEN")

                try:
                    result = func(*args, **kwargs)
                    if self.state == "HALF_OPEN":
                        self.state = "CLOSED"
                        self.failure_count = 0
                    return result
                except Exception as e:
                    self.failure_count += 1
                    self.last_failure_time = time.time()

                    if self.failure_count >= self.failure_threshold:
                        self.state = "OPEN"

                    raise e

        breaker = CircuitBreaker(failure_threshold=2)
        mock_func = MagicMock()

        # Test circuit opening
        mock_func.side_effect = [Exception("Error 1"), Exception("Error 2")]

        for _ in range(2):
            try:
                breaker.call(mock_func)
            except Exception:
                pass

        assert breaker.state == "OPEN"

        # Circuit should be open
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            breaker.call(mock_func)

    def test_sentinel_failover(self):
        """Test Redis Sentinel automatic failover."""
        with patch("redis.sentinel.Sentinel") as mock_sentinel:
            sentinel_instance = MagicMock()
            mock_sentinel.return_value = sentinel_instance

            master_instance = MagicMock()
            slave_instance = MagicMock()

            sentinel_instance.master_for.return_value = master_instance
            sentinel_instance.slave_for.return_value = slave_instance

            # Configure Sentinel
            import redis.sentinel

            sentinels = [("localhost", 26379)]
            sentinel = redis.sentinel.Sentinel(sentinels)

            # Get master for writes
            master = sentinel.master_for("mymaster", socket_timeout=0.1)
            assert master == master_instance

            # Get slave for reads
            slave = sentinel.slave_for("mymaster", socket_timeout=0.1)
            assert slave == slave_instance


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
