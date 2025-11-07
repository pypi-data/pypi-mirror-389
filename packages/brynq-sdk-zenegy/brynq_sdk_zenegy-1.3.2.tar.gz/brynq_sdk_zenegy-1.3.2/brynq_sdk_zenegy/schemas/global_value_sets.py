# Generated schemas for tag: GlobalValueSets

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from uuid import UUID
from datetime import datetime

# Import EffectiveDate from global_values schema
from .global_values import EffectiveDate

# BrynQ Pandera DataFrame Model for Global Value Sets
from pandera.typing import Series
import pandera as pa
import pandas as pd
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class GlobalValueSetCreate(BaseModel):
    """Schema for creating global value sets - Based on Zalary.Models.GlobalValueSets.GlobalValueSetBaseDto."""
    name: str = Field(description="Global value set name", example="Overtime Set")
    number: str = Field(description="Global value set number/code", example="GVS-001")

    class Config:
        allow_population_by_field_name = True


class GlobalValueSetUpdate(BaseModel):
    """Schema for updating global value sets - Based on Zalary.Models.GlobalValueSets.GlobalValueSetUpdateRequest."""
    uid: Optional[str] = Field(default=None, description="Global value set UID", example="00000000-0000-0000-0000-000000000000")
    name: str = Field(description="Global value set name", example="Updated Overtime Set")
    number: str = Field(description="Global value set number/code", example="GVS-001-UPD")

    class Config:
        allow_population_by_field_name = True


class GlobalValueSetEmployeeAssignment(BaseModel):
    """Schema for managing employee assignments to global value sets."""
    add_employees: Optional[List[str]] = Field(alias="addEmployees", default=None, description="Array of employee UIDs to add", example=["00000000-0000-0000-0000-000000000000"])
    remove_employees: Optional[List[str]] = Field(alias="removeEmployees", default=None, description="Array of employee UIDs to remove", example=["00000000-0000-0000-0000-000000000000"])

    class Config:
        allow_population_by_field_name = True


class GlobalValueSetEmployeeAssignmentResponse(BaseModel):
    """Schema for employee assignment response."""
    is_assignment_success: Optional[bool] = Field(alias="isAssignmentSuccess", default=None, description="Whether assignment was successful", example=True)
    is_assignment_partial_success: Optional[bool] = Field(alias="isAssignmentPartialSuccess", default=None, description="Whether assignment was partially successful", example=True)
    is_removal_success: Optional[bool] = Field(alias="isRemovalSuccess", default=None, description="Whether removal was successful", example=True)
    assignment_operation_message: Optional[str] = Field(alias="assignmentOperationMessage", default=None, description="Assignment operation message", example="string")
    removal_operation_message: Optional[str] = Field(alias="removalOperationMessage", default=None, description="Removal operation message", example="string")
    has_employees_with_overlapping_values: Optional[bool] = Field(alias="hasEmployeesWithOverlappingValues", default=None, description="Whether there are employees with overlapping values", example=True)

    class Config:
        allow_population_by_field_name = True


class RemoveGlobalValuesFromSetRequest(BaseModel):
    """Schema for removing global values from global value set."""
    global_value_uids: List[UUID] = Field(description="Array of global value UIDs to remove from the set", example=["00000000-0000-0000-0000-000000000000"])

    class Config:
        allow_population_by_field_name = True


class GetAssignedEmployeesRequest(BaseModel):
    """Schema for getting assigned employees with filters."""
    skip: Optional[int] = Field(default=0, description="Pagination offset", example=0)
    take: Optional[int] = Field(default=50, description="Pagination limit", example=50)
    search: Optional[str] = Field(default=None, description="Search term for employee name/number", example="John")
    department_uids: Optional[List[str]] = Field(alias="departmentUids", default=None, description="Filter by department UIDs", example=["00000000-0000-0000-0000-000000000000"])
    salary_payout_periods: Optional[List[int]] = Field(alias="salaryPayoutPeriods", default=None, description="Filter by salary payout periods", example=[0, 1, 2])
    salary_types: Optional[List[int]] = Field(alias="salaryTypes", default=None, description="Filter by salary types", example=[0, 1, 2])
    assignment_status: Optional[List[int]] = Field(alias="assignmentStatus", default=None, description="Filter by assignment status", example=[0, 1])
    employee_sort_by: Optional[int] = Field(alias="employeeSortBy", default=1, description="Sort employees by field", example=1)

    class Config:
        allow_population_by_field_name = True


class CompanyDepartmentBaseDto(BaseModel):
    """Schema for company department base information."""
    name: Optional[str] = Field(default=None, description="Department name", example="Sales")
    number: Optional[str] = Field(default=None, description="Department number/code", example="DEPT-001")
    has_work_schema: Optional[bool] = Field(alias="hasWorkSchema", default=None, description="Whether department has work schema", example=True)
    id: Optional[int] = Field(default=None, description="Department ID", example=1)
    uid: Optional[str] = Field(default=None, description="Department UID", example="00000000-0000-0000-0000-000000000000")

    class Config:
        allow_population_by_field_name = True


class EmployeesGlobalValueSetDto(BaseModel):
    """Schema for employee information in global value set context."""
    department: Optional[CompanyDepartmentBaseDto] = Field(default=None, description="Employee department information")
    salary_type: Optional[int] = Field(alias="salaryType", default=None, description="Employee salary type", example=1)
    salary_payout_period: Optional[int] = Field(alias="salaryPayoutPeriod", default=None, description="Employee salary payout period", example=1)
    photo_url: Optional[str] = Field(alias="photoUrl", default=None, description="Employee photo URL", example="https://example.com/photo.jpg")
    status_in_set: Optional[str] = Field(alias="statusInSet", default=None, description="Employee status in the set", example="Assigned")
    name: Optional[str] = Field(default=None, description="Employee name", example="John Doe")
    employee_number: Optional[str] = Field(alias="employeeNumber", default=None, description="Employee number", example="EMP-001")
    id: Optional[int] = Field(default=None, description="Employee ID", example=1)
    uid: Optional[str] = Field(default=None, description="Employee UID", example="00000000-0000-0000-0000-000000000000")

    class Config:
        allow_population_by_field_name = True


class GetAssignedEmployeesResponse(BaseModel):
    """Schema for get assigned employees response."""
    total_records: Optional[int] = Field(alias="totalRecords", default=None, description="Total number of records", example=100)
    total_display_records: Optional[int] = Field(alias="totalDisplayRecords", default=None, description="Total display records", example=50)
    data: Optional[List[EmployeesGlobalValueSetDto]] = Field(default=None, description="Array of employee data")

    class Config:
        allow_population_by_field_name = True


class AddCompanyGlobalValueRequest(BaseModel):
    """Schema for adding a company global value to a global value set."""
    is_date_managed: Optional[bool] = Field(alias="isDateManaged", default=None, description="Whether the value is date managed", example=True)

    class Config:
        allow_population_by_field_name = True


class GlobalValueSetsGet(BrynQPanderaDataFrameModel):
    """Flattened schema for Zenegy Global Value Sets Output data"""
    id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Global value set ID", alias="id")
    uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Global value set UID", alias="uid")
    name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Global value set name", alias="name")
    number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Global value set number", alias="number")
    number_of_employees: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Number of employees", alias="numberOfEmployees")
    number_of_global_values: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Number of global values", alias="numberOfGlobalValues")

    class _Annotation:
        primary_key = "uid"
        foreign_keys = {}


class AssignedEmployeesGet(BrynQPanderaDataFrameModel):
    """Flattened schema for assigned employees in global value set context"""
    # Employee fields
    id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee ID", alias="id")
    uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee UID", alias="uid")
    name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee name", alias="name")
    employee_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee number", alias="employeeNumber")
    salary_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee salary type", alias="salaryType")
    salary_payout_period: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee salary payout period", alias="salaryPayoutPeriod")
    photo_url: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee photo URL", alias="photoUrl")
    status_in_set: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee status in the set", alias="statusInSet")

    # Department fields (normalized)
    department_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Department name", alias="department__name")
    department_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Department number", alias="department__number")
    department_has_work_schema: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Department has work schema", alias="department__hasWorkSchema")
    department_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Department ID", alias="department__id")
    department_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Department UID", alias="department__uid")

    class _Annotation:
        primary_key = "uid"
        foreign_keys = {}


class CompanyGlobalValuesGet(BrynQPanderaDataFrameModel):
    """Flattened schema for company global values in global value set context"""
    # Basic global value fields
    id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Global value ID", alias="id")
    uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Global value UID", alias="uid")
    name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Global value name", alias="name")
    number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Global value number", alias="number")
    type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Global value type", alias="type")
    value: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Global value", alias="value")
    is_used_in_set: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is used in set", alias="isUsedInSet")
    has_employees: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Has employees", alias="hasEmployees")
    number_of_employees: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Number of employees", alias="numberOfEmployees")
    is_date_managed: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is date managed", alias="isDateManaged")

    # EffectiveFrom and EffectiveTo fields - handle as direct fields since they can be None
    effective_from: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Effective from", alias="effectiveFrom")
    effective_to: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Effective to", alias="effectiveTo")

    class _Annotation:
        primary_key = "uid"
        foreign_keys = {}
