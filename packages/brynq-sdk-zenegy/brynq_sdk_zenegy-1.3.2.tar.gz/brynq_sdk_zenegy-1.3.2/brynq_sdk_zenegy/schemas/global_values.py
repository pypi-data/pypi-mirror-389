# Generated schemas for tag: GlobalValues

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime

class EffectiveDate(BaseModel):
    effective_date: Optional[str] = Field(alias="effectiveDate", default=None, description="Effective date in ISO format", example="2025-08-26T10:37:46.223Z")
    type: Optional[str] = Field(alias="type", default=None, description="Type", example="string")
    point: Optional[str] = Field(alias="point", default=None, description="Point", example="string")
    unit: Optional[str] = Field(alias="unit", default=None, description="Unit", example="string")
    amount: Optional[int] = Field(alias="amount", default=None, description="Amount", example=0)
    condition_point: Optional[str] = Field(alias="conditionPoint", default=None, description="Condition point", example="string")
    condition_amount: Optional[int] = Field(alias="conditionAmount", default=None, description="Condition amount", example=0)

    class Config:
        allow_population_by_field_name = True


class CompanyGlobalValueCreate(BaseModel):
    """Schema for creating global values."""
    name: str = Field(description="Global value name", example="Overtime Rate")
    number: str = Field(description="Global value number/code", example="GV-001")
    global_value_type: int = Field(alias="type", description="Global value type", example=1)
    value: str = Field(description="Global value value", example="1.5")
    is_used_in_set: Optional[bool] = Field(alias="isUsedInSet", default=None, description="Is used in set", example=True)
    has_employees: Optional[bool] = Field(alias="hasEmployees", default=None, description="Has employees", example=True)
    number_of_employees: Optional[int] = Field(alias="numberOfEmployees", default=None, description="Number of employees", example=0)
    is_date_managed: Optional[bool] = Field(alias="isDateManaged", default=None, description="Is date managed", example=True)
    effective_from: Optional[EffectiveDate] = Field(alias="effectiveFrom", default=None, description="Effective from date")
    effective_to: Optional[EffectiveDate] = Field(alias="effectiveTo", default=None, description="Effective to date")

    # Flat field alternatives for effective_from
    effective_from_effective_date: Optional[str] = Field(default=None, description="Effective from date in ISO format", example="2025-08-26T10:37:46.223Z")
    effective_from_type: Optional[str] = Field(default=None, description="Effective from type", example="string")
    effective_from_point: Optional[str] = Field(default=None, description="Effective from point", example="string")
    effective_from_unit: Optional[str] = Field(default=None, description="Effective from unit", example="string")
    effective_from_amount: Optional[int] = Field(default=None, description="Effective from amount", example=0)
    effective_from_condition_point: Optional[str] = Field(default=None, description="Effective from condition point", example="string")
    effective_from_condition_amount: Optional[int] = Field(default=None, description="Effective from condition amount", example=0)

    # Flat field alternatives for effective_to
    effective_to_effective_date: Optional[str] = Field(default=None, description="Effective to date in ISO format", example="2025-08-26T10:37:46.223Z")
    effective_to_type: Optional[str] = Field(default=None, description="Effective to type", example="string")
    effective_to_point: Optional[str] = Field(default=None, description="Effective to point", example="string")
    effective_to_unit: Optional[str] = Field(default=None, description="Effective to unit", example="string")
    effective_to_amount: Optional[int] = Field(default=None, description="Effective to amount", example=0)
    effective_to_condition_point: Optional[str] = Field(default=None, description="Effective to condition point", example="string")
    effective_to_condition_amount: Optional[int] = Field(default=None, description="Effective to condition amount", example=0)

    def model_dump(self, **kwargs):
        """Override model_dump to build nested structure from flat fields"""
        data = super().model_dump(**kwargs)

        # Build effectiveFrom if any flat fields are present
        effective_from_fields = {
            'effectiveDate': data.pop('effective_from_effective_date', None),
            'type': data.pop('effective_from_type', None),
            'point': data.pop('effective_from_point', None),
            'unit': data.pop('effective_from_unit', None),
            'amount': data.pop('effective_from_amount', None),
            'conditionPoint': data.pop('effective_from_condition_point', None),
            'conditionAmount': data.pop('effective_from_condition_amount', None)
        }

        # Only add effectiveFrom if at least one field has a value
        if any(v is not None for v in effective_from_fields.values()):
            # Remove None values
            effective_from_fields = {k: v for k, v in effective_from_fields.items() if v is not None}
            if effective_from_fields:
                data['effectiveFrom'] = effective_from_fields

        # Build effectiveTo if any flat fields are present
        effective_to_fields = {
            'effectiveDate': data.pop('effective_to_effective_date', None),
            'type': data.pop('effective_to_type', None),
            'point': data.pop('effective_to_point', None),
            'unit': data.pop('effective_to_unit', None),
            'amount': data.pop('effective_to_amount', None),
            'conditionPoint': data.pop('effective_to_condition_point', None),
            'conditionAmount': data.pop('effective_to_condition_amount', None)
        }

        # Only add effectiveTo if at least one field has a value
        if any(v is not None for v in effective_to_fields.values()):
            # Remove None values
            effective_to_fields = {k: v for k, v in effective_to_fields.items() if v is not None}
            if effective_to_fields:
                data['effectiveTo'] = effective_to_fields

        return data

    class Config:
        allow_population_by_field_name = True


class CompanyGlobalValueResponse(BaseModel):
    """Schema for global values response with all fields."""
    id: Optional[int] = Field(default=None, description="Global value ID", example=0)
    uid: Optional[UUID] = Field(default=None, description="Global value UID", example="00000000-0000-0000-0000-000000000000")
    name: Optional[str] = Field(default=None, description="Global value name", example="Overtime Rate")
    number: Optional[str] = Field(default=None, description="Global value number/code", example="GV-001")
    type: Optional[int] = Field(default=None, description="Global value type", example=1)
    value: Optional[str] = Field(default=None, description="Global value value", example="1.5")
    is_used_in_set: Optional[bool] = Field(alias="isUsedInSet", default=None, description="Is used in set", example=True)
    has_employees: Optional[bool] = Field(alias="hasEmployees", default=None, description="Has employees", example=True)
    number_of_employees: Optional[int] = Field(alias="numberOfEmployees", default=None, description="Number of employees", example=0)
    is_date_managed: Optional[bool] = Field(alias="isDateManaged", default=None, description="Is date managed", example=True)
    effective_from: Optional[EffectiveDate] = Field(alias="effectiveFrom", default=None, description="Effective from date")
    effective_to: Optional[EffectiveDate] = Field(alias="effectiveTo", default=None, description="Effective to date")

    class Config:
        allow_population_by_field_name = True


class CompanyGlobalValueUpdate(BaseModel):
    """Schema for updating global values - Based on Zalary.Models.GlobalValues.CompanyGlobalValueUpdateRequest."""
    uid: Optional[str] = Field(default=None, description="Global value UID", example="00000000-0000-0000-0000-000000000000")
    name: str = Field(description="Global value name", example="Overtime Rate")
    number: str = Field(description="Global value number/code", example="GV-001")
    global_value_type: int = Field(alias="type", description="Global value type", example=1)
    value: str = Field(description="Global value value", example="1.5")
    is_used_in_set: Optional[bool] = Field(alias="isUsedInSet", default=None, description="Is used in set", example=True)
    has_employees: Optional[bool] = Field(alias="hasEmployees", default=None, description="Has employees", example=True)
    number_of_employees: Optional[int] = Field(alias="numberOfEmployees", default=None, description="Number of employees", example=0)
    is_date_managed: Optional[bool] = Field(alias="isDateManaged", default=None, description="Is date managed", example=True)
    effective_from: Optional[EffectiveDate] = Field(alias="effectiveFrom", default=None, description="Effective from date")
    effective_to: Optional[EffectiveDate] = Field(alias="effectiveTo", default=None, description="Effective to date")

    # Flat field alternatives for effective_from
    effective_from_effective_date: Optional[str] = Field(default=None, description="Effective from date in ISO format", example="2025-08-26T10:37:46.223Z")
    effective_from_type: Optional[str] = Field(default=None, description="Effective from type", example="string")
    effective_from_point: Optional[str] = Field(default=None, description="Effective from point", example="string")
    effective_from_unit: Optional[str] = Field(default=None, description="Effective from unit", example="string")
    effective_from_amount: Optional[int] = Field(default=None, description="Effective from amount", example=0)
    effective_from_condition_point: Optional[str] = Field(default=None, description="Effective from condition point", example="string")
    effective_from_condition_amount: Optional[int] = Field(default=None, description="Effective from condition amount", example=0)

    # Flat field alternatives for effective_to
    effective_to_effective_date: Optional[str] = Field(default=None, description="Effective to date in ISO format", example="2025-08-26T10:37:46.223Z")
    effective_to_type: Optional[str] = Field(default=None, description="Effective to type", example="string")
    effective_to_point: Optional[str] = Field(default=None, description="Effective to point", example="string")
    effective_to_unit: Optional[str] = Field(default=None, description="Effective to unit", example="string")
    effective_to_amount: Optional[int] = Field(default=None, description="Effective to amount", example=0)
    effective_to_condition_point: Optional[str] = Field(default=None, description="Effective to condition point", example="string")
    effective_to_condition_amount: Optional[int] = Field(default=None, description="Effective to condition amount", example=0)

    def model_dump(self, **kwargs):
        """Override model_dump to build nested structure from flat fields"""
        data = super().model_dump(**kwargs)

        # Build effectiveFrom if any flat fields are present
        effective_from_fields = {
            'effectiveDate': data.pop('effective_from_effective_date', None),
            'type': data.pop('effective_from_type', None),
            'point': data.pop('effective_from_point', None),
            'unit': data.pop('effective_from_unit', None),
            'amount': data.pop('effective_from_amount', None),
            'conditionPoint': data.pop('effective_from_condition_point', None),
            'conditionAmount': data.pop('effective_from_condition_amount', None)
        }

        # Only add effectiveFrom if at least one field has a value
        if any(v is not None for v in effective_from_fields.values()):
            # Remove None values
            effective_from_fields = {k: v for k, v in effective_from_fields.items() if v is not None}
            if effective_from_fields:
                data['effectiveFrom'] = effective_from_fields

        # Build effectiveTo if any flat fields are present
        effective_to_fields = {
            'effectiveDate': data.pop('effective_to_effective_date', None),
            'type': data.pop('effective_to_type', None),
            'point': data.pop('effective_to_point', None),
            'unit': data.pop('effective_to_unit', None),
            'amount': data.pop('effective_to_amount', None),
            'conditionPoint': data.pop('effective_to_condition_point', None),
            'conditionAmount': data.pop('effective_to_condition_amount', None)
        }

        # Only add effectiveTo if at least one field has a value
        if any(v is not None for v in effective_to_fields.values()):
            # Remove None values
            effective_to_fields = {k: v for k, v in effective_to_fields.items() if v is not None}
            if effective_to_fields:
                data['effectiveTo'] = effective_to_fields

        return data

    class Config:
        allow_population_by_field_name = True


class GlobalValueAssign(BaseModel):
    """Schema for assigning global values to employees - Based on Zalary.Models.GlobalValues.AddEmployeesGlobalValueRequest."""
    is_date_managed: Optional[bool] = Field(alias="isDateManaged", default=None, description="Is date managed", example=True)
    effective_from: Optional[EffectiveDate] = Field(alias="effectiveFrom", default=None, description="Effective from date")
    effective_to: Optional[EffectiveDate] = Field(alias="effectiveTo", default=None, description="Effective to date")
    employee_uids: Optional[List[str]] = Field(alias="employeeUids", default=None, description="Array of employee UIDs to assign", example=["00000000-0000-0000-0000-000000000000"])

    # Flat field alternatives for effective_from
    effective_from_effective_date: Optional[str] = Field(default=None, description="Effective from date in ISO format", example="2025-08-26T10:37:46.223Z")
    effective_from_type: Optional[str] = Field(default=None, description="Effective from type", example="string")
    effective_from_point: Optional[str] = Field(default=None, description="Effective from point", example="string")
    effective_from_unit: Optional[str] = Field(default=None, description="Effective from unit", example="string")
    effective_from_amount: Optional[int] = Field(default=None, description="Effective from amount", example=0)
    effective_from_condition_point: Optional[str] = Field(default=None, description="Effective from condition point", example="string")
    effective_from_condition_amount: Optional[int] = Field(default=None, description="Effective from condition amount", example=0)

    # Flat field alternatives for effective_to
    effective_to_effective_date: Optional[str] = Field(default=None, description="Effective to date in ISO format", example="2025-08-26T10:37:46.223Z")
    effective_to_type: Optional[str] = Field(default=None, description="Effective to type", example="string")
    effective_to_point: Optional[str] = Field(default=None, description="Effective to point", example="string")
    effective_to_unit: Optional[str] = Field(default=None, description="Effective to unit", example="string")
    effective_to_amount: Optional[int] = Field(default=None, description="Effective to amount", example=0)
    effective_to_condition_point: Optional[str] = Field(default=None, description="Effective to condition point", example="string")
    effective_to_condition_amount: Optional[int] = Field(default=None, description="Effective to condition amount", example=0)

    def model_dump(self, **kwargs):
        """Override model_dump to build nested structure from flat fields"""
        data = super().model_dump(**kwargs)

        # Build effectiveFrom if any flat fields are present
        effective_from_fields = {
            'effectiveDate': data.pop('effective_from_effective_date', None),
            'type': data.pop('effective_from_type', None),
            'point': data.pop('effective_from_point', None),
            'unit': data.pop('effective_from_unit', None),
            'amount': data.pop('effective_from_amount', None),
            'conditionPoint': data.pop('effective_from_condition_point', None),
            'conditionAmount': data.pop('effective_from_condition_amount', None)
        }

        # Only add effectiveFrom if at least one field has a value
        if any(v is not None for v in effective_from_fields.values()):
            # Remove None values
            effective_from_fields = {k: v for k, v in effective_from_fields.items() if v is not None}
            if effective_from_fields:
                data['effectiveFrom'] = effective_from_fields

        # Build effectiveTo if any flat fields are present
        effective_to_fields = {
            'effectiveDate': data.pop('effective_to_effective_date', None),
            'type': data.pop('effective_to_type', None),
            'point': data.pop('effective_to_point', None),
            'unit': data.pop('effective_to_unit', None),
            'amount': data.pop('effective_to_amount', None),
            'conditionPoint': data.pop('effective_to_condition_point', None),
            'conditionAmount': data.pop('effective_to_condition_amount', None)
        }

        # Only add effectiveTo if at least one field has a value
        if any(v is not None for v in effective_to_fields.values()):
            # Remove None values
            effective_to_fields = {k: v for k, v in effective_to_fields.items() if v is not None}
            if effective_to_fields:
                data['effectiveTo'] = effective_to_fields

        return data

    class Config:
        allow_population_by_field_name = True



class GetGlobalValuesListPerCompanyAsyncRequest(BaseModel):
    skip: Optional[int] = Field(default=None, description="Pagination offset", example=0)
    take: Optional[int] = Field(default=None, description="Pagination limit", example=50)
    search: Optional[str] = Field(default=None, description="Search term (name/number)", example="Overtime")
    types: Optional[List[int]] = Field(default=None, description="Filter by types", example=[1,2])
    override: Optional[int] = Field(default=None, description="Override filter flag", example=0)
    sortby: Optional[int] = Field(alias="sortBy", default=None, description="Sort by field code", example=1)
    employeeuids: Optional[List[UUID]] = Field(alias="employeeUids", default=None, description="Filter by employee UIDs", example=["00000000-0000-0000-0000-000000000000"])
    class Config:
        allow_population_by_field_name = True

class AssignEmployeesToGlobalValueAsyncRequest(BaseModel):
    isdatemanaged: Optional[bool] = Field(alias="isDateManaged", default=None, description="Whether value is date managed", example=False)
    effectivefrom: Optional[Dict[str, Any]] = Field(alias="effectiveFrom", default=None, description="Effective from date descriptor", example={"effectiveDate": "2024-01-01T00:00:00Z"})
    effectiveto: Optional[Dict[str, Any]] = Field(alias="effectiveTo", default=None, description="Effective to date descriptor", example={"effectiveDate": "2024-12-31T23:59:59Z"})
    employeeuids: Optional[List[UUID]] = Field(alias="employeeUids", default=None, description="Employee UIDs to assign", example=["00000000-0000-0000-0000-000000000000"])
    class Config:
        allow_population_by_field_name = True

class GetAssignedEmployeesToGlobalValueAsyncRequest(BaseModel):
    skip: Optional[int] = Field(default=None, description="Pagination offset", example=0)
    take: Optional[int] = Field(default=None, description="Pagination limit", example=50)
    search: Optional[str] = Field(default=None, description="Search term", example="John")
    departmentuids: Optional[List[str]] = Field(alias="departmentUids", default=None, description="Filter by department UIDs", example=["00000000-0000-0000-0000-000000000000"])
    salarypayoutperiods: Optional[List[int]] = Field(alias="salaryPayoutPeriods", default=None, description="Filter by salary payout periods", example=[1,2])
    salarytypes: Optional[List[int]] = Field(alias="salaryTypes", default=None, description="Filter by salary types", example=[1,2])
    filterby: Optional[int] = Field(alias="filterBy", default=None, description="Filter by code", example=0)
    employeesortby: Optional[int] = Field(alias="employeeSortBy", default=None, description="Sort by code", example=1)
    class Config:
        allow_population_by_field_name = True


# BrynQ Pandera DataFrame Model for Global Values
from pandera.typing import Series
import pandera as pa
import pandas as pd
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class GlobalValuesGet(BrynQPanderaDataFrameModel):
    """Flattened schema for Zenegy Global Values Output data"""
    # Basic global value fields
    id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Global value ID", alias="id")
    uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Global value UID", alias="uid")
    name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Global value name", alias="name")
    number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Global value number", alias="number")
    type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Global value type", alias="type")
    value: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Global value", alias="value")
    is_used_in_set: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is used in set", alias="isUsedInSet")
    is_date_managed: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is date managed", alias="isDateManaged")
    has_employees: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Has employees", alias="hasEmployees")
    number_of_employees: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Number of employees", alias="numberOfEmployees")

    # EffectiveFrom fields (normalized)
    effective_from_date: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Effective from date", alias="effectiveFrom__effectiveDate")
    effective_from_type: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Effective from type", alias="effectiveFrom__type")
    effective_from_point: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Effective from point", alias="effectiveFrom__point")
    effective_from_unit: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Effective from unit", alias="effectiveFrom__unit")
    effective_from_amount: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Effective from amount", alias="effectiveFrom__amount")
    effective_from_condition_point: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Effective from condition point", alias="effectiveFrom__conditionPoint")
    effective_from_condition_amount: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Effective from condition amount", alias="effectiveFrom__conditionAmount")

    # EffectiveTo fields (normalized)
    effective_to_date: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Effective to date", alias="effectiveTo__effectiveDate")
    effective_to_type: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Effective to type", alias="effectiveTo__type")
    effective_to_point: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Effective to point", alias="effectiveTo__point")
    effective_to_unit: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Effective to unit", alias="effectiveTo__unit")
    effective_to_amount: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Effective to amount", alias="effectiveTo__amount")
    effective_to_condition_point: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Effective to condition point", alias="effectiveTo__conditionPoint")
    effective_to_condition_amount: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Effective to condition amount", alias="effectiveTo__conditionAmount")

    class _Annotation:
        primary_key = "uid"
        foreign_keys = {}

class GlobalValueSetsGet(BrynQPanderaDataFrameModel):
    """Flattened schema for Zenegy Global Value Sets Output data"""
    # Global value set fields
    number_of_employees: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Number of employees", alias="numberOfEmployees")
    number_of_global_values: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Number of global values", alias="numberOfGlobalValues")
    uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Global value set UID", alias="uid")
    name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Global value set name", alias="name")
    number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Global value set number", alias="number")

    # When API returns value-level details in sets payload
    is_used_in_set: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is used in set", alias="isUsedInSet")
    is_date_managed: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is date managed", alias="isDateManaged")
    has_employees: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Has employees", alias="hasEmployees")

    # EffectiveFrom fields (normalized like GlobalValuesGet)
    effective_from_date: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Effective from date", alias="effectiveFrom__effectiveDate")
    effective_from_type: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Effective from type", alias="effectiveFrom__type")
    effective_from_point: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Effective from point", alias="effectiveFrom__point")
    effective_from_unit: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Effective from unit", alias="effectiveFrom__unit")
    effective_from_amount: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Effective from amount", alias="effectiveFrom__amount")
    effective_from_condition_point: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Effective from condition point", alias="effectiveFrom__conditionPoint")
    effective_from_condition_amount: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Effective from condition amount", alias="effectiveFrom__conditionAmount")

    # EffectiveTo fields (normalized like GlobalValuesGet)
    effective_to_date: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Effective to date", alias="effectiveTo__effectiveDate")
    effective_to_type: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Effective to type", alias="effectiveTo__type")
    effective_to_point: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Effective to point", alias="effectiveTo__point")
    effective_to_unit: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Effective to unit", alias="effectiveTo__unit")
    effective_to_amount: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Effective to amount", alias="effectiveTo__amount")
    effective_to_condition_point: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Effective to condition point", alias="effectiveTo__conditionPoint")
    effective_to_condition_amount: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Effective to condition amount", alias="effectiveTo__conditionAmount")

    class _Annotation:
        primary_key = "uid"
        foreign_keys = {}

class AssignedGlobalValuesGet(BrynQPanderaDataFrameModel):
    """Schema for getting assigned global values for an employee."""
    type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Global value type", alias="type")
    is_available_in_company: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is available in company", alias="isAvailableInCompany")
    is_employee_assigned: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is employee assigned", alias="isEmployeeAssigned")

    # CompanyGlobalValueReferenceUidsPairs fields (normalized)
    company_global_value_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company global value UID", alias="companyGlobalValueReferenceUidsPairs__companyGlobalValueUid")
    reference_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Reference UID", alias="companyGlobalValueReferenceUidsPairs__referenceUid")

    class _Annotation:
        primary_key = "company_global_value_uid"
        foreign_keys = {}


class AssignedEmployeesToGlobalValueGet(BrynQPanderaDataFrameModel):
    """Flattened schema for employees assigned to a global value"""
    # Basic employee fields
    id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee ID", alias="id")
    uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee UID", alias="uid")
    name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee name", alias="name")
    employee_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee number", alias="employeeNumber")
    extra_employee_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Extra employee number", alias="extraEmployeeNumber")
    title: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee title", alias="title")
    photo_url: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee photo URL", alias="photoUrl")
    has_profile_image: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Has profile image", alias="hasProfileImage")
    is_resigned: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is resigned", alias="isResigned")

    # Salary and employment details
    salary_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee salary type", alias="salaryType")
    salary_payout_period: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee salary payout period", alias="salaryPayoutPeriod")
    income_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee income type", alias="incomeType")
    holiday_pay_receiver_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Holiday pay receiver type", alias="holidayPayReceiverType")
    extra_holiday_entitlement_rule: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Extra holiday entitlement rule", alias="extraHolidayEntitlementRule")

    # Global value assignment details
    is_date_managed: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is date managed", alias="isDateManaged")
    effective_from: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Effective from date", alias="effectiveFrom")
    effective_to: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Effective to date", alias="effectiveTo")

    # Department fields (normalized)
    department_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Department ID", alias="department__id")
    department_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Department UID", alias="department__uid")
    department_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Department name", alias="department__name")
    department_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Department number", alias="department__number")
    department_has_work_schema: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Department has work schema", alias="department__hasWorkSchema")

    # User fields (normalized)
    user_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="User ID", alias="user__id")
    user_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="User UID", alias="user__uid")
    user_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="User name", alias="user__name")
    user_email: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="User email", alias="user__email")
    user_photo_url: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="User photo URL", alias="user__photoUrl")

    class _Annotation:
        primary_key = "uid"
        foreign_keys = {}
