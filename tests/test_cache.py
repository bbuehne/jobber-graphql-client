"""NullCache is truly a no-op and structurally satisfies ResponseCache."""

from jobber_graphql_client.cache import NullCache, ResponseCache


def test_nullcache_satisfies_protocol():
    assert isinstance(NullCache(), ResponseCache)


async def test_nullcache_get_always_misses():
    cache = NullCache()
    assert await cache.get("query Q { x }") is None
    assert await cache.get("query Q { x }", {"a": 1}) is None


async def test_nullcache_set_stores_nothing():
    cache = NullCache()
    stored = await cache.set("query Q { x }", {"a": 1}, {"data": {"x": 1}}, "things")
    assert stored is False
    # And a subsequent get still misses.
    assert await cache.get("query Q { x }", {"a": 1}) is None


async def test_nullcache_invalidate_removes_nothing():
    cache = NullCache()
    assert await cache.invalidate("things") == 0


def test_nullcache_detect_query_type_is_default():
    # "default" is the one type the client never invalidates, so a NullCache
    # client performs no invalidation work at all.
    cache = NullCache()
    assert cache.detect_query_type("mutation M { y }") == "default"
    assert cache.detect_query_type("query Q { x }") == "default"
