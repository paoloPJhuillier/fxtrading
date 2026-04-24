"""
Switchable storage abstraction layer.

Supports:
  - "emergent"  : Emergent Object Storage (cloud dev environment)
  - "s3"        : Any S3-compatible store (Huawei OBS, AWS S3, MinIO, etc.)

Controlled by STORAGE_TYPE env var.
"""

import os
import logging
from abc import ABC, abstractmethod

import boto3
from botocore.config import Config as BotoConfig
import requests as http_requests

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Common interface every storage backend must implement."""

    @abstractmethod
    def put_object(self, path: str, data: bytes, content_type: str) -> dict:
        ...

    @abstractmethod
    def get_object(self, path: str) -> tuple[bytes, str]:
        """Returns (data, content_type)."""
        ...

    @abstractmethod
    def delete_object(self, path: str) -> None:
        ...


# ── Emergent Object Storage ──────────────────────────────────────────────────

class EmergentStorage(StorageBackend):
    STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"

    def __init__(self):
        self._key: str | None = None
        self._emergent_key = os.environ.get("EMERGENT_LLM_KEY")

    def _init_key(self) -> str:
        if self._key:
            return self._key
        resp = http_requests.post(
            f"{self.STORAGE_URL}/init",
            json={"emergent_key": self._emergent_key},
            timeout=30,
        )
        resp.raise_for_status()
        self._key = resp.json()["storage_key"]
        return self._key

    def put_object(self, path: str, data: bytes, content_type: str) -> dict:
        key = self._init_key()
        resp = http_requests.put(
            f"{self.STORAGE_URL}/objects/{path}",
            headers={"X-Storage-Key": key, "Content-Type": content_type},
            data=data,
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()

    def get_object(self, path: str) -> tuple[bytes, str]:
        key = self._init_key()
        resp = http_requests.get(
            f"{self.STORAGE_URL}/objects/{path}",
            headers={"X-Storage-Key": key},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.content, resp.headers.get("Content-Type", "application/octet-stream")

    def delete_object(self, path: str) -> None:
        key = self._init_key()
        try:
            http_requests.delete(
                f"{self.STORAGE_URL}/objects/{path}",
                headers={"X-Storage-Key": key},
                timeout=30,
            )
        except Exception as exc:
            logger.warning("Emergent delete failed (non-critical): %s", exc)


# ── S3-Compatible Storage (Huawei OBS / AWS / MinIO) ─────────────────────────

class S3Storage(StorageBackend):
    def __init__(self):
        self._bucket = os.environ["S3_BUCKET_NAME"]
        self._client = boto3.client(
            "s3",
            endpoint_url=os.environ.get("S3_ENDPOINT_URL"),
            aws_access_key_id=os.environ["S3_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["S3_SECRET_ACCESS_KEY"],
            region_name=os.environ.get("S3_REGION", ""),
            config=BotoConfig(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
            ),
        )
        logger.info(
            "S3Storage initialized — endpoint=%s bucket=%s",
            os.environ.get("S3_ENDPOINT_URL", "default"),
            self._bucket,
        )

    def put_object(self, path: str, data: bytes, content_type: str) -> dict:
        self._client.put_object(
            Bucket=self._bucket,
            Key=path,
            Body=data,
            ContentType=content_type,
        )
        return {"path": path, "bucket": self._bucket}

    def get_object(self, path: str) -> tuple[bytes, str]:
        resp = self._client.get_object(Bucket=self._bucket, Key=path)
        data = resp["Body"].read()
        ct = resp.get("ContentType", "application/octet-stream")
        return data, ct

    def delete_object(self, path: str) -> None:
        try:
            self._client.delete_object(Bucket=self._bucket, Key=path)
        except Exception as exc:
            logger.warning("S3 delete failed (non-critical): %s", exc)


# ── Factory ──────────────────────────────────────────────────────────────────

_instance: StorageBackend | None = None


def get_storage() -> StorageBackend:
    """Return a singleton storage backend based on STORAGE_TYPE env var."""
    global _instance
    if _instance is not None:
        return _instance

    storage_type = os.environ.get("STORAGE_TYPE", "emergent").lower()

    if storage_type == "s3":
        _instance = S3Storage()
    else:
        _instance = EmergentStorage()

    logger.info("Storage backend: %s", type(_instance).__name__)
    return _instance
