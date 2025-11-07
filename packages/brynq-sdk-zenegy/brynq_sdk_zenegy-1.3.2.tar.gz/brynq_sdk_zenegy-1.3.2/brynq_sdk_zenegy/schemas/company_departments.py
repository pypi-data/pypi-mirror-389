# Generated schemas for tag: CompanyDepartment

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from uuid import UUID


class ResponsiblePerson(BaseModel):
    """Schema for responsible person information."""
    income_type: Optional[int] = Field(alias="incomeType", default=None, description="Income type code", example=1)
    holiday_pay_receiver_type: Optional[int] = Field(alias="holidayPayReceiverType", default=None, description="Holiday pay receiver type code", example=2)
    extra_holiday_entitlement_rule: Optional[str] = Field(alias="extraHolidayEntitlementRule", default=None, description="Extra holiday entitlement rule name/code", example="RULE_A")
    name: Optional[str] = Field(default=None, description="Responsible person name", example="Jane Doe")
    employee_number: Optional[str] = Field(alias="employeeNumber", default=None, description="Employee number", example="E-2001")
    extra_employee_number: Optional[str] = Field(alias="extraEmployeeNumber", default=None, description="Secondary employee number", example="EXT-10")
    id: Optional[int] = Field(default=None, description="Internal numeric identifier", example=12)
    uid: Optional[UUID] = Field(example="00000000-0000-0000-0000-000000000000", default=None, description="Responsible person UID")

    class Config:
        populate_by_name = True


class CompanyWorkSchema(BaseModel):
    """Schema for company work schema information."""
    name: Optional[str] = Field(default=None, description="Work schema name", example="Standard 7.4h")
    working_hours_per_day: Optional[float] = Field(alias="workingHoursPerDay", default=None, description="Working hours per day", example=7.4)
    can_be_deleted: Optional[bool] = Field(alias="canBeDeleted", default=None, description="Whether this work schema can be deleted", example=True)
    id: Optional[int] = Field(default=None, description="Internal numeric identifier", example=3)
    uid: Optional[UUID] = Field(example="00000000-0000-0000-0000-000000000000", default=None, description="Work schema UID")

    class Config:
        populate_by_name = True


class CompanyDepartmentData(BaseModel):
    """Schema for company department data."""
    is_delete_allowed: Optional[bool] = Field(alias="isDeleteAllowed", default=None, description="Is delete allowed for this department", example=True)
    responsible_persons: Optional[List[ResponsiblePerson]] = Field(alias="responsiblePersons", default=None, description="List of responsible persons")
    company_work_schemas: Optional[List[CompanyWorkSchema]] = Field(alias="companyWorkSchemas", default=None, description="List of work schemas for this department")
    name: Optional[str] = Field(default=None, description="Department name", example="Sales")
    number: Optional[str] = Field(default=None, description="Department number/code", example="D-100")
    has_work_schema: Optional[bool] = Field(alias="hasWorkSchema", default=None, description="Whether department has a work schema", example=True)
    id: Optional[int] = Field(default=None, description="Internal numeric identifier", example=15)
    uid: Optional[UUID] = Field(example="00000000-0000-0000-0000-000000000000", default=None, description="Department UID")

    class Config:
        populate_by_name = True


class GetCompanyDepartmentsAsyncResponse(BaseModel):
    total_records: Optional[int] = Field(alias="totalRecords", default=None, description="Total records in data source", example=120)
    total_display_records: Optional[int] = Field(alias="totalDisplayRecords", default=None, description="Total records in current page", example=50)
    data: Optional[List[CompanyDepartmentData]] = Field(default=None, description="List of department data entries")
    class Config:
        populate_by_name = True


class InsertCompanyDepartmentRequest(BaseModel):
    companydepartmenttemplateuid: UUID = Field(example="00000000-0000-0000-0000-000000000000", alias="companyDepartmentTemplateUid", description="Template UID to base the department on")
    name: str = Field(description="Department name", example="Support")
    number: str = Field(description="Department number/code", example="D-200")
    responsibleemployeepersons: Optional[List[UUID]] = Field(alias="responsibleEmployeePersons", default=None, description="List of responsible employee UIDs", example=["00000000-0000-0000-0000-000000000000"])
    class Config:
        populate_by_name = True


class GetCompanyDepartmentResponse(BaseModel):
    is_delete_allowed: Optional[bool] = Field(alias="isDeleteAllowed", default=None, description="Is delete allowed for this department", example=True)
    responsible_persons: Optional[List[ResponsiblePerson]] = Field(alias="responsiblePersons", default=None, description="List of responsible persons")
    company_work_schemas: Optional[List[CompanyWorkSchema]] = Field(alias="companyWorkSchemas", default=None, description="List of work schemas for this department")
    name: Optional[str] = Field(default=None, description="Department name", example="Sales")
    number: Optional[str] = Field(default=None, description="Department number/code", example="D-100")
    has_work_schema: Optional[bool] = Field(alias="hasWorkSchema", default=None, description="Whether department has a work schema", example=True)
    id: Optional[int] = Field(default=None, description="Internal numeric identifier", example=15)
    uid: Optional[UUID] = Field(example="00000000-0000-0000-0000-000000000000", default=None, description="Department UID")
    class Config:
        populate_by_name = True


class GetWholeCompanyDepartmentResponse(BaseModel):
    accountings: Optional[List[Dict[str, Any]]] = Field(default=None, description="Accounting objects related to department")
    is_delete_allowed: Optional[bool] = Field(alias="isDeleteAllowed", default=None, description="Is delete allowed for this department", example=True)
    responsible_persons: Optional[List[ResponsiblePerson]] = Field(alias="responsiblePersons", default=None, description="List of responsible persons")
    company_work_schemas: Optional[List[CompanyWorkSchema]] = Field(alias="companyWorkSchemas", default=None, description="List of work schemas for this department")
    name: Optional[str] = Field(default=None, description="Department name", example="Sales")
    number: Optional[str] = Field(default=None, description="Department number/code", example="D-100")
    has_work_schema: Optional[bool] = Field(alias="hasWorkSchema", default=None, description="Whether department has a work schema", example=True)
    id: Optional[int] = Field(default=None, description="Internal numeric identifier", example=15)
    uid: Optional[UUID] = Field(example="00000000-0000-0000-0000-000000000000", default=None, description="Department UID")
    class Config:
        populate_by_name = True


class GetCompanyDepartmentAccountingsAsyncResponse(BaseModel):
    totalrecords: Optional[int] = Field(alias="totalRecords", default=None, description="Total records in data source", example=120)
    totaldisplayrecords: Optional[int] = Field(alias="totalDisplayRecords", default=None, description="Total records in current page", example=50)
    data: Optional[List[Dict[str, Any]]] = Field(default=None, description="List of accounting entries")
    class Config:
        populate_by_name = True


class GetCompanyDepartmentsListAsyncRequest(BaseModel):
    skip: Optional[int] = Field(default=None, description="Number of records to skip for pagination", example=0)
    take: Optional[int] = Field(default=None, description="Number of records to take for pagination", example=50)
    companydepartmentuids: Optional[List[UUID]] = Field(alias="companyDepartmentUids", default=None, description="Filter by department UIDs", example=["00000000-0000-0000-0000-000000000000"])
    responsiblepersonsuids: Optional[List[UUID]] = Field(alias="responsiblePersonsUids", default=None, description="Filter by responsible person UIDs", example=["00000000-0000-0000-0000-000000000000"])
    departmentsortoptions: Optional[Dict[str, Any]] = Field(alias="departmentSortOptions", default=None, description="Sorting options for departments", example={"field": "name", "direction": "asc"})
    departmentoverrides: Optional[List[bool]] = Field(alias="departmentOverrides", default=None, description="Override flags for department list", example=[True, False])
    class Config:
        populate_by_name = True

# BrynQ Pandera DataFrame Model for Departments
from pandera.typing import Series
import pandera as pa
import pandas as pd
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class DepartmentsGet(BrynQPanderaDataFrameModel):
    """Flattened schema for Zenegy Departments Output data"""
    # Basic department fields
    is_delete_allowed: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is delete allowed", alias="isDeleteAllowed")
    has_override: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Has override", alias="hasOverride")
    name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Department name", alias="name")
    number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Department number", alias="number")
    has_work_schema: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Has work schema", alias="hasWorkSchema")
    id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Department ID", alias="id")
    uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Department UID", alias="uid")

    # Responsible persons (as JSON string since it's a list of objects)
    responsible_persons: Optional[Series[object]] = pa.Field(coerce=True, nullable=True, description="Responsible persons list", alias="responsiblePersons")

    # Finance department dimension (nested object)
    finance_department_dimension: Optional[Series[object]] = pa.Field(coerce=True, nullable=True, description="Finance department dimension", alias="financeDepartmentDimension")

    # Company work schemas as array (when root-level normalization is used)
    company_work_schemas: Optional[Series[object]] = pa.Field(coerce=True, nullable=True, description="Company work schemas", alias="companyWorkSchemas")

    # Work schema fields (from expanded companyWorkSchemas)
    work_schema_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Work schema name", alias="workSchema__name")
    work_schema_working_hours_per_day: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Working hours per day", alias="workSchema__workingHoursPerDay")
    work_schema_can_be_deleted: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Can be deleted", alias="workSchema__canBeDeleted")
    work_schema_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Work schema ID", alias="workSchema__id")
    work_schema_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Work schema UID", alias="workSchema__uid")

    class _Annotation:
        primary_key = "uid"
        foreign_keys = {}
