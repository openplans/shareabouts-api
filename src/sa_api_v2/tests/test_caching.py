from django.test import TestCase, override_settings
from django.core.cache import caches
from django_redis.cache import RedisCache
from ..cache import SetCache, set_cache


class TestSetCacheFallback(TestCase):
    def setUp(self):
        self.set_cache = SetCache()
        self.test_key = 'test:collection_keys'
        self.set_cache.delete(self.test_key)

    def tearDown(self):
        self.set_cache.delete(self.test_key)

    def test_add_and_is_member(self):
        self.assertFalse(self.set_cache.is_member(self.test_key, 'key_1'))
        self.set_cache.add(self.test_key, 'key_1', 'key_2')
        self.assertTrue(self.set_cache.is_member(self.test_key, 'key_1'))
        self.assertTrue(self.set_cache.is_member(self.test_key, 'key_2'))
        self.assertFalse(self.set_cache.is_member(self.test_key, 'key_3'))

    def test_get_members(self):
        self.set_cache.add(self.test_key, 'key_a', 'key_b')
        members = self.set_cache.get_members(self.test_key)
        self.assertEqual(members, {'key_a', 'key_b'})

    def test_remove_member(self):
        self.set_cache.add(self.test_key, 'key_a', 'key_b')
        self.set_cache.remove(self.test_key, 'key_a')
        self.assertFalse(self.set_cache.is_member(self.test_key, 'key_a'))
        self.assertTrue(self.set_cache.is_member(self.test_key, 'key_b'))
        self.assertEqual(self.set_cache.get_members(self.test_key), {'key_b'})

    def test_delete_set(self):
        self.set_cache.add(self.test_key, 'key_x', 'key_y')
        self.set_cache.delete(self.test_key)
        self.assertFalse(self.set_cache.is_member(self.test_key, 'key_x'))
        self.assertEqual(self.set_cache.get_members(self.test_key), set())


class TestSetCacheWithRedis(TestCase):
    def setUp(self):
        # Configure django-redis backend pointing to local test Redis instance in podman
        try:
            self.redis_backend = RedisCache('redis://127.0.0.1:16379/0', {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'KEY_PREFIX': 'test_setcache',
            })
            # Test connectivity
            client = self.redis_backend.client.get_client(write=True)
            client.ping()
            self.redis_available = True
        except Exception:
            self.redis_available = False

        self.set_cache = SetCache(cache_backend=self.redis_backend) if self.redis_available else None
        self.test_key = 'test:redis_collection_keys'
        if self.redis_available:
            self.set_cache.delete(self.test_key)

    def tearDown(self):
        if self.redis_available and self.set_cache:
            self.set_cache.delete(self.test_key)

    def test_redis_native_sadd_and_sismember(self):
        if not self.redis_available:
            self.skipTest('Redis container not reachable at 127.0.0.1:16379')

        self.assertFalse(self.set_cache.is_member(self.test_key, 'url_page_1'))
        self.set_cache.add(self.test_key, 'url_page_1', 'url_page_2', timeout=300)

        # Verify atomic membership
        self.assertTrue(self.set_cache.is_member(self.test_key, 'url_page_1'))
        self.assertTrue(self.set_cache.is_member(self.test_key, 'url_page_2'))
        self.assertFalse(self.set_cache.is_member(self.test_key, 'url_page_3'))

        # Verify native Redis key type is 'set'
        raw_client = self.redis_backend.client.get_client(write=True)
        redis_key = self.redis_backend.make_key(self.test_key)
        key_type = raw_client.type(redis_key)
        if isinstance(key_type, bytes):
            key_type = key_type.decode('utf-8')
        self.assertEqual(key_type, 'set')

    def test_redis_native_smembers_decoding(self):
        if not self.redis_available:
            self.skipTest('Redis container not reachable at 127.0.0.1:16379')

        self.set_cache.add(self.test_key, 'item_1', 'item_2')
        members = self.set_cache.get_members(self.test_key)

        # Verify decoded string set
        self.assertEqual(members, {'item_1', 'item_2'})
        self.assertTrue(all(isinstance(m, str) for m in members))

    def test_redis_ttl_refresh_on_add(self):
        if not self.redis_available:
            self.skipTest('Redis container not reachable at 127.0.0.1:16379')

        raw_client = self.redis_backend.client.get_client(write=True)
        redis_key = self.redis_backend.make_key(self.test_key)

        self.set_cache.add(self.test_key, 'item_1', timeout=600)
        ttl = raw_client.ttl(redis_key)
        self.assertGreater(ttl, 0)
        self.assertLessEqual(ttl, 600)

    def test_redis_native_srem_and_delete(self):
        if not self.redis_available:
            self.skipTest('Redis container not reachable at 127.0.0.1:16379')

        self.set_cache.add(self.test_key, 'item_1', 'item_2', 'item_3')
        self.set_cache.remove(self.test_key, 'item_2')
        self.assertEqual(self.set_cache.get_members(self.test_key), {'item_1', 'item_3'})

        self.set_cache.delete(self.test_key)
        self.assertEqual(self.set_cache.get_members(self.test_key), set())
