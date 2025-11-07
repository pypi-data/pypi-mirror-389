# Generated schemas for tag: Absence

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from uuid import UUID


class Department(BaseModel):
    """Schema for department information."""
    name: Optional[str] = Field(default=None)
    number: Optional[str] = Field(default=None)
    has_work_schema: Optional[bool] = Field(alias="hasWorkSchema", default=None)
    id: Optional[int] = Field(default=None)
    uid: Optional[UUID] = Field(example="00000000-0000-0000-0000-000000000000", default=None)

    class Config:
        populate_by_name = True


class Center(BaseModel):
    """Schema for cost center or profit center information."""
    id: Optional[int] = Field(default=None)
    uid: Optional[UUID] = Field(example="00000000-0000-0000-0000-000000000000", default=None)
    name: Optional[str] = Field(default=None)
    number: Optional[str] = Field(default=None)
    type: Optional[str] = Field(default=None)

    class Config:
        populate_by_name = True


class Employee(BaseModel):
    """Schema for employee information."""
    title: Optional[str] = Field(default=None)
    is_active: Optional[bool] = Field(alias="isActive", default=None)
    is_resigned: Optional[bool] = Field(alias="isResigned", default=None)
    cpr: Optional[str] = Field(default=None)
    salary_type: Optional[int] = Field(alias="salaryType", default=None)
    contact_phone: Optional[str] = Field(alias="contactPhone", default=None)
    contact_email: Optional[str] = Field(alias="contactEmail", default=None)
    department: Optional[Department] = Field(default=None)
    cost_center: Optional[Center] = Field(alias="costCenter", default=None)
    profit_center: Optional[Center] = Field(alias="profitCenter", default=None)
    car_registration_number: Optional[str] = Field(alias="carRegistrationNumber", default=None)
    type: Optional[int] = Field(default=None)
    salary_payout_period: Optional[int] = Field(alias="salaryPayoutPeriod", default=None)
    revenue_type: Optional[int] = Field(alias="revenueType", default=None)
    income_type: Optional[int] = Field(alias="incomeType", default=None)
    holiday_pay_receiver_type: Optional[int] = Field(alias="holidayPayReceiverType", default=None)
    extra_holiday_entitlement_rule: Optional[str] = Field(alias="extraHolidayEntitlementRule", default=None)
    name: Optional[str] = Field(default=None)
    employee_number: Optional[str] = Field(alias="employeeNumber", default=None)
    extra_employee_number: Optional[str] = Field(alias="extraEmployeeNumber", default=None)
    id: Optional[int] = Field(default=None)
    uid: Optional[UUID] = Field(example="00000000-0000-0000-0000-000000000000", default=None)

    class Config:
        populate_by_name = True


class CompanyAbsenceType(BaseModel):
    """Schema for company absence type information."""
    name: Optional[str] = Field(default=None)
    number: Optional[str] = Field(default=None)
    absence_type_name: Optional[str] = Field(alias="absenceTypeName", default=None)
    absence_type: Optional[int] = Field(alias="absenceType", default=None)
    is_custom_absence_type: Optional[bool] = Field(alias="isCustomAbsenceType", default=None)
    search_name: Optional[str] = Field(alias="searchName", default=None)
    id: Optional[int] = Field(default=None)
    uid: Optional[UUID] = Field(example="00000000-0000-0000-0000-000000000000", default=None)

    class Config:
        populate_by_name = True


class AbsenceData(BaseModel):
    """Schema for absence data items."""
    employee: Optional[Employee] = Field(default=None)
    from_date: Optional[datetime] = Field(alias="fromDate", default=None)
    to_date: Optional[datetime] = Field(alias="toDate", default=None)
    note: Optional[str] = Field(default=None)
    absence_type: Optional[int] = Field(alias="absenceType", default=None)
    status: Optional[int] = Field(default=None)
    days: Optional[float] = Field(default=None)
    project_id: Optional[str] = Field(alias="projectId", default=None)
    attachment_count: Optional[int] = Field(alias="attachmentCount", default=None)
    absence_type_name: Optional[str] = Field(alias="absenceTypeName", default=None)
    company_absence_type: Optional[CompanyAbsenceType] = Field(alias="companyAbsenceType", default=None)
    employee_payroll_fk: Optional[int] = Field(alias="employeePayrollFk", default=None)
    id: Optional[int] = Field(default=None)
    uid: Optional[UUID] = Field(example="00000000-0000-0000-0000-000000000000", default=None)

    class Config:
        populate_by_name = True


class GetAbsenceDaysPerCompanyResponse(BaseModel):
    """
    Schema for getting absence days per company response.

    """
    total_records: Optional[int] = Field(alias="totalRecords", default=None)
    total_display_records: Optional[int] = Field(alias="totalDisplayRecords", default=None)
    data: Optional[List[AbsenceData]] = Field(default=None)

    class Config:
        populate_by_name = True

class CreateAbsenceRequest(BaseModel):
    """
    Schema for creating absence request.
    """
    uid: Optional[UUID] = Field(
        default=None,
        description="Absence UID (server-assigned on creation)",
        example="00000000-0000-0000-0000-000000000000",
    )
    employee_uid: UUID = Field(
        alias="employeeUid",
        description="UID of the employee for whom the absence is created",
        example="00000000-0000-0000-0000-000000000000",
    )
    from_date: datetime = Field(
        alias="fromDate",
        description="Absence start date/time (ISO 8601)",
        example="2024-01-10T00:00:00Z",
    )
    to_date: datetime = Field(
        alias="toDate",
        description="Absence end date/time (ISO 8601)",
        example="2024-01-12T23:59:59Z",
    )
    absence_type: int = Field(
        alias="absenceType",
        description="Absence type code",
        example=1,
    )
    company_absence_type_uid: Optional[UUID] = Field(
        alias="companyAbsenceTypeUid", default=None,
        description="Company absence type UID",
        example="00000000-0000-0000-0000-000000000000",
    )
    note: Optional[str] = Field(
        default=None,
        description="Optional note for the absence",
        example="Sick leave",
    )
    days: Optional[float] = Field(
        default=None,
        description="Total number of absence days",
        example=2.0,
    )
    project_id: Optional[str] = Field(
        alias="projectId", default=None,
        description="Related project identifier (if any)",
        example="PRJ-1001",
    )
    status: Optional[int] = Field(
        default=None,
        description="Absence status code",
        example=0,
    )
    attachment_uids: Optional[List[UUID]] = Field(
        alias="attachmentUids", default=None,
        description="List of attachment UIDs",
        example=["00000000-0000-0000-0000-000000000000"],
    )

    class Config:
        populate_by_name = True

class GetAbsenceAsyncResponse(BaseModel):
    """
    Schema for getting absence asynchronously response.
    """
    attachments: Optional[List[Dict[str, Any]]] = Field(default=None)
    employee: Optional[Employee] = Field(default=None)
    from_date: Optional[datetime] = Field(alias="fromDate", default=None)
    to_date: Optional[datetime] = Field(alias="toDate", default=None)
    note: Optional[str] = Field(default=None)
    absence_type: Optional[int] = Field(alias="absenceType", default=None)
    status: Optional[int] = Field(default=None)
    days: Optional[float] = Field(default=None)
    project_id: Optional[str] = Field(alias="projectId", default=None)
    attachment_count: Optional[int] = Field(alias="attachmentCount", default=None)
    absence_type_name: Optional[str] = Field(alias="absenceTypeName", default=None)
    company_absence_type: Optional[CompanyAbsenceType] = Field(alias="companyAbsenceType", default=None)
    employee_payroll_fk: Optional[int] = Field(alias="employeePayrollFk", default=None)
    id: Optional[int] = Field(default=None)
    uid: Optional[UUID] = Field(example="00000000-0000-0000-0000-000000000000", default=None)
    class Config:
        populate_by_name = True

class UpdateAbsenceRequest(BaseModel):
    """
    Schema for updating absence request.
    """
    uid: Optional[UUID] = Field(
        example="00000000-0000-0000-0000-000000000000", default=None,
        description="Absence UID to update",
    )
    employee_uid: UUID = Field(
        example="00000000-0000-0000-0000-000000000000", alias="employeeUid",
        description="UID of the employee for whom the absence is updated",
    )
    from_date: datetime = Field(
        alias="fromDate",
        description="Absence start date/time (ISO 8601)",
        example="2024-01-10T00:00:00Z",
    )
    to_date: datetime = Field(
        alias="toDate",
        description="Absence end date/time (ISO 8601)",
        example="2024-01-12T23:59:59Z",
    )
    absence_type: int = Field(
        alias="absenceType",
        description="Absence type code",
        example=1,
    )
    company_absence_type_uid: Optional[UUID] = Field(
        example="00000000-0000-0000-0000-000000000000", alias="companyAbsenceTypeUid", default=None,
        description="Company absence type UID",
    )
    note: Optional[str] = Field(
        default=None,
        description="Optional note for the absence",
        example="Medical appointment",
    )
    days: Optional[float] = Field(
        default=None,
        description="Total number of absence days",
        example=1.0,
    )
    project_id: Optional[str] = Field(
        alias="projectId", default=None,
        description="Related project identifier (if any)",
        example="PRJ-1001",
    )
    status: Optional[int] = Field(
        default=None,
        description="Absence status code",
        example=0,
    )
    attachment_uids: Optional[List[UUID]] = Field(
        alias="attachmentUids", default=None,
        description="List of attachment UIDs",
        example=["00000000-0000-0000-0000-000000000000"],
    )
    class Config:
        populate_by_name = True

class GetCompanyAbsenceAttachmentLocationAsyncResponse(BaseModel):
    """
    Schema for getting company absence attachment location asynchronously response.
    """
    pass
    class Config:
        populate_by_name = True

class InsertAbsencesAsyncRequest(BaseModel):
    """
    Schema for inserting absences asynchronously request.
    """
    absences: List[AbsenceData]
    class Config:
        populate_by_name = True

class GetAbsenceCalendarDaysForCompanyRequest(BaseModel):
    """
    Schema for getting absence calendar days for company request.

    """
    status: Optional[int] = Field(default=None)
    types: Optional[List[int]] = Field(default=None)
    company_absence_type_uids: Optional[List[UUID]] = Field(alias="companyAbsenceTypeUids", default=None)
    employee_uids: Optional[List[UUID]] = Field(alias="employeeUids", default=None)
    company_department_uids: Optional[List[UUID]] = Field(alias="companyDepartmentUids", default=None)
    period: Optional[Dict[str, Any]] = Field(default=None)
    attachments: Optional[int] = Field(default=None)
    skip: Optional[int] = Field(default=None)
    take: Optional[int] = Field(default=None)
    class Config:
        populate_by_name = True

class ValidateAbsencesAsyncRequest(BaseModel):
    """
    Schema for validating absences asynchronously request.
    """
    absences: List[AbsenceData]
    class Config:
        populate_by_name = True

class SplitEmployeeAbsenceRequest(BaseModel):
    """
    Schema for splitting employee absence request.
    """
    number_of_days: float = Field(alias="numberOfDays")
    payroll_uid: UUID = Field(example="00000000-0000-0000-0000-000000000000", alias="payrollUid")
    class Config:
        populate_by_name = True

class GetAbsenceDataPerEmployeeRequest(BaseModel):
    """
    Schema for getting absence data per employee request.
    """
    datefrom: datetime = Field(alias="dateFrom")
    dateto: datetime = Field(alias="dateTo")
    class Config:
        populate_by_name = True

# BrynQ Pandera DataFrame Model for Absence Days Per Company
from pandera.typing import Series
import pandera as pa
import pandas as pd
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class AbsenceGet(BrynQPanderaDataFrameModel):
    """Flattened schema for Zenegy Absence Output data"""
    # Employee fields
    employee_title: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee title", alias="employee__title")
    employee_is_active: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Employee active status", alias="employee__isActive")
    employee_is_resigned: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Employee resigned status", alias="employee__isResigned")
    employee_cpr: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee CPR number", alias="employee__cpr")
    employee_salary_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee salary type", alias="employee__salaryType")
    employee_contact_phone: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee contact phone", alias="employee__contactPhone")
    employee_contact_email: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee contact email", alias="employee__contactEmail")
    employee_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee type", alias="employee__type")
    employee_salary_payout_period: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee salary payout period", alias="employee__salaryPayoutPeriod")
    employee_revenue_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee revenue type", alias="employee__revenueType")
    employee_income_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee income type", alias="employee__incomeType")
    employee_holiday_pay_receiver_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee holiday pay receiver type", alias="employee__holidayPayReceiverType")
    employee_extra_holiday_entitlement_rule: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee extra holiday entitlement rule", alias="employee__extraHolidayEntitlementRule")
    employee_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee name", alias="employee__name")
    employee_employee_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee number", alias="employee__employeeNumber")
    employee_extra_employee_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee extra employee number", alias="employee__extraEmployeeNumber")
    employee_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee ID", alias="employee__id")
    employee_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee UID", alias="employee__uid")

    # Department fields
    employee_department_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee department name", alias="employee__department__name")
    employee_department_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee department number", alias="employee__department__number")
    employee_department_has_work_schema: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Employee department has work schema", alias="employee__department__hasWorkSchema")
    employee_department_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee department ID", alias="employee__department__id")
    employee_department_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee department UID", alias="employee__department__uid")

    # Direct Employee fields (not nested)
    employee_cost_center: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee cost center", alias="employee__costCenter")
    employee_profit_center: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee profit center", alias="employee__profitCenter")
    employee_car_registration_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee car registration number", alias="employee__carRegistrationNumber")

    # Cost Center fields (nested)
    employee_cost_center_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee cost center ID", alias="employee__costCenter__id")
    employee_cost_center_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee cost center UID", alias="employee__costCenter__uid")
    employee_cost_center_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee cost center name", alias="employee__costCenter__name")
    employee_cost_center_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee cost center number", alias="employee__costCenter__number")
    employee_cost_center_type: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee cost center type", alias="employee__costCenter__type")

    # Profit Center fields
    employee_profit_center_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee profit center ID", alias="employee__profitCenter__id")
    employee_profit_center_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee profit center UID", alias="employee_profitCenter__uid")
    employee_profit_center_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee profit center name", alias="employee__profitCenter__name")
    employee_profit_center_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee profit center number", alias="employee__profitCenter__number")
    employee_profit_center_type: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee profit center type", alias="employee__profitCenter__type")

    # Absence fields
    from_date: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Absence from date", alias="fromDate")
    to_date: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Absence to date", alias="toDate")
    note: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Absence note", alias="note")
    absence_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Absence type", alias="absenceType")
    status: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Absence status", alias="status")
    days: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Absence days", alias="days")
    project_id: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Project ID", alias="projectId")
    attachment_count: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Attachment count", alias="attachmentCount")
    absence_type_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Absence type name", alias="absenceTypeName")
    employee_payroll_fk: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee payroll foreign key", alias="employeePayrollFk")
    id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Absence ID", alias="id")
    uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Absence UID", alias="uid")

    # Company Absence Type fields
    company_absence_type_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company absence type name", alias="companyAbsenceType__name")
    company_absence_type_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company absence type number", alias="companyAbsenceType__number")
    company_absence_type_absence_type_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company absence type absence type name", alias="companyAbsenceType__absenceTypeName")
    company_absence_type_absence_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Company absence type absence type", alias="companyAbsenceType__absenceType")
    company_absence_type_is_custom_absence_type: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Company absence type is custom absence type", alias="companyAbsenceType__isCustomAbsenceType")
    company_absence_type_search_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company absence type search name", alias="companyAbsenceType__searchName")
    company_absence_type_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Company absence type ID", alias="companyAbsenceType__id")
    company_absence_type_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company absence type UID", alias="companyAbsenceType__uid")

    class _Annotation:
        primary_key = "uid"
        foreign_keys = {}
