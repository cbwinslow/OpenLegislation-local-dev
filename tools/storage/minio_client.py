"""Utility helpers for archiving raw payloads to MinIO/S3."""
from __future__ import annotations

import json
import os
import logging
from typing import Any, Dict

try:  # Optional dependency
    import orjson
except ImportError:  # pragma: no cover - fallback
    orjson = None

try:  # optional
    from minio import Minio
except ImportError:  # pragma: no cover
    Minio = None

logger = logging.getLogger(__name__)

_CLIENT = None


def _get_client():
    global _CLIENT  # noqa: PLW0603
    if _CLIENT is not None:
        return _CLIENT
    if not os.getenv("ARCHIVE_RAW_PAYLOADS"):
        return None
    if Minio is None:
        logger.warning("MinIO client not installed; skipping archival")
        return None
    endpoint = os.getenv("MINIO_ENDPOINT")
    access_key = os.getenv("MINIO_ACCESS_KEY")
    secret_key = os.getenv("MINIO_SECRET_KEY")
    secure = os.getenv("MINIO_SECURE", "true").lower() == "true"
    if not all([endpoint, access_key, secret_key]):
        logger.warning("MinIO configuration incomplete; skipping archival")
        return None
    _CLIENT = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
    return _CLIENT


def archive_json_payload(bucket: str, key: str, payload: Dict[str, Any]) -> None:
    client = _get_client()
    if client is None:
        return
    data = (orjson.dumps(payload) if orjson else json.dumps(payload).encode("utf-8"))
    try:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
    except Exception:  # pragma: no cover - race condition acceptable
        pass
    client.put_object(bucket, key, data=bytes(data), length=len(data), content_type="application/json")
    logger.debug("Archived payload to %s/%s", bucket, key)
