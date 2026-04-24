"""
MongoDB backend — thin wrapper around motor that exposes the same
collection-level API used by server.py.  Almost zero overhead.
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument  # noqa: re-export for server.py

from services.database import UpdateResult, DeleteResult


class MongoCursor:
    """Wraps a motor cursor to preserve the .sort().skip().limit().to_list() chain."""

    __slots__ = ("_cursor",)

    def __init__(self, cursor):
        self._cursor = cursor

    def sort(self, key, direction=None):
        if direction is not None:
            self._cursor = self._cursor.sort(key, direction)
        else:
            self._cursor = self._cursor.sort(key)
        return self

    def skip(self, n):
        self._cursor = self._cursor.skip(n)
        return self

    def limit(self, n):
        self._cursor = self._cursor.limit(n)
        return self

    async def to_list(self, length=None):
        return await self._cursor.to_list(length)

    def __aiter__(self):
        return self

    async def __anext__(self):
        if await self._cursor.fetch_next:
            return self._cursor.next_object()
        raise StopAsyncIteration


class MongoCollection:
    """Thin proxy around a motor collection."""

    __slots__ = ("_col",)

    def __init__(self, col):
        self._col = col

    async def find_one(self, query, projection=None):
        return await self._col.find_one(query, projection)

    def find(self, query, projection=None):
        return MongoCursor(self._col.find(query, projection))

    async def insert_one(self, doc):
        return await self._col.insert_one(doc)

    async def insert_many(self, docs):
        return await self._col.insert_many(docs)

    async def update_one(self, query, update, upsert=False, array_filters=None):
        kwargs = {}
        if upsert:
            kwargs["upsert"] = True
        if array_filters:
            kwargs["array_filters"] = array_filters
        r = await self._col.update_one(query, update, **kwargs)
        return UpdateResult(r.modified_count)

    async def update_many(self, query, update, array_filters=None):
        kwargs = {}
        if array_filters:
            kwargs["array_filters"] = array_filters
        r = await self._col.update_many(query, update, **kwargs)
        return UpdateResult(r.modified_count)

    async def delete_one(self, query):
        r = await self._col.delete_one(query)
        return DeleteResult(r.deleted_count)

    async def delete_many(self, query):
        r = await self._col.delete_many(query)
        return DeleteResult(r.deleted_count)

    async def count_documents(self, query):
        return await self._col.count_documents(query)

    async def find_one_and_update(self, query, update, upsert=False, return_document=None):
        kwargs = {}
        if upsert:
            kwargs["upsert"] = True
        if return_document is not None:
            # Accept True as shorthand for AFTER
            kwargs["return_document"] = ReturnDocument.AFTER if return_document else ReturnDocument.BEFORE
        return await self._col.find_one_and_update(query, update, **kwargs)

    def aggregate(self, pipeline):
        return MongoCursor(self._col.aggregate(pipeline))


class MongoDatabase:
    """Database proxy that returns MongoCollection for attribute/item access."""

    def __init__(self, motor_db):
        self._db = motor_db
        self._cache = {}

    @classmethod
    def create(cls):
        mongo_url = os.environ["MONGO_URL"]
        db_name = os.environ["DB_NAME"]
        client = AsyncIOMotorClient(mongo_url)
        return cls(client[db_name])

    def _col(self, name):
        if name not in self._cache:
            self._cache[name] = MongoCollection(self._db[name])
        return self._cache[name]

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return self._col(name)

    def __getitem__(self, name):
        return self._col(name)
