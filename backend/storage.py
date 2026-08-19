"""Almacenamiento de las fotos que sube la vendedora.

Con AWS_S3_BUCKET_NAME configurado, usa un bucket S3-compatible (persiste
entre deploys). Sin esa variable —el caso por default en desarrollo local—
cae a disco local, para no exigir credenciales de bucket solo para probar
el proyecto en la máquina.
"""
import os

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

BUCKET = os.environ.get("AWS_S3_BUCKET_NAME")


def habilitado():
    return bool(BUCKET)


def _cliente():
    return boto3.client(
        "s3",
        endpoint_url=os.environ["AWS_ENDPOINT_URL"],
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        region_name=os.environ.get("AWS_DEFAULT_REGION", "auto"),
        config=Config(s3={"addressing_style": "virtual"}),
    )


def guardar(key, datos, content_type):
    _cliente().put_object(Bucket=BUCKET, Key=key, Body=datos, ContentType=content_type)


def leer(key):
    """Regresa (bytes, content_type), o None si la llave no existe."""
    try:
        objeto = _cliente().get_object(Bucket=BUCKET, Key=key)
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") in ("NoSuchKey", "404"):
            return None
        raise
    return objeto["Body"].read(), objeto.get("ContentType") or "application/octet-stream"


def eliminar(key):
    try:
        _cliente().delete_object(Bucket=BUCKET, Key=key)
    except ClientError:
        # Si ya no existe (o el bucket no responde), no debe tumbar la
        # petición: el registro en la base de datos ya se borró.
        pass
