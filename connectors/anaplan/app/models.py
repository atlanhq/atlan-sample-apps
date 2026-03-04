from enum import Enum
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel


class AuthType(str, Enum):
    BASIC = "basic"
    CA_CERT = "ca_cert"


class AnaplanTokenInfo(BaseModel):
    tokenValue: str


class AnaplanAuthResponse(BaseModel):
    tokenInfo: AnaplanTokenInfo


class AnaplanCredentials(BaseModel):
    host: str = "us1a.app.anaplan.com"
    authType: AuthType = AuthType.BASIC
    username: Optional[str] = None
    password: Optional[str] = None
    extra: Union[str, Dict[str, Any]] = {}
    model_config = {"extra": "allow"}
