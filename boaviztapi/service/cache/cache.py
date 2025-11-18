import asyncio
from typing import Dict, Any

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, UTC, timedelta
import logging

from boaviztapi.application_context import get_app_context


class CacheService:

    _instances = {}

    def __new__(cls, *args, **kwargs):
        if _instance := cls._instances.get(kwargs["name"]):
            return _instance
        _instance = super().__new__(cls)
        cls._instances[kwargs["name"]] = _instance
        return _instance

    def __init__(self, name: str, endpoints: list[str], ttl: int = 3600, headers: dict = None):
        self.name = name
        self.endpoints = endpoints
        self.ttl = ttl
        self.headers = headers
        self.memory_cache = {}
        self.db_cache = None
        self.scheduler = AsyncIOScheduler()
        self._logger = logging.getLogger("CacheService-" + name)


    async def fetch_all(self) -> None:
        """
        Scheduled job based on the set `ttl`. It does a GET request for each endpoint and stores the results
        in the memory cache. The memory cache is also persisted to MongoDB in case of server restart.
        """
        # First, check if the database cache is not expired.
        cached_results = await self.get_results()
        if cached_results and cached_results.get("expires_at"):
            expires_at = cached_results["expires_at"]
            if isinstance(expires_at, datetime):
                expires_at = expires_at.replace(tzinfo=UTC)
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            if datetime.now(UTC) < expires_at:
                self._logger.info("Using cached results")
                # The cache is not expired, use the cached results.
                self.memory_cache = cached_results["data"]
                return

        # The cache is expired or does not exist, fetch the results from the endpoints.
        self._logger.info("Fetching results from endpoints")
        async with httpx.AsyncClient(timeout=10) as client:
            if self.headers:
                client.headers.update(self.headers)
            tasks = [client.get(url) for url in self.endpoints]
            print(self.endpoints)
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            self.memory_cache.clear()
            for url, resp in zip(self.endpoints, responses):
                if isinstance(resp, Exception):
                    self._logger.error(f"Error fetching results from {url}: {resp}")
                    self.memory_cache[url] = {"error": str(resp)}
                else:
                    self.memory_cache[url] = resp.json()
        self._logger.info("Persisting results to database")
        await self.db_cache.find_one_and_update(
            filter={"name": self.name},
            update={"$set":{
                "data": self.memory_cache,
                "expires_at": datetime.now(UTC) + timedelta(seconds=self.ttl)}},
            upsert=True
        )

    async def startup(self):
        """
        Start the cache service. It first pre-warms the cache with the latest results from the endpoints.
        """
        self._logger.info("Starting cache service")
        if not self.db_cache:
            _ctx = get_app_context()
            _db = _ctx.mongodb_client.get_database("development")
            self.db_cache = _db.get_collection("electricity_prices_cache")

        # pre-warm the cache
        self._logger.info("Pre-warming cache")
        await self.fetch_all()

        # schedule hourly refresh
        self._logger.info("Scheduling cache refresh")
        self.scheduler.add_job(self.fetch_all, 'interval', seconds=self.ttl)
        self.scheduler.start()

    async def get_results(self) -> Dict[str, Any]:
        """
        Get the results from the cache.

        It first tries to get the results from the memory cache. If it fails, it tries to get the results from the database.
        """
        if self.memory_cache:
           return self.memory_cache

        return await self.db_cache.find_one({"name": self.name})

