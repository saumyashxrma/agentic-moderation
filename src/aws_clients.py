import boto3
from src.config import config


def _base_kwargs():
    kwargs = {
        "region_name": config.AWS_REGION,
        "aws_access_key_id": config.AWS_ACCESS_KEY_ID,
        "aws_secret_access_key": config.AWS_SECRET_ACCESS_KEY,
    }
    if config.AWS_ENDPOINT_URL:
        kwargs["endpoint_url"] = config.AWS_ENDPOINT_URL
    return kwargs


def get_sqs_client():
    return boto3.client("sqs", **_base_kwargs())


def get_s3_client():
    return boto3.client("s3", **_base_kwargs())


def get_lambda_client():
    return boto3.client("lambda", **_base_kwargs())