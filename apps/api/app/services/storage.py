"""
ByggSjekk – Object storage abstraction layer.

Provides:
  StorageAdapter     – abstract base class
  MinIOStorageAdapter – implementation using aiobotocore (S3-compatible)
  get_storage_adapter() – factory function
"""

from __future__ import annotations

import abc
from typing import BinaryIO

import aiobotocore.session
from botocore.exceptions import ClientError

from app.core.config import settings


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------


class StorageAdapter(abc.ABC):
    """Protocol for all storage back-ends."""

    @abc.abstractmethod
    async def upload(
        self,
        file: BinaryIO | bytes,
        key: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload *file* to *key* and return the storage key."""

    @abc.abstractmethod
    async def download(self, key: str) -> bytes:
        """Download the object at *key* and return its raw bytes."""

    @abc.abstractmethod
    async def delete(self, key: str) -> None:
        """Delete the object at *key*."""

    @abc.abstractmethod
    async def get_presigned_url(self, key: str, expires: int = 3600) -> str:
        """Return a pre-signed GET URL valid for *expires* seconds."""


# ---------------------------------------------------------------------------
# MinIO / S3 implementation
# ---------------------------------------------------------------------------


class MinIOStorageAdapter(StorageAdapter):
    """Async S3-compatible storage using aiobotocore."""

    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        use_ssl: bool = False,
    ) -> None:
        self._endpoint_url = (
            f"{'https' if use_ssl else 'http'}://{endpoint_url}"
        )
        self._access_key = access_key
        self._secret_key = secret_key
        self._bucket = bucket
        self._session = aiobotocore.session.AioSession()

    def _client(self):
        """Return a context-managed aiobotocore S3 client."""
        return self._session.create_client(
            "s3",
            endpoint_url=self._endpoint_url,
            aws_access_key_id=self._access_key,
            aws_secret_access_key=self._secret_key,
        )

    async def _ensure_bucket(self, client) -> None:
        try:
            await client.head_bucket(Bucket=self._bucket)
        except ClientError:
            await client.create_bucket(Bucket=self._bucket)

    async def upload(
        self,
        file: BinaryIO | bytes,
        key: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        body = file if isinstance(file, bytes) else file.read()
        async with self._client() as client:
            await self._ensure_bucket(client)
            await client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=body,
                ContentType=content_type,
            )
        return key

    async def download(self, key: str) -> bytes:
        async with self._client() as client:
            response = await client.get_object(Bucket=self._bucket, Key=key)
            async with response["Body"] as stream:
                return await stream.read()

    async def delete(self, key: str) -> None:
        async with self._client() as client:
            await client.delete_object(Bucket=self._bucket, Key=key)

    async def get_presigned_url(self, key: str, expires: int = 3600) -> str:
        async with self._client() as client:
            url: str = await client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": key},
                ExpiresIn=expires,
            )
        return url


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_storage_adapter: StorageAdapter | None = None


def get_storage_adapter() -> StorageAdapter:
    """Return (and cache) a storage adapter based on settings."""
    global _storage_adapter
    if _storage_adapter is None:
        _storage_adapter = MinIOStorageAdapter(
            endpoint_url=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            bucket=settings.MINIO_BUCKET,
            use_ssl=settings.MINIO_USE_SSL,
        )
    return _storage_adapter
