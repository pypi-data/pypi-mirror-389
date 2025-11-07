# Generated schemas for tag: Companies

from pydantic import BaseModel, Field, RootModel
from typing import Dict, List, Optional, Any
from uuid import UUID

# BrynQ Pandera DataFrame Model for Companies
from pandera.typing import Series
import pandera as pa
import pandas as pd
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class CompaniesGet(BrynQPanderaDataFrameModel):
    """Flattened schema for Zenegy Companies Output data"""
    # Basic company fields
    user_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="User ID", alias="userId")
    employee_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee UID", alias="employeeUid")
    vat_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="VAT number", alias="vatNumber")
    is_valid: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is valid flag", alias="isValid")
    purpose_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Purpose type", alias="purposeType")
    status: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Status", alias="status")
    source: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Source", alias="source")
    area: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Area", alias="area")
    id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Company ID", alias="id")
    uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company UID", alias="uid")
    name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company name", alias="name")
    logo_url: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Logo URL", alias="logoUrl")

    # Roles, products, and modules (as JSON strings since they are lists)
    roles: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Roles list", alias="roles")
    products: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Products list", alias="products")
    modules: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Modules list", alias="modules")

    # Override app scopes (as JSON string since it's a list of objects)
    override_app_scopes: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Override app scopes", alias="overrideAppScopes")

    # Identity providers (as JSON string since it's a list of objects)
    identity_providers: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Identity providers", alias="identityProviders")

    class _Annotation:
        primary_key = "uid"
        foreign_keys = {}
