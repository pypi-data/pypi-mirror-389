# Generated schemas for tag: CompanyCostCenter

from pydantic import BaseModel, Field, RootModel
from typing import Dict, List, Optional, Any
from uuid import UUID

from pandera.typing import Series
import pandera as pa
import pandas as pd
from brynq_sdk_functions import BrynQPanderaDataFrameModel


class CostCenterCreate(BaseModel):
    cost_center_name: str = Field(
        alias="costCenterName",
        description="Cost center display name",
        example="Finance"
    )
    cost_center_code: str = Field(
        alias="costCenterCode",
        description="Cost center code",
        example="FIN"
    )
    type: str = Field(
        description="Cost center type/category",
        example="department"
    )
    employee_uids: Optional[List[UUID]] = Field(
        alias="employeeUids", default=None,
        description="List of employee UIDs assigned to the cost center",
        example=["00000000-0000-0000-0000-000000000000"]
    )

    class Config:
        populate_by_name = True


class CostCentersGet(BrynQPanderaDataFrameModel):
    """Flattened schema for Zenegy Cost Centers Output data"""
    cost_center_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Cost center name", alias="costCenterName")
    cost_center_code: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Cost center code", alias="costCenterCode")
    type: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Cost center type", alias="type")
    id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Cost center ID", alias="id")
    uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Cost center UID", alias="uid")

    class _Annotation:
        primary_key = "uid"
        foreign_keys = {}
