import redis.asyncio as aioredis

from fastapi_starlette_essentials.cache import RedisCache


async def test_disabled_when_no_url():
    cache = RedisCache(None)
    await cache.connect()
    assert cache.enabled is False
    assert await cache.get("missing") is None
    assert await cache.set("k", "v") is False


async def test_roundtrip_with_fakeredis(monkeypatch):
    import fakeredis.aioredis

    def fake_from_url(*_args, **_kwargs):
        return fakeredis.aioredis.FakeRedis(decode_responses=True)

    monkeypatch.setattr(aioredis, "from_url", fake_from_url)

    cache = RedisCache("redis://localhost:6379/0")
    await cache.connect()
    assert cache.enabled is True

    assert await cache.set("user:1", {"name": "hew"}, ttl=60) is True
    assert await cache.get("user:1") == {"name": "hew"}

    await cache.set("user:2", {"name": "x"})
    assert await cache.delete_pattern("user:*") == 2
    assert await cache.get("user:1") is None

    assert await cache.clear() is True
    await cache.disconnect()