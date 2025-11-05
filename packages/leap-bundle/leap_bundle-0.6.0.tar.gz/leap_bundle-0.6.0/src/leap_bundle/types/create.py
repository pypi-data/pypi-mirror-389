from typing import Optional

from pydantic import BaseModel, ConfigDict


class CreateBundleRequestBody(BaseModel):
    """In sync with apps/web/src/lib/bundle-requests/cli-types.ts"""

    model_config = ConfigDict(extra="ignore")

    input_path: str
    input_hash: str
    force_recreate: Optional[bool] = False
    quantization: Optional[str] = None
    model_type: Optional[str] = None
    cli_version: Optional[str] = None


class SignedUrlData(BaseModel):
    """Signed URL data returned by the API."""

    model_config = ConfigDict(extra="ignore")

    url: str
    fields: dict[str, str]
    path: str
    expirationSeconds: int


class StsCredentials(BaseModel):
    """STS credentials returned by the API."""

    model_config = ConfigDict(extra="ignore")

    access_key_id: str
    secret_access_key: str
    session_token: str
    expiration: str
    region: str
    bucket_name: str
    s3_prefix: str


class CreateBundleResponse(BaseModel):
    """In sync with apps/web/src/lib/bundle-requests/cli-types.ts"""

    model_config = ConfigDict(extra="ignore")

    new_request_id: int
    signed_url: SignedUrlData
    sts_credentials: StsCredentials


class ResumeBundleResponse(BaseModel):
    """In sync with apps/web/src/lib/bundle-requests/cli-types.ts"""

    model_config = ConfigDict(extra="ignore")

    signed_url: SignedUrlData
    sts_credentials: StsCredentials


class BundleRequestExistsResponse(BaseModel):
    """Response when a bundle request already exists."""

    model_config = ConfigDict(extra="ignore")

    message: str
