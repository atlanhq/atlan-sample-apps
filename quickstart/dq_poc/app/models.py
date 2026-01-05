from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel, Field


@dataclass
class DqPocResult:
    """Final result of the dq poc sample application."""

    result: int = 0


class DqPocResponse(BaseModel):
    workflow_id: str
    run_id: str
    message: str
    started_at: str


class DqPocFormData(BaseModel):
    source_dq_database: Optional[str] = Field(default=None, alias="sourceDQDatabase")
    dmf_definition: Optional[str] = Field(default=None, alias="dmfDefinition")
    sql: Optional[str] = None
    connection_qualified_name: Optional[str] = Field(
        default=None, alias="connectionQualifiedName"
    )
    asset_qualified_name: Optional[str] = Field(
        default=None, alias="assetQualifiedName"
    )
    template_name: Optional[str] = Field(default=None, alias="templateName")
    custom_sql_result_type: Optional[str] = Field(
        default=None, alias="customSQLResultType"
    )


class DqPocRequest(BaseModel):
    credential_id: str = Field(alias="credentialId")
    form_data: DqPocFormData = Field(alias="formData")
