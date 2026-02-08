"""FileStorageAdapter — S3/MinIO adapter for PDF storage (Adapter pattern).

Stores files with tenant-scoped paths: {tenant_id}/{user_id}/{filename}.
Uses boto3 SDK compatible with both MinIO (dev) and AWS S3 (prod).
"""

import logging

import boto3  # type: ignore[import-untyped]
from botocore.exceptions import ClientError  # type: ignore[import-untyped]

from config import Settings

logger = logging.getLogger(__name__)


class FileStorageAdapter:
    """Manages file upload/download to S3-compatible storage."""

    def __init__(self, settings: Settings) -> None:
        self._bucket = settings.s3_bucket_name
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
        )
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        """Create the bucket if it does not exist."""
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except ClientError:
            try:
                logger.info("Creating bucket: %s", self._bucket)
                self._client.create_bucket(Bucket=self._bucket)
            except Exception:
                logger.warning(
                    "Could not create bucket %s (storage may not be available)",
                    self._bucket,
                )
        except Exception:
            logger.warning(
                "Could not connect to S3/MinIO (storage may not be available)"
            )

    def store(
        self,
        tenant_id: str,
        user_id: str,
        filename: str,
        file_bytes: bytes,
    ) -> str:
        """Upload a file to S3/MinIO.

        Args:
            tenant_id: Tenant UUID string for path isolation.
            user_id: User UUID string.
            filename: Original filename.
            file_bytes: Raw file content.

        Returns:
            The storage path (S3 object key).
        """
        key = f"{tenant_id}/{user_id}/{filename}"
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=file_bytes,
            ContentType="application/pdf",
        )
        logger.info("Stored file: %s/%s", self._bucket, key)
        return key

    def retrieve(self, storage_path: str) -> bytes:
        """Download a file from S3/MinIO.

        Args:
            storage_path: The S3 object key.

        Returns:
            The file content as bytes.
        """
        response = self._client.get_object(Bucket=self._bucket, Key=storage_path)
        data: bytes = response["Body"].read()
        return data

    def delete(self, storage_path: str) -> None:
        """Delete a file from S3/MinIO.

        Args:
            storage_path: The S3 object key to delete.
        """
        self._client.delete_object(Bucket=self._bucket, Key=storage_path)
        logger.info("Deleted file: %s/%s", self._bucket, storage_path)
