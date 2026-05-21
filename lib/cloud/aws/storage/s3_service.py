import boto3
from botocore.exceptions import NoCredentialsError, ClientError
import os

from config.config import settings

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.AWS_S3_BUCKET

    def upload_file(self, file_path, object_name=None):
        """
        Sube un archivo a un bucket de S3.
        """
        if object_name is None:
            object_name = os.path.basename(file_path)
        try:
            self.s3_client.upload_file(file_path, self.bucket_name, object_name)
            return True
        except (NoCredentialsError, ClientError) as e:
            print(f"Error al subir el archivo: {e}")
            return False

    def download_file(self, object_name, file_path):
        """
        Descarga un archivo desde un bucket de S3.
        """
        try:
            self.s3_client.download_file(self.bucket_name, object_name, file_path)
            return True
        except (NoCredentialsError, ClientError) as e:
            print(f"Error al descargar el archivo: {e}")
            return False
