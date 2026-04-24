"""
Couchbase Enterprise backend using SDK 4.x with scopes & collections.

All Couchbase SDK calls are synchronous; they're wrapped with
asyncio.to_thread() so they don't block the FastAPI event loop.

N1QL (SQL++) is used for queries; KV + subdocument ops for single-doc mutations.
"""

import os
import asyncio
import logging
import copy
from datetime import timedelta

from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions, ClusterTimeoutOptions, QueryOptions
from couchbase.auth import PasswordAuthenticator
from couchbase import subdocument as SD
from couchbase.exceptions import (
    DocumentNotFoundException,
    DocumentExistsException,
    CouchbaseException,
    QueryIndexNotFoundException,
)

from services.database import SCOPE_MAP, ALL_SCOPES, UpdateResult, DeleteResult

logger = logging.getLogger(__name__)

MAX_INDEX_RETRIES = 10
INDEX_RETRY_DELAY = 5  # seconds


def _retry_on_no_index(fn):
    """Retry a query function if indexes aren't online yet."""
    import time
    for attempt in range(MAX_INDEX_RETRIES):
        try:
            return fn()
        except (QueryIndexNotFoundException, CouchbaseException) as e:
            is_no_index = "No index available" in str(e) or isinstance(e, QueryIndexNotFoundException)
            if is_no_index and attempt < MAX_INDEX_RETRIES - 1:
                logger.info("Index not ready (attempt %d/%d): %.200s",
                            attempt + 1, MAX_INDEX_RETRIES, str(e))
                time.sleep(INDEX_RETRY_DELAY)
            elif is_no_index:
                logger.error("Index retry exhausted: %.300s", str(e))
                raise
            else:
                raise


# ---------------------------------------------------------------------------
# Query builder: MongoDB query dict → N1QL WHERE clause
# ---------------------------------------------------------------------------

class _ParamCounter:
    def __init__(self):
        self.n = 0

    def next(self, prefix="p"):
        self.n += 1
        return f"{prefix}{self.n}"


def _build_where(query: dict, counter: _ParamCounter | None = None) -> tuple[str, dict]:
    """Translate a MongoDB-style query dict to (where_clause, named_params)."""
    if counter is None:
        counter = _ParamCounter()

    conditions = []
    params = {}

    for key, value in query.items():
        if key == "$or":
            or_parts = []
            for sub in value:
                w, p = _build_where(sub, counter)
                or_parts.append(f"({w})")
                params.update(p)
            conditions.append(f"({' OR '.join(or_parts)})")

        elif isinstance(value, dict) and any(k.startswith("$") for k in value):
            for op, op_val in value.items():
                if op == "$regex":
                    options = value.get("$options", "")
                    pn = counter.next()
                    pattern = f"%{op_val}%"
                    if "i" in options:
                        conditions.append(f"LOWER(d.`{key}`) LIKE ${pn}")
                        params[pn] = pattern.lower()
                    else:
                        conditions.append(f"d.`{key}` LIKE ${pn}")
                        params[pn] = pattern
                elif op == "$options":
                    pass  # consumed with $regex
                elif op == "$gte":
                    pn = counter.next()
                    conditions.append(f"d.`{key}` >= ${pn}")
                    params[pn] = op_val
                elif op == "$lte":
                    pn = counter.next()
                    conditions.append(f"d.`{key}` <= ${pn}")
                    params[pn] = op_val
                elif op == "$lt":
                    pn = counter.next()
                    conditions.append(f"d.`{key}` < ${pn}")
                    params[pn] = op_val
                elif op == "$gt":
                    pn = counter.next()
                    conditions.append(f"d.`{key}` > ${pn}")
                    params[pn] = op_val
                elif op == "$exists":
                    if op_val:
                        conditions.append(f"d.`{key}` IS NOT MISSING")
                    else:
                        conditions.append(f"d.`{key}` IS MISSING")
                elif op == "$elemMatch":
                    elem_parts = []
                    for ek, ev in op_val.items():
                        if isinstance(ev, dict):
                            for eop, eov in ev.items():
                                if eop == "$exists":
                                    if eov:
                                        elem_parts.append(f"v.`{ek}` IS NOT MISSING")
                                    else:
                                        elem_parts.append(f"v.`{ek}` IS MISSING")
                        else:
                            pn = counter.next()
                            elem_parts.append(f"v.`{ek}` = ${pn}")
                            params[pn] = ev
                    conditions.append(
                        f"ANY v IN d.`{key}` SATISFIES {' AND '.join(elem_parts)} END"
                    )
        else:
            pn = counter.next()
            conditions.append(f"d.`{key}` = ${pn}")
            params[pn] = value

    return " AND ".join(conditions) if conditions else "", params


def _projection_fields(projection: dict | None) -> str:
    """Convert a MongoDB projection dict to a N1QL SELECT field list."""
    if not projection:
        return "d.*"
    includes = [k for k, v in projection.items() if v and k != "_id"]
    if includes:
        return ", ".join(f"d.`{f}`" for f in includes)
    # For exclusion projections, SELECT d.* and post-filter is simpler
    return "d.*"


# ---------------------------------------------------------------------------
# Couchbase cursor (accumulates sort/skip/limit, executes on to_list)
# ---------------------------------------------------------------------------

class CouchbaseCursor:
    def __init__(self, cb_col, query, projection, is_aggregate=False, pipeline=None):
        self._cb_col = cb_col
        self._query = query
        self._projection = projection
        self._sort_field = None
        self._sort_dir = None
        self._skip_val = 0
        self._limit_val = 0
        self._is_aggregate = is_aggregate
        self._pipeline = pipeline
        self._iter_results = None
        self._iter_idx = 0

    def sort(self, key, direction=None):
        self._sort_field = key
        self._sort_dir = direction
        return self

    def skip(self, n):
        self._skip_val = n
        return self

    def limit(self, n):
        self._limit_val = n
        return self

    async def to_list(self, length=None):
        if self._is_aggregate:
            return await self._cb_col._execute_aggregate(self._pipeline)
        return await self._cb_col._execute_find(
            self._query,
            self._projection,
            self._sort_field,
            self._sort_dir,
            self._skip_val,
            self._limit_val or length,
        )

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._iter_results is None:
            self._iter_results = await self.to_list(100000)
        if self._iter_idx >= len(self._iter_results):
            raise StopAsyncIteration
        item = self._iter_results[self._iter_idx]
        self._iter_idx += 1
        return item


# ---------------------------------------------------------------------------
# Couchbase collection proxy
# ---------------------------------------------------------------------------

class CouchbaseCollection:
    def __init__(self, cluster, bucket_name, scope_name, collection_name):
        self._cluster = cluster
        self._bucket_name = bucket_name
        self._scope_name = scope_name
        self._collection_name = collection_name

        bucket = cluster.bucket(bucket_name)
        self._scope = bucket.scope(scope_name)
        self._collection = self._scope.collection(collection_name)
        self._fqn = f"`{bucket_name}`.`{scope_name}`.`{collection_name}`"

    # -- helpers ---

    def _strip_id(self, doc: dict | None, projection: dict | None = None) -> dict | None:
        """Apply exclusion projection (mimics MongoDB _id:0 + field exclusions)."""
        if doc is None:
            return None
        if projection:
            excludes = [k for k, v in projection.items() if not v]
            if excludes:
                doc = {k: v for k, v in doc.items() if k not in excludes}
        return doc

    def _doc_key(self, doc_or_query: dict) -> str | None:
        """Extract the document key ('id' field) from a query or doc."""
        return doc_or_query.get("id")

    # -- read ops --

    async def find_one(self, query, projection=None):
        doc_id = self._doc_key(query)
        simple_eq = all(not isinstance(v, dict) for v in query.values()) and "$or" not in query

        # Fast path: KV get when querying by known fields that include 'id'
        if doc_id and simple_eq:
            def _kv_get():
                try:
                    result = self._collection.get(doc_id)
                    doc = result.content_as[dict]
                    # Verify additional query fields match
                    for k, v in query.items():
                        if k == "id":
                            continue
                        if doc.get(k) != v:
                            return None
                    return doc
                except DocumentNotFoundException:
                    return None
            doc = await asyncio.to_thread(_kv_get)
            return self._strip_id(doc, projection)

        # Slow path: N1QL
        where, params = _build_where(query)
        fields = _projection_fields(projection)
        sql = f"SELECT {fields} FROM {self._fqn} d"
        if where:
            sql += f" WHERE {where}"
        sql += " LIMIT 1"

        def _query():
            rows = list(self._cluster.query(sql, QueryOptions(named_parameters=params)))
            return rows[0] if rows else None

        doc = await asyncio.to_thread(lambda: _retry_on_no_index(_query))
        return self._strip_id(doc, projection)

    def find(self, query, projection=None):
        return CouchbaseCursor(self, query, projection)

    async def _execute_find(self, query, projection, sort_field, sort_dir, skip_val, limit_val):
        where, params = _build_where(query)
        fields = _projection_fields(projection)
        sql = f"SELECT {fields} FROM {self._fqn} d"
        if where:
            sql += f" WHERE {where}"
        if sort_field:
            direction = "DESC" if sort_dir == -1 else "ASC"
            sql += f" ORDER BY d.`{sort_field}` {direction}"
        if skip_val:
            sql += f" OFFSET {skip_val}"
        if limit_val:
            sql += f" LIMIT {limit_val}"

        def _query():
            rows = list(self._cluster.query(sql, QueryOptions(named_parameters=params)))
            if projection:
                excludes = [k for k, v in projection.items() if not v]
                if excludes:
                    rows = [{k: v for k, v in row.items() if k not in excludes} for row in rows]
            return rows

        return await asyncio.to_thread(lambda: _retry_on_no_index(_query))

    async def count_documents(self, query):
        where, params = _build_where(query)
        sql = f"SELECT COUNT(*) AS cnt FROM {self._fqn} d"
        if where:
            sql += f" WHERE {where}"

        def _query():
            rows = list(self._cluster.query(sql, QueryOptions(named_parameters=params)))
            return rows[0]["cnt"] if rows else 0

        return await asyncio.to_thread(lambda: _retry_on_no_index(_query))

    # -- write ops --

    async def insert_one(self, doc):
        doc_id = self._doc_key(doc)
        if not doc_id:
            raise ValueError("Document must have an 'id' field for Couchbase KV")
        clean = {k: v for k, v in doc.items() if k != "_id"}

        def _insert():
            self._collection.upsert(doc_id, clean)

        await asyncio.to_thread(_insert)

    async def insert_many(self, docs):
        def _insert_batch():
            for doc in docs:
                doc_id = doc.get("id")
                if not doc_id:
                    continue
                clean = {k: v for k, v in doc.items() if k != "_id"}
                self._collection.upsert(doc_id, clean)

        await asyncio.to_thread(_insert_batch)

    async def update_one(self, query, update, upsert=False, array_filters=None):
        doc = await self.find_one(query)

        if not doc and not upsert:
            return UpdateResult(0)

        if not doc:
            doc = dict(query)

        doc = self._apply_update(doc, update, array_filters)
        doc_id = doc.get("id")
        if not doc_id:
            return UpdateResult(0)

        clean = {k: v for k, v in doc.items() if k != "_id"}

        def _upsert():
            self._collection.upsert(doc_id, clean)

        await asyncio.to_thread(_upsert)
        return UpdateResult(1)

    async def update_many(self, query, update, array_filters=None):
        # Fetch all matching docs, apply update, upsert back
        docs = await self._execute_find(query, None, None, None, 0, 100000)
        if not docs:
            return UpdateResult(0)

        def _batch_update():
            count = 0
            for doc in docs:
                updated = self._apply_update(copy.deepcopy(doc), update, array_filters)
                doc_id = updated.get("id")
                if doc_id:
                    clean = {k: v for k, v in updated.items() if k != "_id"}
                    self._collection.upsert(doc_id, clean)
                    count += 1
            return count

        count = await asyncio.to_thread(_batch_update)
        return UpdateResult(count)

    async def delete_one(self, query):
        doc = await self.find_one(query)
        if not doc:
            return DeleteResult(0)
        doc_id = doc.get("id")
        if not doc_id:
            return DeleteResult(0)

        def _remove():
            try:
                self._collection.remove(doc_id)
                return 1
            except DocumentNotFoundException:
                return 0

        count = await asyncio.to_thread(_remove)
        return DeleteResult(count)

    async def delete_many(self, query):
        docs = await self._execute_find(query, {"id": 1}, None, None, 0, 100000)
        if not docs:
            return DeleteResult(0)

        def _batch_remove():
            count = 0
            for doc in docs:
                doc_id = doc.get("id")
                if doc_id:
                    try:
                        self._collection.remove(doc_id)
                        count += 1
                    except DocumentNotFoundException:
                        pass
            return count

        count = await asyncio.to_thread(_batch_remove)
        return DeleteResult(count)

    async def find_one_and_update(self, query, update, upsert=False, return_document=None):
        """Atomic get-modify-upsert.  Used for counters."""
        doc_id = self._doc_key(query)
        # Build a deterministic key for counter docs
        if not doc_id:
            parts = [f"{k}={v}" for k, v in sorted(query.items())]
            doc_id = "__".join(parts)

        def _atomic_update():
            try:
                result = self._collection.get(doc_id)
                doc = result.content_as[dict]
            except DocumentNotFoundException:
                if not upsert:
                    return None
                doc = dict(query)
                doc["id"] = doc_id

            # Apply $inc
            if "$inc" in update:
                for k, v in update["$inc"].items():
                    doc[k] = doc.get(k, 0) + v
            # Apply $set
            if "$set" in update:
                for k, v in update["$set"].items():
                    doc[k] = v

            clean = {k: v for k, v in doc.items() if k != "_id"}
            self._collection.upsert(doc_id, clean)
            return clean

        return await asyncio.to_thread(_atomic_update)

    # -- aggregation --

    def aggregate(self, pipeline):
        return CouchbaseCursor(self, {}, None, is_aggregate=True, pipeline=pipeline)

    async def _execute_aggregate(self, pipeline):
        """
        Translate MongoDB aggregation pipeline to N1QL.
        Handles the specific $match + $facet pattern used by the dashboard.
        """
        match_stage = {}
        facet_stage = {}

        for stage in pipeline:
            if "$match" in stage:
                match_stage = stage["$match"]
            elif "$facet" in stage:
                facet_stage = stage["$facet"]

        if not facet_stage:
            return []

        where, params = _build_where(match_stage)
        where_clause = f" WHERE {where}" if where else ""

        results = {}
        for facet_name, facet_pipeline in facet_stage.items():
            results[facet_name] = await self._execute_facet(
                facet_pipeline, where_clause, params
            )

        return [results]

    async def _execute_facet(self, facet_pipeline, where_clause, base_params):
        """Execute a single facet sub-pipeline as N1QL."""
        # Detect the pattern
        has_group = any("$group" in s for s in facet_pipeline)

        if has_group:
            return await self._execute_group_facet(facet_pipeline, where_clause, base_params)

        # Simple sort + limit + project (e.g., "recent" facet)
        sort_field = None
        sort_dir = "ASC"
        limit_val = 1000

        for stage in facet_pipeline:
            if "$sort" in stage:
                for k, v in stage["$sort"].items():
                    sort_field = k
                    sort_dir = "DESC" if v == -1 else "ASC"
            if "$limit" in stage:
                limit_val = stage["$limit"]

        sql = f"SELECT d.* FROM {self._fqn} d{where_clause}"
        if sort_field:
            sql += f" ORDER BY d.`{sort_field}` {sort_dir}"
        sql += f" LIMIT {limit_val}"

        def _query():
            return list(self._cluster.query(sql, QueryOptions(named_parameters=dict(base_params))))

        return await asyncio.to_thread(_query)

    async def _execute_group_facet(self, facet_pipeline, where_clause, base_params):
        """Translate $group stage to N1QL GROUP BY."""
        group_stage = next(s["$group"] for s in facet_pipeline if "$group" in s)
        sort_stage = next((s["$sort"] for s in facet_pipeline if "$sort" in s), None)

        group_id = group_stage["_id"]

        # Determine GROUP BY expression
        if isinstance(group_id, dict):
            # e.g., {"$substr": ["$created_at", 0, 10]}
            if "$substr" in group_id:
                field = group_id["$substr"][0].lstrip("$")
                start = group_id["$substr"][1]
                length = group_id["$substr"][2]
                group_expr = f"SUBSTR(d.`{field}`, {start}, {length})"
            else:
                group_expr = "d.`id`"
        elif isinstance(group_id, str) and group_id.startswith("$"):
            field = group_id.lstrip("$")
            group_expr = f"d.`{field}`"
        else:
            group_expr = f"'{group_id}'"

        # Build SELECT with aggregation fields
        select_parts = [f"{group_expr} AS `_id`"]
        for agg_name, agg_def in group_stage.items():
            if agg_name == "_id":
                continue
            if isinstance(agg_def, dict):
                if "$sum" in agg_def:
                    sum_val = agg_def["$sum"]
                    if sum_val == 1:
                        select_parts.append(f"COUNT(*) AS `{agg_name}`")
                    elif isinstance(sum_val, dict) and "$toDouble" in sum_val:
                        inner = sum_val["$toDouble"]
                        if isinstance(inner, dict) and "$ifNull" in inner:
                            field = inner["$ifNull"][0].lstrip("$")
                            default = inner["$ifNull"][1]
                            select_parts.append(
                                f"SUM(TONUMBER(IFMISSINGORNULL(d.`{field}`, {default}))) AS `{agg_name}`"
                            )
                        elif isinstance(inner, str) and inner.startswith("$"):
                            field = inner.lstrip("$")
                            select_parts.append(f"SUM(TONUMBER(d.`{field}`)) AS `{agg_name}`")

        sql = f"SELECT {', '.join(select_parts)} FROM {self._fqn} d{where_clause}"
        sql += f" GROUP BY {group_expr}"

        if sort_stage:
            for k, v in sort_stage.items():
                direction = "DESC" if v == -1 else "ASC"
                if k == "_id":
                    sql += f" ORDER BY {group_expr} {direction}"
                else:
                    sql += f" ORDER BY `{k}` {direction}"

        def _query():
            return list(self._cluster.query(sql, QueryOptions(named_parameters=dict(base_params))))

        return await asyncio.to_thread(_query)

    # -- update helpers --

    @staticmethod
    def _apply_update(doc: dict, update: dict, array_filters=None) -> dict:
        """Apply MongoDB update operators to a document in-memory."""
        if "$set" in update:
            for key, value in update["$set"].items():
                if array_filters and "$[" in key:
                    # Handle array filter syntax: "settlement_proofs.$[elem].proof_type"
                    parts = key.split(".$[")
                    arr_field = parts[0]
                    rest = parts[1]  # "elem].proof_type"
                    filter_var = rest.split("]")[0]  # "elem"
                    nested_field = rest.split("].", 1)[1] if "]." in rest else None

                    # Find the matching filter
                    af = next((f for f in array_filters if any(k.startswith(f"{filter_var}.") for k in f)), None)
                    if af and arr_field in doc and isinstance(doc[arr_field], list):
                        for item in doc[arr_field]:
                            match = True
                            for fk, fv in af.items():
                                item_key = fk.split(".", 1)[1] if "." in fk else fk
                                if isinstance(fv, dict):
                                    for fop, fov in fv.items():
                                        if fop == "$exists":
                                            if fov and item_key in item:
                                                pass
                                            elif not fov and item_key not in item:
                                                pass
                                            else:
                                                match = False
                                else:
                                    if item.get(item_key) != fv:
                                        match = False
                            if match and nested_field:
                                item[nested_field] = value
                else:
                    doc[key] = value

        if "$push" in update:
            for key, value in update["$push"].items():
                if key not in doc:
                    doc[key] = []
                if isinstance(doc[key], list):
                    doc[key].append(value)

        if "$pull" in update:
            for key, value in update["$pull"].items():
                if key in doc and isinstance(doc[key], list):
                    if isinstance(value, dict):
                        doc[key] = [
                            item for item in doc[key]
                            if not all(item.get(k) == v for k, v in value.items())
                        ]
                    else:
                        doc[key] = [item for item in doc[key] if item != value]

        if "$unset" in update:
            for key in update["$unset"]:
                doc.pop(key, None)

        if "$inc" in update:
            for key, value in update["$inc"].items():
                doc[key] = doc.get(key, 0) + value

        return doc


# ---------------------------------------------------------------------------
# Couchbase database proxy
# ---------------------------------------------------------------------------

class CouchbaseDatabase:
    def __init__(self, cluster, bucket_name):
        self._cluster = cluster
        self._bucket_name = bucket_name
        self._cache = {}

    @classmethod
    async def create(cls):
        conn_str = os.environ["CB_CONNECTION_STRING"]
        username = os.environ["CB_USERNAME"]
        password = os.environ["CB_PASSWORD"]
        bucket_name = os.environ["CB_BUCKET_NAME"]

        def _connect():
            cluster = Cluster(
                conn_str,
                ClusterOptions(
                    PasswordAuthenticator(username, password),
                    timeout_options=ClusterTimeoutOptions(
                        connect_timeout=timedelta(seconds=20),
                        kv_timeout=timedelta(seconds=10),
                        query_timeout=timedelta(seconds=30),
                    ),
                ),
            )
            cluster.wait_until_ready(timedelta(seconds=20))
            logger.info("Connected to Couchbase: %s bucket=%s", conn_str, bucket_name)
            return cluster

        cluster = await asyncio.to_thread(_connect)
        instance = cls(cluster, bucket_name)
        await instance._ensure_scopes_and_collections()
        await instance._ensure_indexes()
        return instance

    async def _ensure_scopes_and_collections(self):
        """Create scopes and collections if they don't exist."""
        def _provision():
            bucket = self._cluster.bucket(self._bucket_name)
            mgr = bucket.collections()
            existing = mgr.get_all_scopes()
            existing_map = {}
            for s in existing:
                existing_map[s.name] = {c.name for c in s.collections}

            created_any = False
            for mongo_col, (scope_name, col_name) in SCOPE_MAP.items():
                if scope_name not in existing_map:
                    try:
                        mgr.create_scope(scope_name)
                        logger.info("Created scope: %s", scope_name)
                        existing_map[scope_name] = set()
                        created_any = True
                    except CouchbaseException as e:
                        if "already exists" not in str(e).lower():
                            logger.warning("Scope create failed: %s — %s", scope_name, e)
                        else:
                            existing_map.setdefault(scope_name, set())

                if col_name not in existing_map.get(scope_name, set()):
                    try:
                        mgr.create_collection(scope_name, col_name)
                        logger.info("Created collection: %s.%s", scope_name, col_name)
                        created_any = True
                    except CouchbaseException as e:
                        if "already exists" not in str(e).lower():
                            logger.warning("Collection create failed: %s.%s — %s", scope_name, col_name, e)
            return created_any

        created = await asyncio.to_thread(_provision)
        if created:
            # Wait for Couchbase to propagate collection metadata
            logger.info("Waiting for collection metadata propagation...")
            await asyncio.sleep(5)

    async def _ensure_indexes(self):
        """Create primary + key secondary indexes for each collection, one at a time."""
        def _create_indexes():
            created = 0
            for mongo_col, (scope_name, col_name) in SCOPE_MAP.items():
                fqn = f"`{self._bucket_name}`.`{scope_name}`.`{col_name}`"
                try:
                    result = self._cluster.query(
                        f"CREATE PRIMARY INDEX IF NOT EXISTS ON {fqn}",
                        QueryOptions(timeout=timedelta(seconds=120)),
                    )
                    list(result)  # consume to ensure completion
                    created += 1
                except CouchbaseException as e:
                    logger.warning("Primary index on %s: %s", fqn, e)

            # Secondary indexes
            secondaries = [
                ("identity", "users", "email", "idx_users_email"),
                ("identity", "users", "role", "idx_users_role"),
                ("trading", "deals", "created_by", "idx_deals_created_by"),
                ("trading", "deals", "status", "idx_deals_status"),
                ("trading", "deals", "created_at", "idx_deals_created_at"),
                ("trading", "deals", "client_name", "idx_deals_client"),
                ("reference", "bank_accounts", "bank_id", "idx_bank_accounts_bank_id"),
                ("audit", "audit_logs", "created_at", "idx_audit_created_at"),
            ]
            for scope_name, col_name, field, idx_name in secondaries:
                fqn = f"`{self._bucket_name}`.`{scope_name}`.`{col_name}`"
                try:
                    result = self._cluster.query(
                        f"CREATE INDEX IF NOT EXISTS `{idx_name}` ON {fqn}(`{field}`)",
                        QueryOptions(timeout=timedelta(seconds=120)),
                    )
                    list(result)
                except CouchbaseException as e:
                    logger.debug("Index %s: %s", idx_name, e)

            logger.info("Couchbase indexes ensured (%d primary)", created)

        await asyncio.to_thread(_create_indexes)

        # Verify indexes are online by running a simple test query on EACH collection
        def _verify():
            import time
            for attempt in range(10):
                all_ok = True
                for mongo_col, (scope_name, col_name) in SCOPE_MAP.items():
                    fqn = f"`{self._bucket_name}`.`{scope_name}`.`{col_name}`"
                    try:
                        list(self._cluster.query(f"SELECT COUNT(*) AS cnt FROM {fqn} d"))
                    except (QueryIndexNotFoundException, CouchbaseException):
                        all_ok = False
                        break
                if all_ok:
                    logger.info("All indexes verified online (attempt %d)", attempt + 1)
                    return
                logger.info("Some indexes not ready, waiting... (attempt %d/10)", attempt + 1)
                time.sleep(5)
            logger.warning("Index verification timed out — some indexes may still be building")

        await asyncio.to_thread(_verify)

    def _col(self, name: str) -> CouchbaseCollection:
        """Get a CouchbaseCollection by its MongoDB collection name."""
        if name not in self._cache:
            scope_name, col_name = SCOPE_MAP.get(name, ("_default", name))
            self._cache[name] = CouchbaseCollection(
                self._cluster, self._bucket_name, scope_name, col_name
            )
        return self._cache[name]

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return self._col(name)

    def __getitem__(self, name):
        return self._col(name)
