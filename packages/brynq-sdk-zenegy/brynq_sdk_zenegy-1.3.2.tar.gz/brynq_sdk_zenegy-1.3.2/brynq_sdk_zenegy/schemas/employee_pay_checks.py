# Generated schemas for tag: EmployeePayChecks

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from uuid import UUID

from brynq_sdk_zenegy.schemas.company_departments import CompanyDepartmentData

class PaycheckCreate(BaseModel):
    """Schema for creating pay checks."""
    paycheck_for: Optional[int] = Field(alias="payCheckFor", default=None, description="Target paycheck type/code", example=1)
    name: str = Field(..., min_length=0, max_length=128, description="Paycheck item name", example="Bonus")
    unit: Optional[float] = Field(default=None, description="Units for the item", example=10.0)
    payment_per_unit: Optional[float] = Field(alias="paymentPerUnit", default=None, description="Payment per unit", example=150.0)
    rate_uid: Optional[UUID] = Field(example="00000000-0000-0000-0000-000000000000", alias="rateUid", default=None, description="Linked rate UID")
    reg_number: Optional[str] = Field(alias="regNumber", pattern=r"^\d{4}$", description="Must be exactly 4 digits", default=None, example="0001")
    konto_number: Optional[str] = Field(alias="kontoNumber", pattern=r"^\d{10}$", description="Must be exactly 10 digits", default=None, example="1234567890")
    include_in_pension_base: Optional[bool] = Field(alias="includeInPensionBase", default=None, description="Include in pension base", example=True)
    include_in_am_pension_base: Optional[bool] = Field(alias="includeInAmPensionBase", default=None, description="Include in AM pension base", example=True)
    is_included_in_holiday_entitlement_salary: Optional[bool] = Field(alias="isIncludedInHolidayEntitlementSalary", default=None, description="Included in holiday entitlement salary", example=False)
    department_uid: Optional[UUID] = Field(example="00000000-0000-0000-0000-000000000000", alias="departmentUid", default=None, description="Department UID")
    cost_center_uid: Optional[UUID] = Field(example="00000000-0000-0000-0000-000000000000", alias="costCenterUid", default=None, description="Cost center UID")
    profit_center_uid: Optional[UUID] = Field(example="00000000-0000-0000-0000-000000000000", alias="profitCenterUid", default=None, description="Profit center UID")
    percentage: Optional[float] = Field(default=None, description="Percentage for calculation", example=12.5)
    is_included_in_holiday_entitlement_salary_reduction: Optional[bool] = Field(alias="isIncludedInHolidayEntitlementSalaryReduction", default=None, description="Included in holiday entitlement salary reduction", example=False)

    class Config:
        populate_by_name = True

class PaycheckUpdate(BaseModel):
    """Schema for updating pay checks."""
    paycheck_for: Optional[int] = Field(alias="payCheckFor", default=None, description="Target paycheck type/code", example=1)
    name: str = Field(..., min_length=0, max_length=128, description="Paycheck item name", example="Bonus")
    unit: Optional[float] = Field(default=None, description="Units for the item", example=10.0)
    payment_per_unit: Optional[float] = Field(alias="paymentPerUnit", default=None, description="Payment per unit", example=150.0)
    rate_uid: Optional[UUID] = Field(example="00000000-0000-0000-0000-000000000000", alias="rateUid", default=None, description="Linked rate UID")
    reg_number: Optional[str] = Field(alias="regNumber", pattern=r"^\d{4}$", description="Must be exactly 4 digits", default=None, example="0001")
    konto_number: Optional[str] = Field(alias="kontoNumber", pattern=r"^\d{10}$", description="Must be exactly 10 digits", default=None, example="1234567890")
    include_in_pension_base: Optional[bool] = Field(alias="includeInPensionBase", default=None, description="Include in pension base", example=True)
    include_in_am_pension_base: Optional[bool] = Field(alias="includeInAmPensionBase", default=None, description="Include in AM pension base", example=True)
    is_included_in_holiday_entitlement_salary: Optional[bool] = Field(alias="isIncludedInHolidayEntitlementSalary", default=None, description="Included in holiday entitlement salary", example=False)
    department_uid: Optional[UUID] = Field(example="00000000-0000-0000-0000-000000000000", alias="departmentUid", default=None, description="Department UID")
    cost_center_uid: Optional[UUID] = Field(example="00000000-0000-0000-0000-000000000000", alias="costCenterUid", default=None, description="Cost center UID")
    profit_center_uid: Optional[UUID] = Field(example="00000000-0000-0000-0000-000000000000", alias="profitCenterUid", default=None, description="Profit center UID")
    percentage: Optional[float] = Field(default=None, description="Percentage for calculation", example=12.5)
    is_included_in_holiday_entitlement_salary_reduction: Optional[bool] = Field(alias="isIncludedInHolidayEntitlementSalaryReduction", default=None, description="Included in holiday entitlement salary reduction", example=False)

    class Config:
        populate_by_name = True

# BrynQ Pandera DataFrame Model for Pay Checks
from pandera.typing import Series
import pandera as pa
import pandas as pd
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class PayChecksGet(BrynQPanderaDataFrameModel):
    """Flattened schema for Zenegy Pay Checks Output data"""
    # Basic pay check fields
    source: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Source", alias="source")
    paycheck_for: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Pay check for", alias="payCheckFor")
    name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Pay check name", alias="name")
    unit: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Unit", alias="unit")
    payment_per_unit: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Payment per unit", alias="paymentPerUnit")
    reg_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Registration number", alias="regNumber")
    konto_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Konto number", alias="kontoNumber")
    is_prorated: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is prorated", alias="isProrated")
    prorated_amount: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Prorated amount", alias="proratedAmount")
    cost_center_code: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Cost center code", alias="costCenterCode")
    cost_center_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Cost center name", alias="costCenterName")
    registration_date: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Registration date", alias="registrationDate")
    should_trigger_retro: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Should trigger retro", alias="shouldTriggerRetro")
    include_in_pension_base: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Include in pension base", alias="includeInPensionBase")
    include_in_am_pension_base: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Include in AM pension base", alias="includeInAmPensionBase")
    is_included_in_holiday_entitlement_salary: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is included in holiday entitlement salary", alias="isIncludedInHolidayEntitlementSalary")
    created_on: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Created on", alias="createdOn")
    percentage_info_text: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Percentage info text", alias="percentageInfoText")
    calculated_amount: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Calculated amount", alias="calculatedAmount")
    hours: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Hours", alias="hours")
    percentage: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Percentage", alias="percentage")
    is_included_in_holiday_entitlement_salary_reduction: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is included in holiday entitlement salary reduction", alias="isIncludedInHolidayEntitlementSalaryReduction")
    id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Pay check ID", alias="id")
    uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Pay check UID", alias="uid")

    # Raw nested objects (if API returns unflattened objects as-is)
    rate: Optional[Series[object]] = pa.Field(coerce=True, nullable=True, description="Raw rate object", alias="rate")
    department: Optional[Series[object]] = pa.Field(coerce=True, nullable=True, description="Raw department object", alias="department")
    cost_center: Optional[Series[object]] = pa.Field(coerce=True, nullable=True, description="Raw cost center object", alias="costCenter")
    profit_center: Optional[Series[object]] = pa.Field(coerce=True, nullable=True, description="Raw profit center object", alias="profitCenter")
    country_specific_dto: Optional[Series[object]] = pa.Field(coerce=True, nullable=True, description="Raw country specific DTO", alias="countrySpecificDto")

    # Rate fields (nested object)
    rate_has_override: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Rate has override", alias="rate__hasOverride")
    rate_account_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Rate account type", alias="rate__accountType")
    rate_account_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Rate account number", alias="rate__accountNumber")
    rate_account_text: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Rate account text", alias="rate__accountText")
    rate_wage_code: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Rate wage code", alias="rate__wageCode")
    rate_credit_account_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Rate credit account number", alias="rate__creditAccountNumber")
    rate_reg_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Rate reg number", alias="rate__regNumber")
    rate_konto_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Rate konto number", alias="rate__kontoNumber")
    rate_is_deleted: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Rate is deleted", alias="rate__isDeleted")
    rate_is_prorated_rate: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Rate is prorated rate", alias="rate__isProratedRate")
    rate_include_in_pension_base: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Rate include in pension base", alias="rate__includeInPensionBase")
    rate_include_in_am_pension_base: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Rate include in AM pension base", alias="rate__includeInAmPensionBase")
    rate_is_included_in_holiday_entitlement_salary: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Rate is included in holiday entitlement salary", alias="rate__isIncludedInHolidayEntitlementSalary")
    rate_use_supplement_rates: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Rate use supplement rates", alias="rate__useSupplementRates")
    rate_use_hour_rates: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Rate use hour rates", alias="rate__useHourRates")
    rate_composed_rates: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Rate composed rates", alias="rate__composedRates")
    rate_calculate_on_percentage: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Rate calculate on percentage", alias="rate__calculateOnPercentage")
    rate_percentage_info_text: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Rate percentage info text", alias="rate__percentageInfoText")
    rate_calculate_on_gross_salary: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Rate calculate on gross salary", alias="rate__calculateOnGrossSalary")
    rate_is_from_template: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Rate is from template", alias="rate__isFromTemplate")
    rate_predefined_rate_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Rate predefined rate type", alias="rate__predefinedRateType")
    rate_is_included_in_holiday_entitlement_salary_reduction: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Rate is included in holiday entitlement salary reduction", alias="rate__isIncludedInHolidayEntitlementSalaryReduction")
    rate_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Rate number", alias="rate__number")
    rate_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Rate type", alias="rate__type")
    rate_limited_to_employee: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Rate limited to employee", alias="rate__limitedToEmployee")
    rate_is_benefit_package_two_enabled: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Rate is benefit package two enabled", alias="rate__isBenefitPackageTwoEnabled")
    rate_override_rate: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Rate override rate", alias="rate__overrideRate")
    rate_hours: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Rate hours", alias="rate__hours")
    rate_override_name: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Rate override name", alias="rate__overrideName")
    rate_employees: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Rate employees", alias="rate__employees")
    rate_departments: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Rate departments", alias="rate__departments")
    rate_rate: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Rate rate", alias="rate__rate")
    rate_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Rate name", alias="rate__name")
    rate_percentage: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Rate percentage", alias="rate__percentage")
    rate_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Rate ID", alias="rate__id")
    rate_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Rate UID", alias="rate__uid")

    # Country specific fields (nested object)
    country_specific_dto_country_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Country specific DTO country UID", alias="countrySpecificDto__countryUid")
    country_specific_dto_country_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Country specific DTO country name", alias="countrySpecificDto__countryName")
    country_specific_dto_country_code: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Country specific DTO country code", alias="countrySpecificDto__countryCode")
    country_specific_dto_country_id: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Country specific DTO country ID", alias="countrySpecificDto__countryId")
    country_specific_dto_country_tax_percentage: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Country specific DTO country tax percentage", alias="countrySpecificDto__countryTaxPercentage")
    country_specific_dto_country_taxable_income: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Country specific DTO country taxable income", alias="countrySpecificDto__countryTaxableIncome")

    # Department fields (nested object)
    department_is_delete_allowed: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Department is delete allowed", alias="department__isDeleteAllowed")
    department_responsible_persons: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Department responsible persons", alias="department__responsiblePersons")
    department_company_work_schemas: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Department company work schemas", alias="department__companyWorkSchemas")
    department_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Department name", alias="department__name")
    department_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Department number", alias="department__number")
    department_has_work_schema: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Department has work schema", alias="department__hasWorkSchema")
    department_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Department ID", alias="department__id")
    department_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Department UID", alias="department__uid")

    # Cost center fields (nested object)
    cost_center_number_of_employees: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Cost center number of employees", alias="costCenter__numberOfEmployees")
    cost_center_employee_uids: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Cost center employee UIDs", alias="costCenter__employeeUids")
    cost_center_cost_center_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Cost center cost center name", alias="costCenter__costCenterName")
    cost_center_cost_center_code: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Cost center cost center code", alias="costCenter__costCenterCode")
    cost_center_type: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Cost center type", alias="costCenter__type")
    cost_center_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Cost center ID", alias="costCenter__id")
    cost_center_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Cost center UID", alias="costCenter__uid")

    # Profit center fields (nested object)
    profit_center_number_of_employees: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Profit center number of employees", alias="profitCenter__numberOfEmployees")
    profit_center_employee_uids: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Profit center employee UIDs", alias="profitCenter__employeeUids")
    profit_center_cost_center_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Profit center cost center name", alias="profitCenter__costCenterName")
    profit_center_cost_center_code: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Profit center cost center code", alias="profitCenter__costCenterCode")
    profit_center_type: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Profit center type", alias="profitCenter__type")
    profit_center_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Profit center ID", alias="profitCenter__id")
    profit_center_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Profit center UID", alias="profitCenter__uid")

    class _Annotation:
        primary_key = "uid"
        foreign_keys = {}
