"""FileStorageAdapter — S3/MinIO adapter for PDF file storage (Adapter pattern).

Stores uploaded PDF files with tenant-scoped paths: /{tenant_id}/{user_id}/{filename}.
Uses boto3 SDK compatible with both MinIO (dev) and AWS S3 (prod).
"""

# TODO(#64): Implement FileStorageAdapter with store() and retrieve() methods
# TODO(#65): Implement tenant-scoped path generation
