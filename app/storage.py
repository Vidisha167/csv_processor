import os
import time

import boto3
from botocore.exceptions import BotoCoreError, ClientError

BUCKET = os.environ["MINIO_BUCKET"]

s3 = boto3.client(
    "s3",
    endpoint_url=os.environ["MINIO_ENDPOINT"],
    aws_access_key_id=os.environ["MINIO_ACCESS_KEY"],
    aws_secret_access_key=os.environ["MINIO_SECRET_KEY"],
    region_name="us-east-1",
)


def ensure_bucket(retries: int = 10, delay: float = 2.0):
    """Create the bucket if missing. Retries because MinIO may still be starting."""
    for attempt in range(retries):
        try:
            s3.head_bucket(Bucket=BUCKET)
            return
        except ClientError as e:
            if e.response["Error"]["Code"] in ("404", "NoSuchBucket", "NotFound"):
                s3.create_bucket(Bucket=BUCKET)
                return
            raise
        except BotoCoreError:
            if attempt == retries - 1:
                raise
            time.sleep(delay)


def upload_file(fileobj, key: str):
    """Stream a file-like object to MinIO without loading it all into memory."""
    s3.upload_fileobj(fileobj, BUCKET, key)

def download_file(key: str):
    """Download an object from MinIO into an in-memory buffer."""
    from io import BytesIO

    buf = BytesIO()
    s3.download_fileobj(BUCKET, key, buf)
    buf.seek(0)
    return buf