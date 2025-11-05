from __future__ import annotations
import mimetypes
from dataclasses import dataclass
from typing import Optional, Iterable
from pathlib import Path
from datetime import timedelta
import yaml
from google.cloud import storage
from .auth import get_credentials
from tqdm import tqdm

@dataclass
class UploadResult:
    bucket: str
    blob: str
    size: int
    generation: str


def _load_config():
    """Load configuration from config.yml"""
    config_path = Path(__file__).parent.parent.parent / "config.yml"
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
            return config
    return {}


class GCSClient:
    def __init__(
        self,
        project: Optional[str] = None,
        default_bucket: Optional[str] = None,
        create_bucket_if_missing: bool = False,
        location: Optional[str] = None,
        uniform_access: Optional[bool] = None,
    ):
        """
        project: GCP project ID (optional if resolved by ADC).
        default_bucket: default bucket (optional). Can be just the bucket name
                       (e.g., "sandbox-geosub") or bucket with default path/prefix
                       (e.g., "sandbox-geosub/Pruebas_ISSEC/TEST"). If not specified, uses config.yml.
        create_bucket_if_missing: creates the bucket if it doesn't exist.
        location: location when creating bucket (e.g., EU, US, europe-west1). If not specified, uses config.yml.
        uniform_access: enables Uniform bucket-level access. If not specified, uses config.yml.
        """
        config = _load_config()
        if default_bucket is None:
            default_bucket = config.get('default_bucket')
        if location is None:
            location = config.get('location', 'EU')
        if uniform_access is None:
            uniform_access = config.get('uniform_access', True)

        # Parse bucket path - can be "bucket" or "bucket/prefix/path"
        if default_bucket and '/' in default_bucket:
            self.bucket_name, self.default_prefix = default_bucket.split('/', 1)
            # Ensure default_prefix ends with '/' for proper path concatenation
            if self.default_prefix and not self.default_prefix.endswith('/'):
                self.default_prefix += '/'
        else:
            self.bucket_name = default_bucket
            self.default_prefix = ''

        creds = get_credentials()
        self.client = storage.Client(project=project, credentials=creds)
        self._ensure_bucket(self.bucket_name, create_bucket_if_missing, location, uniform_access)

    def _ensure_bucket(self, bucket_name, create, location, uniform):
        if not bucket_name or not create:
            return
        try:
            self.client.get_bucket(bucket_name)
        except Exception:
            bucket = storage.Bucket(self.client, bucket_name)
            bucket.location = location
            bucket.iam_configuration.uniform_bucket_level_access_enabled = uniform
            self.client.create_bucket(bucket)

    # --------- Basic Operations ----------
    def upload_file(
        self,
        local_path: str | Path,
        blob_path: str,
        bucket_name: Optional[str] = None,
        content_type: Optional[str] = None,
        make_public: bool = False,
        chunk_size: Optional[int] = None,
        show_progress: bool = True,
        metadata: Optional[dict] = None,
        cache_control: Optional[str] = None,
    ) -> UploadResult:
        """
        Uploads a file (resumable) with content-type detection.
        """
        config = _load_config()
        if chunk_size is None:
            chunk_size = config.get('chunk_size', 8 * 1024 * 1024)
        if cache_control is None:
            cache_control = config.get('cache_control', "public, max-age=3600")

        bucket_name = bucket_name or self.bucket_name
        if not bucket_name:
            raise ValueError("Specify bucket_name or configure default_bucket in the constructor.")

        # If no explicit bucket_name provided and we have a default_prefix, prepend it to blob_path
        if bucket_name == self.bucket_name and self.default_prefix and not blob_path.startswith(self.default_prefix.rstrip('/')):
            blob_path = self.default_prefix + blob_path

        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        blob.chunk_size = chunk_size
        blob.cache_control = cache_control

        if metadata:
            blob.metadata = metadata

        local_path = Path(local_path)
        size = local_path.stat().st_size

        if not content_type:
            content_type = mimetypes.guess_type(str(local_path))[0] or "application/octet-stream"

        with local_path.open("rb") as f:
            if show_progress and size > chunk_size:
                with tqdm(total=size, unit="B", unit_scale=True, desc=f"Uploading {local_path.name}") as pbar:
                    def _reader():
                        while True:
                            data = f.read(chunk_size)
                            if not data:
                                break
                            pbar.update(len(data))
                            yield data
                    blob.upload_from_file(_reader(), size=size, content_type=content_type, rewind=True)
            else:
                blob.upload_from_file(f, size=size, content_type=content_type, rewind=True)

        if make_public:
            blob.make_public()

        blob.reload()
        return UploadResult(bucket=bucket_name, blob=blob_path, size=size, generation=str(blob.generation))

    def download_file(
        self,
        blob_path: str,
        local_path: str | Path,
        bucket_name: Optional[str] = None,
    ) -> Path:
        bucket_name = bucket_name or self.bucket_name
        if not bucket_name:
            raise ValueError("Specify bucket_name or configure default_bucket.")
        
        # If no explicit bucket_name provided and we have a default_prefix, prepend it to blob_path
        if bucket_name == self.bucket_name and self.default_prefix and not blob_path.startswith(self.default_prefix.rstrip('/')):
            blob_path = self.default_prefix + blob_path
            
        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        blob.download_to_filename(str(local_path))
        return local_path

    def list(
        self,
        prefix: str = "",
        bucket_name: Optional[str] = None,
        recursive: bool = True,
    ) -> Iterable[str]:
        bucket_name = bucket_name or self.bucket_name
        if not bucket_name:
            raise ValueError("Specify bucket_name or configure default_bucket.")
        
        # If no explicit bucket_name provided and we have a default_prefix, prepend it to prefix
        if bucket_name == self.bucket_name and self.default_prefix:
            if prefix:
                prefix = self.default_prefix + prefix
            else:
                prefix = self.default_prefix
        
        blobs = self.client.list_blobs(bucket_name, prefix=prefix, delimiter=None if recursive else "/")
        for b in blobs:
            yield b.name

    def exists(self, blob_path: str, bucket_name: Optional[str] = None) -> bool:
        bucket_name = bucket_name or self.bucket_name
        if not bucket_name:
            raise ValueError("Specify bucket_name or configure default_bucket.")
        
        # If no explicit bucket_name provided and we have a default_prefix, prepend it to blob_path
        if bucket_name == self.bucket_name and self.default_prefix and not blob_path.startswith(self.default_prefix.rstrip('/')):
            blob_path = self.default_prefix + blob_path
            
        bucket = self.client.bucket(bucket_name)
        return bucket.blob(blob_path).exists()

    def delete(self, blob_path: str, bucket_name: Optional[str] = None) -> None:
        bucket_name = bucket_name or self.bucket_name
        if not bucket_name:
            raise ValueError("Specify bucket_name or configure default_bucket.")
        
        # If no explicit bucket_name provided and we have a default_prefix, prepend it to blob_path
        if bucket_name == self.bucket_name and self.default_prefix and not blob_path.startswith(self.default_prefix.rstrip('/')):
            blob_path = self.default_prefix + blob_path
            
        bucket = self.client.bucket(bucket_name)
        bucket.blob(blob_path).delete()

    def signed_url(
        self,
        blob_path: str,
        bucket_name: Optional[str] = None,
        expires: Optional[timedelta] = None,
        method: str = "GET",
        response_content_type: Optional[str] = None,
        response_disposition: Optional[str] = None,
    ) -> str:
        config = _load_config()
        if expires is None:
            expires_minutes = config.get('signed_url_expires_minutes', 15)
            expires = timedelta(minutes=expires_minutes)

        bucket_name = bucket_name or self.bucket_name
        if not bucket_name:
            raise ValueError("Specify bucket_name or configure default_bucket.")
        
        # If no explicit bucket_name provided and we have a default_prefix, prepend it to blob_path
        if bucket_name == self.bucket_name and self.default_prefix and not blob_path.startswith(self.default_prefix.rstrip('/')):
            blob_path = self.default_prefix + blob_path
            
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        return blob.generate_signed_url(
            version="v4",
            expiration=expires,
            method=method,
            response_type=response_content_type,
            response_disposition=response_disposition,
        )
