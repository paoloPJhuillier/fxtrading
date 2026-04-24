"""
Switchable database abstraction layer.

Supports:
  - "mongodb"   : MongoDB via motor (async)
  - "couchbase" : Couchbase Enterprise via SDK 4.x (sync, wrapped with asyncio.to_thread)

Controlled by DB_TYPE env var.

Collections are accessed via attribute: db.users, db.deals, etc.
Each collection proxy supports MongoDB-like operations:
  find_one, find, insert_one, insert_many, update_one, update_many,
  delete_one, delete_many, count_documents, find_one_and_update, aggregate
"""

import os
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# -- Scope/Collection mapping (Couchbase best practice) --
# Maps MongoDB collection names → (scope, collection) in Couchbase
SCOPE_MAP = {
    "users":             ("identity",  "users"),
    "deals":             ("trading",   "deals"),
    "counters":          ("trading",   "deal_counters"),
    "audit_logs":        ("audit",     "audit_logs"),
    "companies":         ("reference", "companies"),
    "banks":             ("reference", "banks"),
    "bank_accounts":     ("reference", "bank_accounts"),
    "currencies":        ("reference", "currencies"),
    "transaction_types": ("reference", "transaction_types"),
    "transfer_types":    ("reference", "transfer_types"),
}

ALL_SCOPES = sorted({scope for scope, _ in SCOPE_MAP.values()})


@dataclass
class UpdateResult:
    modified_count: int = 0


@dataclass
class DeleteResult:
    deleted_count: int = 0


# -- Factory ---------------------------------------------------------------

_instance = None


async def get_database():
    """Return a singleton database proxy based on DB_TYPE env var."""
    global _instance
    if _instance is not None:
        return _instance

    db_type = os.environ.get("DB_TYPE", "mongodb").lower()

    if db_type == "couchbase":
        from services.db_couchbase import CouchbaseDatabase
        _instance = await CouchbaseDatabase.create()
    else:
        from services.db_mongo import MongoDatabase
        _instance = MongoDatabase.create()

    logger.info("Database backend: %s", type(_instance).__name__)
    return _instance
