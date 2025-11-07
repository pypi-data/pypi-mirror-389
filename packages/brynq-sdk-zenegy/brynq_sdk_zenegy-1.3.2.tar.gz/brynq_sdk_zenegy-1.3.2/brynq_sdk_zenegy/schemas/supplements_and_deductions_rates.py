# Generated schemas for tag: SupplementRates

from pandera.typing import Series
import pandera as pa
import pandas as pd
from typing import Optional
from brynq_sdk_functions import BrynQPanderaDataFrameModel


class SupplementRatesGet(BrynQPanderaDataFrameModel):
    """Flattened schema for Zenegy Supplement Rates Output data"""
    # Basic supplement rate fields
    id: Optional[Series[pd.Int64Dtype]] = pa.Field(
        coerce=True, nullable=True, description="Supplement rate ID", alias="id"
    )
    uid: Optional[Series[pd.StringDtype]] = pa.Field(
        coerce=True, nullable=True, description="Supplement rate UID", alias="uid"
    )
    created_on: Optional[Series[pd.StringDtype]] = pa.Field(
        coerce=True, nullable=True, description="Created on date", alias="createdOn"
    )
    rate: Optional[Series[pd.Float64Dtype]] = pa.Field(
        coerce=True, nullable=True, description="Rate", alias="rate"
    )
    hours: Optional[Series[pd.Float64Dtype]] = pa.Field(
        coerce=True, nullable=True, description="Hours", alias="hours"
    )
    name: Optional[Series[pd.StringDtype]] = pa.Field(
        coerce=True, nullable=True, description="Name", alias="name"
    )
    number: Optional[Series[pd.StringDtype]] = pa.Field(
        coerce=True, nullable=True, description="Number", alias="number"
    )
    konto_number: Optional[Series[pd.StringDtype]] = pa.Field(
        coerce=True, nullable=True, description="Konto number", alias="kontoNumber"
    )
    reg_number: Optional[Series[pd.StringDtype]] = pa.Field(
        coerce=True, nullable=True, description="Registration number", alias="regNumber"
    )
    type: Optional[Series[pd.Int64Dtype]] = pa.Field(
        coerce=True, nullable=True, description="Type", alias="type"
    )
    shared_to_all: Optional[Series[pd.BooleanDtype]] = pa.Field(
        coerce=True, nullable=True, description="Shared to all", alias="sharedToAll"
    )
    limited_to_employee: Optional[Series[pd.BooleanDtype]] = pa.Field(
        coerce=True, nullable=True, description="Limited to employee", alias="limitedToEmployee"
    )
    is_benefit_package_two_enabled: Optional[Series[pd.BooleanDtype]] = pa.Field(
        coerce=True, nullable=True, description="Is benefit package two enabled", alias="isBenefitPackageTwoEnabled"
    )
    override_rate: Optional[Series[pd.BooleanDtype]] = pa.Field(
        coerce=True, nullable=True, description="Override rate", alias="overrideRate"
    )
    is_prorated_rate: Optional[Series[pd.BooleanDtype]] = pa.Field(
        coerce=True, nullable=True, description="Is prorated rate", alias="isProratedRate"
    )
    include_in_pension_base: Optional[Series[pd.BooleanDtype]] = pa.Field(
        coerce=True, nullable=True, description="Include in pension base", alias="includeInPensionBase"
    )
    include_in_am_pension_base: Optional[Series[pd.BooleanDtype]] = pa.Field(
        coerce=True, nullable=True, description="Include in AM pension base", alias="includeInAmPensionBase"
    )
    predefined_rate_type: Optional[Series[pd.Int64Dtype]] = pa.Field(
        coerce=True, nullable=True, description="Predefined rate type", alias="predefinedRateType"
    )
    is_included_in_holiday_entitlement_salary: Optional[Series[pd.BooleanDtype]] = pa.Field(
        coerce=True, nullable=True, description="Is included in holiday entitlement salary", alias="isIncludedInHolidayEntitlementSalary"
    )
    override_name: Optional[Series[pd.BooleanDtype]] = pa.Field(
        coerce=True, nullable=True, description="Override name", alias="overrideName"
    )
    use_supplement_rates: Optional[Series[pd.BooleanDtype]] = pa.Field(
        coerce=True, nullable=True, description="Use supplement rates", alias="useSupplementRates"
    )
    use_hour_rates: Optional[Series[pd.BooleanDtype]] = pa.Field(
        coerce=True, nullable=True, description="Use hour rates", alias="useHourRates"
    )
    composed_rates: Optional[Series[pd.StringDtype]] = pa.Field(
        coerce=True, nullable=True, description="Composed rates", alias="composedRates"
    )
    calculate_on_percentage: Optional[Series[pd.BooleanDtype]] = pa.Field(
        coerce=True, nullable=True, description="Calculate on percentage", alias="calculateOnPercentage"
    )
    percentage: Optional[Series[pd.Float64Dtype]] = pa.Field(
        coerce=True, nullable=True, description="Percentage", alias="percentage"
    )
    calculate_on_gross_salary: Optional[Series[pd.BooleanDtype]] = pa.Field(
        coerce=True, nullable=True, description="Calculate on gross salary", alias="calculateOnGrossSalary"
    )
    has_booking_group_override: Optional[Series[pd.BooleanDtype]] = pa.Field(
        coerce=True, nullable=True, description="Has booking group override", alias="hasBookingGroupOverride"
    )
    is_from_template: Optional[Series[pd.BooleanDtype]] = pa.Field(
        coerce=True, nullable=True, description="Is from template", alias="isFromTemplate"
    )
    is_in_use: Optional[Series[pd.BooleanDtype]] = pa.Field(
        coerce=True, nullable=True, description="Is in use", alias="isInUse"
    )
    is_included_in_holiday_entitlement_salary_reduction: Optional[Series[pd.BooleanDtype]] = pa.Field(
        coerce=True, nullable=True, description="Is included in holiday entitlement salary reduction", alias="isIncludedInHolidayEntitlementSalaryReduction"
    )
    is_overridden: Optional[Series[pd.BooleanDtype]] = pa.Field(
        coerce=True, nullable=True, description="Is overridden", alias="isOverridden"
    )

    class _Annotation:
        primary_key = "uid"
        foreign_keys = {}


# Employee-level supplement registrations (moved from employee_supplements_and_deductions_rates.py)
class SupplementRegistrationsGet(BrynQPanderaDataFrameModel):
    """Flattened schema for Zenegy Supplement Registrations Output data"""
    # Basic registration fields
    id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Registration ID", alias="id")
    uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Registration UID", alias="uid")
    date: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Date", alias="date")
    units: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Units", alias="units")
    rate: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Rate", alias="rate")
    total: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Total", alias="total")
    name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Name", alias="name")
    description: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Description", alias="description")
    status: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Status", alias="status")
    project_id: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Project ID", alias="projectId")
    attachment_count: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Attachment count", alias="attachmentCount")
    country_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Country UID", alias="countryUid")
    country_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Country name", alias="countryName")
    country_code: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Country code", alias="countryCode")
    country_id: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Country ID", alias="countryId")
    country_tax_percentage: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Country tax percentage", alias="countryTaxPercentage")
    country_taxable_income: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Country taxable income", alias="countryTaxableIncome")
    cost_center_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Cost center UID", alias="costCenterUid")
    cost_center_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Cost center name", alias="costCenterName")
    cost_center_code: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Cost center code", alias="costCenterCode")
    trigger_retro: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Trigger retro", alias="triggerRetro")
    company_department_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company department UID", alias="companyDepartmentUid")
    company_profit_center_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company profit center UID", alias="companyProfitCenterUid")
    percentage: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Percentage", alias="percentage")
    reference_id: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Reference ID", alias="referenceId")

    # Employee fields (nested object)
    employee_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee ID", alias="employee__id")
    employee_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee UID", alias="employee__uid")
    employee_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee name", alias="employee__name")
    employee_income_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee income type", alias="employee__incomeType")

    # Department fields (nested object)
    department_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Department ID", alias="department__id")
    department_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Department UID", alias="department__uid")
    department_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Department name", alias="department__name")
    department_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Department number", alias="department__number")
    department_has_work_schema: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Department has work schema", alias="department__hasWorkSchema")

    # Supplement rate fields (nested object)
    supplement_rate_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Supplement rate ID", alias="supplementRate__id")
    supplement_rate_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Supplement rate UID", alias="supplementRate__uid")
    supplement_rate_created_on: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Supplement rate created on", alias="supplementRate__createdOn")
    supplement_rate_rate: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Supplement rate rate", alias="supplementRate__rate")
    supplement_rate_hours: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Supplement rate hours", alias="supplementRate__hours")
    supplement_rate_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Supplement rate name", alias="supplementRate__name")
    supplement_rate_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Supplement rate number", alias="supplementRate__number")
    supplement_rate_konto_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Supplement rate konto number", alias="supplementRate__kontoNumber")
    supplement_rate_reg_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Supplement rate reg number", alias="supplementRate__regNumber")
    supplement_rate_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Supplement rate type", alias="supplementRate__type")
    supplement_rate_shared_to_all: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Supplement rate shared to all", alias="supplementRate__sharedToAll")
    supplement_rate_limited_to_employee: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Supplement rate limited to employee", alias="supplementRate__limitedToEmployee")
    supplement_rate_is_benefit_package_two_enabled: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Supplement rate is benefit package two enabled", alias="supplementRate__isBenefitPackageTwoEnabled")
    supplement_rate_override_rate: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Supplement rate override rate", alias="supplementRate__overrideRate")
    supplement_rate_is_prorated_rate: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Supplement rate is prorated rate", alias="supplementRate__isProratedRate")
    supplement_rate_include_in_pension_base: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Supplement rate include in pension base", alias="supplementRate__includeInPensionBase")
    supplement_rate_include_in_am_pension_base: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Supplement rate include in AM pension base", alias="supplementRate__includeInAmPensionBase")
    supplement_rate_predefined_rate_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Supplement rate predefined rate type", alias="supplementRate__predefinedRateType")
    supplement_rate_is_included_in_holiday_entitlement_salary: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Supplement rate is included in holiday entitlement salary", alias="supplementRate__isIncludedInHolidayEntitlementSalary")
    supplement_rate_override_name: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Supplement rate override name", alias="supplementRate__overrideName")
    supplement_rate_use_supplement_rates: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Supplement rate use supplement rates", alias="supplementRate__useSupplementRates")
    supplement_rate_use_hour_rates: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Supplement rate use hour rates", alias="supplementRate__useHourRates")
    supplement_rate_composed_rates: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Supplement rate composed rates", alias="supplementRate__composedRates")
    supplement_rate_calculate_on_percentage: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Supplement rate calculate on percentage", alias="supplementRate__calculateOnPercentage")
    supplement_rate_percentage: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Supplement rate percentage", alias="supplementRate__percentage")
    supplement_rate_calculate_on_gross_salary: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Supplement rate calculate on gross salary", alias="supplementRate__calculateOnGrossSalary")
    supplement_rate_has_booking_group_override: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Supplement rate has booking group override", alias="supplementRate__hasBookingGroupOverride")
    supplement_rate_is_from_template: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Supplement rate is from template", alias="supplementRate__isFromTemplate")
    supplement_rate_is_in_use: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Supplement rate is in use", alias="supplementRate__isInUse")
    supplement_rate_is_included_in_holiday_entitlement_salary_reduction: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Supplement rate is included in holiday entitlement salary reduction", alias="supplementRate__isIncludedInHolidayEntitlementSalaryReduction")

    class _Annotation:
        primary_key = "uid"
        foreign_keys = {}
