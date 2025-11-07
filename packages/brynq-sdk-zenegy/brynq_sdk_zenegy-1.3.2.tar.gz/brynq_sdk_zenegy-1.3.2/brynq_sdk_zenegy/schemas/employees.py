# Generated schemas for tag: Employees

from datetime import datetime
from typing import List, Optional, Any, Dict
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

# BrynQ Pandera DataFrame Model for Employees
from pandera.typing import Series
import pandera as pa
import pandas as pd
from brynq_sdk_functions import BrynQPanderaDataFrameModel


class User(BaseModel):
    """
    User schema for employee user information.
    """
    email: Optional[str] = Field(default=None, description="User email address", example="john.doe@example.com")
    id: Optional[int] = Field(default=None, description="User ID (internal numeric identifier)", example=1001)
    is_active: Optional[bool] = Field(alias="isActive", default=None, description="Whether the user is active", example=True)
    name: Optional[str] = Field(default=None, description="User display name", example="John Doe")
    photo_url: Optional[str] = Field(alias="photoUrl", default=None, description="URL to user's profile photo", example="https://example.com/photo.jpg")
    uid: Optional[UUID] = Field(example="00000000-0000-0000-0000-000000000000", default=None, description="User UID")

    class Config:
        populate_by_name = True


class Center(BaseModel):
    """Schema for cost center or profit center information."""
    number_of_employees: Optional[int] = Field(alias="numberOfEmployees", default=None, description="Number of employees in center", example=42)
    employee_uids: Optional[List[UUID]] = Field(alias="employeeUids", default=None, description="Employee UIDs assigned to the center", example=["00000000-0000-0000-0000-000000000000"])
    cost_center_name: Optional[str] = Field(alias="costCenterName", default=None, description="Cost center name", example="Sales")
    cost_center_code: Optional[str] = Field(alias="costCenterCode", default=None, description="Cost center code", example="SALES")
    type: Optional[str] = Field(default=None, description="Center type (cost/profit)", example="cost")
    id: Optional[int] = Field(default=None, description="Center ID (internal numeric)", example=7)
    uid: Optional[UUID] = Field(example="00000000-0000-0000-0000-000000000000", default=None, description="Center UID")

    class Config:
        populate_by_name = True


class Department(BaseModel):
    """Schema for department information."""
    name: Optional[str] = Field(default=None, description="Department name", example="Sales")
    number: Optional[str] = Field(default=None, description="Department code/number", example="D-100")
    has_work_schema: Optional[bool] = Field(alias="hasWorkSchema", default=None, description="Whether department has a work schema", example=True)
    id: Optional[int] = Field(default=None, description="Department ID (internal numeric)", example=15)
    uid: Optional[UUID] = Field(example="00000000-0000-0000-0000-000000000000", default=None, description="Department UID")

    class Config:
        populate_by_name = True


class Company(BaseModel):
    """Schema for company information."""
    association_id: Optional[int] = Field(alias="associationId", default=None, description="Association ID", example=12)
    p_number: Optional[str] = Field(alias="pNumber", default=None, description="Company P-number", example="P12345")
    cvr: Optional[str] = Field(default=None, description="Company CVR number", example="12345678")
    has_holiday_payment: Optional[bool] = Field(alias="hasHolidayPayment", default=None, description="Has holiday payment enabled", example=True)
    has_benefit_package: Optional[bool] = Field(alias="hasBenefitPackage", default=None, description="Has benefit package enabled", example=True)
    has_benefit_package_two: Optional[bool] = Field(alias="hasBenefitPackageTwo", default=None, description="Has second benefit package enabled", example=False)
    has_am_pension: Optional[bool] = Field(alias="hasAmPension", default=None, description="Has AM pension enabled", example=True)
    is_department_income_split_enabled: Optional[bool] = Field(alias="isDepartmentIncomeSplitEnabled", default=None, description="Department income split enabled", example=False)
    insurance_type: Optional[int] = Field(alias="insuranceType", default=None, description="Insurance type code", example=1)
    is_use_of_vacation_days_in_advance_enabled: Optional[bool] = Field(alias="isUseOfVacationDaysInAdvanceEnabled", default=None, description="Use of vacation days in advance enabled", example=False)
    is_horesta_supplement_enabled: Optional[bool] = Field(alias="isHorestaSupplementEnabled", default=None, description="HORESTA supplement enabled", example=False)
    has_holiday_payment_netto_transfer_or_payout: Optional[bool] = Field(alias="hasHolidayPaymentNettoTransferOrPayout", default=None, description="Holiday payment netto transfer or payout enabled", example=False)
    is_sh_payout_netto_enabled_payou: Optional[bool] = Field(alias="isShPayoutNettoEnabled", default=None, description="SH net payout enabled", example=False)
    is_transfer_fifth_holiday_week_enabled_l: Optional[bool] = Field(alias="isTransferFifthHolidayWeekEnabled", default=None, description="Transfer of fifth holiday week enabled", example=False)
    is_holiday_hindrance_enabled: Optional[bool] = Field(alias="isHolidayHindranceEnabled", default=None, description="Holiday hindrance enabled", example=False)
    is_extra_holiday_entitlement_in_hours_enabled_l: Optional[bool] = Field(alias="isExtraHolidayEntitlementInHoursEnabled", default=None, description="Extra holiday entitlement in hours enabled", example=False)
    extra_holiday_entitlement_in_hours: Optional[bool] = Field(alias="extraHolidayEntitlementInHours", default=None, description="Extra holiday entitlement applies in hours", example=False)
    id: Optional[int] = Field(default=None, description="Company ID (internal numeric)", example=5)
    uid: Optional[UUID] = Field(example="00000000-0000-0000-0000-000000000000", default=None, description="Company UID")
    name: Optional[str] = Field(default=None, description="Company name", example="Acme A/S")
    logo_url: Optional[str] = Field(alias="logoUrl", default=None, description="Company logo URL", example="https://example.com/logo.png")

    class Config:
        populate_by_name = True


class EmployeeBase(BaseModel):
    """Schema for employee base information."""
    date_of_resignation: Optional[datetime] = Field(None, alias="dateOfResignation", description="Employee resignation date (ISO 8601)", example="2024-05-31T00:00:00Z")
    last_work_day: Optional[datetime] = Field(None, alias="lastWorkDay", description="Last working day (ISO 8601)", example="2024-05-30T00:00:00Z")
    company_cost_center: Optional[Center] = Field(None, alias="companyCostCenter", description="Company-level cost center object")
    company_profit_center: Optional[Center] = Field(None, alias="companyProfitCenter", description="Company-level profit center object")
    created_on: Optional[datetime] = Field(None, alias="createdOn", description="Record creation timestamp (ISO 8601)", example="2024-01-15T12:00:00Z")
    image_url: Optional[str] = Field(None, alias="imageUrl", description="Profile image URL", example="https://example.com/photo.jpg")
    is_foreign: Optional[bool] = Field(None, alias="isForeign", description="Whether employee is foreign resident", example=False)
    company: Optional[Company] = None
    invited_by_email: Optional[int] = Field(None, alias="invitedByEmail", description="Invited by email flag (0/1)", example=0)
    has_payroll: Optional[bool] = Field(None, alias="hasPayroll", description="Whether employee has payroll", example=True)
    has_profile_image: Optional[bool] = Field(None, alias="hasProfileImage", description="Whether employee has a profile image", example=False)
    user: Optional[User] = None
    has_user: Optional[bool] = Field(None, alias="hasUser", description="Whether employee has a linked user", example=True)
    is_resigned_within_last_year: Optional[bool] = Field(None, alias="isResignedWithinLastyear", description="Resigned within last year", example=False)
    is_resigned_with_registrations: Optional[bool] = Field(None, alias="isResignedWithRegistrations", description="Resigned employee still has registrations", example=False)
    salary_mode: Optional[int] = Field(None, alias="salaryMode", description="Salary mode code", example=0)
    employment_date: Optional[datetime] = Field(None, alias="employmentDate", description="Employment start date (ISO 8601)", example="2023-06-01T00:00:00Z")
    global_value_set_number: Optional[str] = Field(None, alias="globalValueSetNumber", description="Global value set number", example="GV-SET-01")
    title: Optional[str] = None
    is_active: Optional[bool] = Field(None, alias="isActive", description="Active employment status", example=True)
    is_resigned: Optional[bool] = Field(None, alias="isResigned", description="Resigned status", example=False)
    cpr: Optional[str] = None
    salary_type: Optional[int] = Field(None, alias="salaryType", description="Salary type code", example=1)
    contact_phone: Optional[str] = Field(None, alias="contactPhone", description="Contact phone number", example="+45 12 34 56 78")
    email: Optional[str] = Field(None, alias="contactEmail", description="Contact email address", example="john.doe@example.com")
    department: Optional[Department] = None
    cost_center: Optional[Center] = Field(None, alias="costCenter", description="Employee cost center object")
    profit_center: Optional[Center] = Field(None, alias="profitCenter", description="Employee profit center object")
    car_registration_number: Optional[str] = Field(None, alias="carRegistrationNumber", description="Car registration number", example="AB12345")
    type: Optional[int] = None
    salary_payout_period: Optional[int] = Field(None, alias="salaryPayoutPeriod", description="Salary payout period code", example=1)
    revenue_type: Optional[int] = Field(None, alias="revenueType", description="Revenue type code", example=0)
    income_type: Optional[int] = Field(None, alias="incomeType", description="Income type code", example=0)
    holiday_pay_receiver_type: Optional[int] = Field(None, alias="holidayPayReceiverType", description="Holiday pay receiver type code", example=0)
    extra_holiday_entitlement_rule: Optional[str] = Field(None, alias="extraHolidayEntitlementRule", description="Extra holiday entitlement rule", example="RULE-1")
    name: Optional[str] = None
    employee_number: Optional[str] = Field(None, alias="employeeNumber", description="Internal employee number", example="E-1001")
    extra_employee_number: Optional[str] = Field(None, alias="extraEmployeeNumber", description="Secondary employee number", example="EXT-55")
    id: Optional[int] = None
    uid: Optional[UUID] = Field(None, example="00000000-0000-0000-0000-000000000000", description="Employee UID")

    class Config:
        populate_by_name = True


class GetEmployeeBasesAsyncResponse(BaseModel):
    """
    Schema for getting employee bases asynchronously response.
    """
    total_records: Optional[int] = Field(
        None, alias="totalRecords",
        description="Total records in source", example=120
    )
    total_display_records: Optional[int] = Field(
        None, alias="totalDisplayRecords",
        description="Records count for current page", example=50
    )
    data: Optional[List[EmployeeBase]] = Field(
        None,
        description="List of employee base entries"
    )

    class Config:
        populate_by_name = True

class EmployeeLanguage(BaseModel):
    translation_key: Optional[str] = Field(
        None, alias='translationKey',
        description="Translation key for language", example="en"
    )
    id: Optional[int] = Field(
        None, alias='id',
        description="Language numeric identifier", example=1
    )
    name: Optional[str] = Field(
        None, alias='name',
        description="Language name", example="English"
    )

    class Config:
        populate_by_name = True

class EmployeeUpsert(BaseModel):
    """Request body for creating or replacing an employee."""
    employee_type: int = Field(
        ..., ge=1, le=3, alias="employeeType",
        description="Employee type code (1=hourly, 2=monthly, 3=other)", example=1
    )
    p_number: str = Field(
        ..., alias="pnumber",
        description="External P-number for the employee (system specific)", example="P12345"
    )
    address: Optional[str] = Field(
        None, max_length=50,
        description="Street address", example="Main Street 1"
    )
    city: Optional[str] = Field(
        None, max_length=50,
        description="City name", example="Copenhagen"
    )
    postal_number: Optional[str] = Field(
        None, max_length=20, alias="postalNumber",
        description="Postal/ZIP code", example="2100"
    )
    mobile_phone: Optional[str] = Field(
        None, max_length=50, alias="mobilePhone",
        description="Mobile phone number", example="+45 12 34 56 78"
    )
    konto_number: Optional[str] = Field(
        None, alias="kontoNumber",
        description="Bank account (konto) number", example="1234567890"
    )
    reg_number: Optional[str] = Field(
        None, alias="regNumber",
        description="Bank registration number", example="0001"
    )
    language: Optional[EmployeeLanguage] = Field(
        None, description="Preferred language object", example={"name": "English"}
    )
    tin_number: Optional[str] = Field(
        None, alias="tinNumber",
        description="Tax identification number", example="12345678"
    )
    cpr: Optional[str] = Field(
        None, max_length=30,
        description="Danish CPR (personal ID)", example="010190-1234"
    )
    email: Optional[str] = Field(
        None, max_length=75,
        description="Email address", example="john.doe@example.com"
    )
    name: str = Field(
        ..., max_length=150,
        description="Full name", example="John Doe"
    )
    linked_in: Optional[str] = Field(
        None, max_length=200, alias="linkedIn",
        description="LinkedIn profile URL", example="https://www.linkedin.com/in/johndoe"
    )
    car_registration_number: Optional[str] = Field(
        None, max_length=20, alias="carRegistrationNumber",
        description="Car registration number", example="AB12345"
    )
    country_code: Optional[str] = Field(
        None, max_length=5, alias="countryCode",
        description="ISO country code", example="DK"
    )

    class Config:
        populate_by_name = True


class StartSaldo(BaseModel):
    start_g_days: Optional[float] = Field(default=None, description="Start G-days balance", example=0.0)
    start_time_off_good: Optional[float] = Field(default=None, description="Start time-off good balance", example=0.0)
    start_time_off_amount: Optional[float] = Field(default=None, description="Start time-off amount", example=0.0)
    start_am_income: Optional[float] = Field(default=None, description="Start AM income", example=0.0)
    start_contributory_income: Optional[float] = Field(default=None, description="Start contributory income", example=0.0)
    start_one_time_income: Optional[float] = Field(default=None, description="Start one-time income", example=0.0)
    start_b_income_with_am: Optional[float] = Field(default=None, description="Start B income with AM", example=0.0)
    start_b_in_come_without_am: Optional[float] = Field(default=None, description="Start B income without AM", example=0.0)
    start_hours: Optional[float] = Field(default=None, description="Start hours balance", example=0.0)
    start_atp: Optional[float] = Field(default=None, description="Start ATP amount", example=0.0)
    start_am: Optional[float] = Field(default=None, description="Start AM amount", example=0.0)
    start_a_skat: Optional[float] = Field(default=None, description="Start A-skat amount", example=0.0)
    start_health_insurance: Optional[float] = Field(default=None, description="Start health insurance amount", example=0.0)
    start_company_car: Optional[float] = Field(default=None, description="Start company car amount", example=0.0)
    start_company_lodging: Optional[float] = Field(default=None, description="Start company lodging amount", example=0.0)
    start_mileage: Optional[float] = Field(default=None, description="Start mileage", example=0.0)
    start_mileage_low_rate: Optional[float] = Field(default=None, description="Start mileage low rate", example=0.0)
    start_travel_allowance: Optional[float] = Field(default=None, description="Start travel allowance", example=0.0)
    start_personal_pension: Optional[float] = Field(default=None, description="Start personal pension amount", example=0.0)
    start_pension_from_company: Optional[float] = Field(default=None, description="Start company pension amount", example=0.0)
    start_group_life: Optional[float] = Field(default=None, description="Start group life amount", example=0.0)
    start_group_life_2: Optional[float] = Field(default=None, description="Start group life amount (2)", example=0.0)
    start_personal_amp: Optional[float] = Field(default=None, description="Start personal AMP amount", example=0.0)
    start_company_amp: Optional[float] = Field(default=None, description="Start company AMP amount", example=0.0)
    start_net_holiday_pay: Optional[float] = Field(default=None, description="Start net holiday pay amount", example=0.0)
    start_number_of_vacation_days: Optional[float] = Field(default=None, description="Start number of vacation days", example=0.0)
    start_holiday_supplement_value: Optional[float] = Field(default=None, description="Start holiday supplement value", example=0.0)
    start_benefits_package_saldo: Optional[float] = Field(default=None, description="Start benefits package saldo", example=0.0)
    start_benefits_package_earned: Optional[float] = Field(default=None, description="Start benefits package earned", example=0.0)
    start_benefits_package_two_saldo: Optional[float] = Field(default=None, description="Start benefits package two saldo", example=0.0)
    start_benefits_package_two_earned: Optional[float] = Field(default=None, description="Start benefits package two earned", example=0.0)
    start_vacations_legitimate_salary: Optional[float] = Field(default=None, description="Start vacations legitimate salary", example=0.0)
    start_free_phone: Optional[float] = Field(default=None, description="Start free phone amount", example=0.0)
    start_am_contributions_wages_and_holidaypay: Optional[float] = Field(default=None, description="Start AM contributions wages and holiday pay", example=0.0)
    start_number_of_vacation_days_two_periods_before: Optional[float] = Field(default=None, description="Start vacation days two periods before", example=0.0)
    start_number_of_vacation_days_previous_period: Optional[float] = Field(default=None, description="Start vacation days previous period", example=0.0)
    start_number_of_vacation_days_frozen_period: Optional[float] = Field(default=None, description="Start vacation days frozen period", example=0.0)
    start_number_of_vacation_days_current_period: Optional[float] = Field(default=None, description="Start vacation days current period", example=0.0)
    start_holiday_supplement_two_periods_before: Optional[float] = Field(default=None, description="Start holiday supplement two periods before", example=0.0)
    start_holiday_supplement_previous_period: Optional[float] = Field(default=None, description="Start holiday supplement previous period", example=0.0)
    start_holiday_supplement_current_period: Optional[float] = Field(default=None, description="Start holiday supplement current period", example=0.0)
    start_holiday_payment_saved: Optional[float] = Field(default=None, description="Start holiday payment saved", example=0.0)
    start_holiday_payment_advance: Optional[float] = Field(default=None, description="Start holiday payment advance", example=0.0)
    start_holiday_payment_advance_year_before: Optional[float] = Field(default=None, description="Start holiday payment advance year before", example=0.0)
    start_holiday_payment_saved_year_before: Optional[float] = Field(default=None, description="Start holiday payment saved year before", example=0.0)
    start_holiday_payment_saved_netto_year_before: Optional[float] = Field(default=None, description="Start holiday payment saved netto year before", example=0.0)
    start_holiday_payment_saved_netto: Optional[float] = Field(default=None, description="Start holiday payment saved netto", example=0.0)
    start_holiday_payment_saldo_netto: Optional[float] = Field(default=None, description="Start holiday payment saldo netto", example=0.0)
    start_used_vacation_day_units_current_period: Optional[float] = Field(default=None, description="Start used vacation day units current period", example=0.0)
    start_used_vacation_day_units_previous_period: Optional[float] = Field(default=None, description="Start used vacation day units previous period", example=0.0)
    start_used_vacation_day_units_two_periods_before: Optional[float] = Field(default=None, description="Start used vacation day units two periods before", example=0.0)
    start_used_vacation_day_units_frozen_period: Optional[float] = Field(default=None, description="Start used vacation day units frozen period", example=0.0)
    start_used_holiday_supplement_current_period: Optional[float] = Field(default=None, description="Start used holiday supplement current period", example=0.0)
    start_used_holiday_supplement_previous_period: Optional[float] = Field(default=None, description="Start used holiday supplement previous period", example=0.0)
    start_used_holiday_supplement_two_periods_before: Optional[float] = Field(default=None, description="Start used holiday supplement two periods before", example=0.0)
    start_earned_vacations_legitimate_salary_amount_previous_period: Optional[float] = Field(default=None, description="Earned vacations legitimate salary amount previous period", example=0.0)
    start_earned_vacations_legitimate_salary_amount_two_periods_before: Optional[float] = Field(default=None, description="Earned vacations legitimate salary amount two periods before", example=0.0)
    start_earned_vacations_legitimate_salary_amount_frozen_period: Optional[float] = Field(default=None, description="Earned vacations legitimate salary amount frozen period", example=0.0)
    start_earned_holiday_pay_net_amount_previous_period: Optional[float] = Field(default=None, description="Earned holiday pay net amount previous period", example=0.0)
    start_earned_holiday_pay_net_amount_two_periods_before: Optional[float] = Field(default=None, description="Earned holiday pay net amount two periods before", example=0.0)
    start_earned_holiday_pay_net_amount_frozen_period: Optional[float] = Field(default=None, description="Earned holiday pay net amount frozen period", example=0.0)
    start_earned_holiday_pay_net_amount_current_period: Optional[float] = Field(default=None, description="Earned holiday pay net amount current period", example=0.0)
    start_used_holiday_pay_net_amount_current_period: Optional[float] = Field(default=None, description="Used holiday pay net amount current period", example=0.0)
    start_used_holiday_pay_net_amount_previous_period: Optional[float] = Field(default=None, description="Used holiday pay net amount previous period", example=0.0)
    start_used_holiday_pay_net_amount_two_periods_before: Optional[float] = Field(default=None, description="Used holiday pay net amount two periods before", example=0.0)
    start_used_holiday_pay_net_amount_frozen_period: Optional[float] = Field(default=None, description="Used holiday pay net amount frozen period", example=0.0)
    start_earned_care_days_two_years_before: Optional[float] = Field(default=None, description="Earned care days two years before", example=0.0)
    start_earned_care_days_year_before: Optional[float] = Field(default=None, description="Earned care days year before", example=0.0)
    start_earned_care_days_current_year: Optional[float] = Field(default=None, description="Earned care days current year", example=0.0)
    start_used_care_days_two_years_before: Optional[float] = Field(default=None, description="Used care days two years before", example=0.0)
    start_used_care_days_year_before: Optional[float] = Field(default=None, description="Used care days year before", example=0.0)
    start_used_care_days_current_year: Optional[float] = Field(default=None, description="Used care days current year", example=0.0)
    start_earned_free_vacation_days_two_years_before: Optional[float] = Field(default=None, description="Earned free vacation days two years before", example=0.0)
    start_earned_free_vacation_days_year_before: Optional[float] = Field(default=None, description="Earned free vacation days year before", example=0.0)
    start_earned_free_vacation_days_current_year: Optional[float] = Field(default=None, description="Earned free vacation days current year", example=0.0)
    start_used_free_vacation_days_two_years_before: Optional[float] = Field(default=None, description="Used free vacation days two years before", example=0.0)
    start_used_free_vacation_days_year_before: Optional[float] = Field(default=None, description="Used free vacation days year before", example=0.0)
    start_used_free_vacation_days_current_year: Optional[float] = Field(default=None, description="Used free vacation days current year", example=0.0)
    start_earned_holiday_pay_gross_two_periods_before: Optional[float] = Field(default=None, description="Earned holiday pay gross two periods before", example=0.0)
    start_earned_holiday_pay_gross_previous_period: Optional[float] = Field(default=None, description="Earned holiday pay gross previous period", example=0.0)
    start_earned_holiday_pay_gross_current_period: Optional[float] = Field(default=None, description="Earned holiday pay gross current period", example=0.0)
    start_earned_holiday_pay_gross_frozen_period: Optional[float] = Field(default=None, description="Earned holiday pay gross frozen period", example=0.0)
    start_used_holiday_pay_gross_two_periods_before: Optional[float] = Field(default=None, description="Used holiday pay gross two periods before", example=0.0)
    start_used_holiday_pay_gross_previous_period: Optional[float] = Field(default=None, description="Used holiday pay gross previous period", example=0.0)
    start_used_holiday_pay_gross_current_period: Optional[float] = Field(default=None, description="Used holiday pay gross current period", example=0.0)
    start_used_holiday_pay_gross_frozen_period: Optional[float] = Field(default=None, description="Used holiday pay gross frozen period", example=0.0)
    start_flex_hours: Optional[float] = Field(default=None, description="Start flex hours", example=0.0)
    start_time_in_lieu_earned_hours: Optional[float] = Field(default=None, description="Start time-in-lieu earned hours", example=0.0)
    start_time_in_lieu_earned_amount: Optional[float] = Field(default=None, description="Start time-in-lieu earned amount", example=0.0)
    start_health_insurance_no_am_pension: Optional[float] = Field(default=None, description="Start health insurance (no AM pension)", example=0.0)
    start_health_insurance_no_am_pension_no_vacation_entitled_money: Optional[float] = Field(default=None, description="Start health insurance (no AM pension, no vacation entitled)", example=0.0)
    start_not_covered_by_triviality: Optional[float] = Field(default=None, description="Start not covered by triviality", example=0.0)
    start_christmas_gifts_benefit: Optional[float] = Field(default=None, description="Start Christmas gifts benefit", example=0.0)
    start_other_benefit: Optional[float] = Field(default=None, description="Start other benefit", example=0.0)
    start_negative_salary_saldo: Optional[float] = Field(default=None, description="Start negative salary saldo", example=0.0)
    start_anniversary_bonus_saldo: Optional[float] = Field(default=None, description="Start anniversary bonus saldo", example=0.0)
    start_severance_saldo: Optional[float] = Field(default=None, description="Start severance saldo", example=0.0)
    start_travel_allowance_without_payment: Optional[float] = Field(default=None, description="Start travel allowance without payment", example=0.0)
    start_holday_at_own_expense_two_years_before: Optional[float] = Field(default=None, description="Start holiday at own expense two years before", example=0.0)
    start_holday_at_own_expense_year_before: Optional[float] = Field(default=None, description="Start holiday at own expense year before", example=0.0)
    start_holday_at_own_expense_current_year: Optional[float] = Field(default=None, description="Start holiday at own expense current year", example=0.0)
    start_holday_at_own_expense_two_years_before_saldo: Optional[float] = Field(default=None, description="Start holiday at own expense two years before saldo", example=0.0)
    start_holday_at_own_expense_year_before_saldo: Optional[float] = Field(default=None, description="Start holiday at own expense year before saldo", example=0.0)
    start_holday_at_own_expense_current_year_saldo: Optional[float] = Field(default=None, description="Start holiday at own expense current year saldo", example=0.0)
    start_number_of_vacation_days_fifth_holiday_week_two_years_before: Optional[float] = Field(default=None, description="Start vacation days (5th week) two years before", example=0.0)
    start_number_used_vacation_days_fifth_holiday_week_two_years_before: Optional[float] = Field(default=None, description="Start used vacation days (5th week) two years before", example=0.0)
    start_vacation_pay_gross_fifth_holiday_week_two_years_before: Optional[float] = Field(default=None, description="Start vacation pay gross (5th week) two years before", example=0.0)
    start_vacations_legitimate_salary_fifth_holiday_week_two_years_before: Optional[float] = Field(default=None, description="Start vacations legitimate salary (5th week) two years before", example=0.0)
    start_vacation_supplement_earned_fifth_holiday_week_two_years_before: Optional[float] = Field(default=None, description="Start vacation supplement earned (5th week) two years before", example=0.0)
    start_vacation_supplement_used_fifth_holiday_week_two_years_before: Optional[float] = Field(default=None, description="Start vacation supplement used (5th week) two years before", example=0.0)
    start_number_of_vacation_days_fifth_holiday_week_three_years_before: Optional[float] = Field(default=None, description="Start vacation days (5th week) three years before", example=0.0)
    start_number_used_vacation_days_fifth_holiday_week_three_years_before: Optional[float] = Field(default=None, description="Start used vacation days (5th week) three years before", example=0.0)
    start_vacation_pay_gross_fifth_holiday_week_three_years_before: Optional[float] = Field(default=None, description="Start vacation pay gross (5th week) three years before", example=0.0)
    start_vacations_legitimate_salary_fifth_holiday_week_three_years_before: Optional[float] = Field(default=None, description="Start vacations legitimate salary (5th week) three years before", example=0.0)
    start_vacation_supplement_earned_fifth_holiday_week_three_years_before: Optional[float] = Field(default=None, description="Start vacation supplement earned (5th week) three years before", example=0.0)
    start_vacation_supplement_used_fifth_holiday_week_three_years_before: Optional[float] = Field(default=None, description="Start vacation supplement used (5th week) three years before", example=0.0)
    start_vacation_pay_gross_used_fifth_holiday_week_two_years_before: Optional[float] = Field(default=None, description="Start vacation pay gross used (5th week) two years before", example=0.0)
    start_vacation_pay_gross_used_fifth_holiday_week_three_years_before: Optional[float] = Field(default=None, description="Start vacation pay gross used (5th week) three years before", example=0.0)
    start_holiday_hindrance_transferred_days_fifth_holiday_week_current_period: Optional[float] = None
    start_payout_from_fifth_holiday_week_current_period: Optional[float] = None
    start_gross_holiday_pay_transferred_fifth_holiday_week_current_period: Optional[float] = None
    start_lost_gross_holiday_pay_fifth_holiday_week_current_period: Optional[float] = None
    start_paid_days_fifth_holiday_week_current_period: Optional[float] = None
    start_transferred_days_fifth_holiday_week_current_period: Optional[float] = None
    start_transferred_days_used_fifth_holiday_week_current_period: Optional[float] = None
    start_gross_holiday_pay_transferred_fifth_holiday_week_previous_period: Optional[float] = None
    start_holiday_hindrance_transferred_days_fifth_holiday_week_previous_period: Optional[float] = None
    start_payout_from_fifth_holiday_week_previous_period: Optional[float] = None
    start_lost_gross_holiday_pay_fifth_holiday_week_previous_period: Optional[float] = None
    start_paid_days_fifth_holiday_week_previous_period: Optional[float] = None
    start_transferred_days_fifth_holiday_week_previous_period: Optional[float] = None
    start_transferred_days_used_fifth_holiday_week_previous_period: Optional[float] = None
    start_holiday_hindrance_transferred_days_fifth_holiday_week_two_periods_before: Optional[float] = None
    start_lost_gross_holiday_pay_fifth_holiday_week_two_periods_before: Optional[float] = None
    start_holiday_hindrance_transferred_days_fifth_holiday_week_three_periods_before: Optional[float] = None
    start_transferred_days_fifth_holiday_week_three_periods_before: Optional[float] = None
    start_transferred_days_used_fifth_holiday_week_three_periods_before: Optional[float] = None
    start_gross_holiday_pay_transferred_fifth_holiday_week_three_periods_before: Optional[float] = None
    start_lost_gross_holiday_pay_fifth_holiday_week_three_periods_before: Optional[float] = None
    start_earned_care_days_three_years_before: Optional[float] = None
    start_used_care_days_three_years_before: Optional[float] = None
    start_earned_free_vacation_days_three_years_before: Optional[float] = None
    start_used_free_vacation_days_three_years_before: Optional[float] = None
    start_holday_at_own_expense_three_years_before: Optional[float] = None
    start_holday_at_own_expense_three_years_before_saldo: Optional[float] = None
    start_holiday_hindrance_used_days_fifth_holiday_week_two_periods_before: Optional[float] = None
    start_holiday_hindrance_used_days_fifth_holiday_week_three_periods_before: Optional[float] = None
    start_holiday_pay_gross_used_fifth_holiday_week_current_period: Optional[float] = None
    start_holiday_pay_gross_used_fifth_holiday_week_previous_period: Optional[float] = None
    start_transferred_gross_holiday_pay_used_fifth_holiday_week_previous_period: Optional[float] = None
    start_transferred_gross_holiday_pay_used_fifth_holiday_week_three_periods_before: Optional[float] = None
    start_holiday_hindrance_used_days_fifth_holiday_week_previous_period: Optional[float] = None
    start_holiday_pay_gross_used_two_periods_before: Optional[float] = None
    start_holiday_pay_gross_used_three_periods_before: Optional[float] = None
    start_paid_days_fifth_holiday_week_two_periods_before: Optional[float] = None
    start_transferred_days_fifth_holiday_week_two_periods_before: Optional[float] = None
    start_transferred_days_used_fifth_holiday_week_two_periods_before: Optional[float] = None
    start_payout_from_fifth_holiday_week_two_periods_before: Optional[float] = None
    start_gross_holiday_pay_transferred_fifth_holiday_week_two_periods_before: Optional[float] = None
    start_transferred_gross_holiday_pay_used_fifth_holiday_week_two_periods_before: Optional[float] = None


class EmploymentData(BaseModel):
    employee_number: Optional[str] = Field(None, max_length=15, description="Internal employee number", example="E-1001")
    extra_employee_number: Optional[str] = Field(None, max_length=15, description="Secondary employee number", example="EXT-55")
    employment_date: Optional[datetime] = None
    department_id: Optional[int] = Field(None, ge=-2147483648, le=2147483647, description="Department ID (int)", example=10)

class EmployeeCreate(BaseModel):
    iban: Optional[str] = Field(
        None, max_length=34, alias='iban',
        description="International Bank Account Number", example="DK5000400440116243"
    )
    swift: Optional[str] = Field(
        None, max_length=11, alias='swift',
        description="SWIFT/BIC code", example="NDEADKKK"
    )
    is_foreign: Optional[bool] = Field(
        None, alias='isForeign',
        description="Is the employee foreign resident?", example=False
    )
    is_cpr_validated: Optional[bool] = Field(
        None, alias='isCprValidated',
        description="Whether CPR has been validated", example=False
    )
    employee_number: Optional[str] = Field(
        None, alias='employeeNumber',
        description="Internal employee number", example="E-1001"
    )
    extra_employee_number: Optional[str] = Field(
        None, alias='extraEmployeeNumber',
        description="Secondary employee number", example="EXT-55"
    )
    global_value_set_uid: Optional[UUID] = Field(
        None, alias='globalValueSetUid',
        description="Global value set UID", example="00000000-0000-0000-0000-000000000000"
    )
    global_value_uid: Optional[UUID] = Field(
        None, alias='globalValueUid',
        description="Global value UID", example="00000000-0000-0000-0000-000000000000"
    )
    employment_date: Optional[datetime] = Field(
        None, alias='employmentDate',
        description="Employment start date", example="2024-01-01T00:00:00Z"
    )
    ancinity_date: Optional[datetime] = Field(
        None, alias='ancinityDate',
        description="Seniority date", example="2023-06-01T00:00:00Z"
    )
    company_date: Optional[datetime] = Field(
        None, alias='companyDate',
        description="Date of joining the company group", example="2023-06-15T00:00:00Z"
    )
    start_saldo: Optional[StartSaldo] = Field(
        None, alias='startSaldo',
        description="Starting balances (saldo) object", example=None
    )
    employment_data: Optional[EmploymentData] = Field(
        None, alias='employmentData',
        description="Employment metadata (numbers, department)", example=None
    )
    address: Optional[str] = Field(
        None, max_length=50, alias='address',
        description="Street address", example="Main Street 1"
    )
    city: Optional[str] = Field(
        None, max_length=50, alias='city',
        description="City name", example="Copenhagen"
    )
    postal_number: Optional[str] = Field(
        None, max_length=20, alias='postalNumber',
        description="Postal/ZIP code", example="2100"
    )
    mobile_phone: Optional[str] = Field(
        None, max_length=50, alias='mobilePhone',
        description="Mobile phone number", example="+45 12 34 56 78"
    )
    konto_number: Optional[str] = Field(
        None, alias='kontoNumber',
        description="Bank account (konto) number", example="1234567890"
    )
    reg_number: Optional[str] = Field(
        None, alias='regNumber',
        description="Bank registration number", example="0001"
    )
    language: Optional[EmployeeLanguage] = Field(
        None, alias='language',
        description="Preferred language object", example={"name": "English"}
    )
    tin_number: Optional[str] = Field(
        None, alias='tinNumber',
        description="Tax identification number", example="12345678"
    )
    cpr: Optional[str] = Field(
        None, max_length=30, alias='cpr',
        description="Danish CPR (personal ID)", example="010190-1234"
    )
    email: Optional[str] = Field(
        None, max_length=75, alias='email',
        description="Email address", example="john.doe@example.com"
    )
    name: str = Field(
        ..., max_length=150, alias='name',
        description="Full name", example="John Doe"
    )
    linked_in: Optional[str] = Field(
        None, max_length=200, alias='linkedIn',
        description="LinkedIn profile URL", example="https://www.linkedin.com/in/johndoe"
    )
    car_registration_number: Optional[str] = Field(
        None, max_length=20, alias='carRegistrationNumber',
        description="Car registration number", example="AB12345"
    )
    country_code: Optional[str] = Field(
        None, max_length=5, alias='countryCode',
        description="ISO country code", example="DK"
    )

    class Config:
        populate_by_name = True


class EmployeeUpdate(BaseModel):
    """Partial update for an employee (PATCH). All fields optional."""

    # Contact / identity
    cpr: Optional[str] = Field(
        None, alias='cpr',
        description="Danish CPR (personal ID)", example="010190-1234"
    )
    email: Optional[str] = Field(
        None, alias='email',
        description="Email address", example="john.doe@example.com"
    )
    name: Optional[str] = Field(
        None, alias='name',
        description="Full name", example="John Doe"
    )
    linked_in: Optional[str] = Field(
        None, alias='linkedIn',
        description="LinkedIn profile URL", example="https://www.linkedin.com/in/johndoe"
    )
    car_registration_number: Optional[str] = Field(
        None, alias='carRegistrationNumber',
        description="Car registration number", example="AB12345"
    )

    # Address & communication
    address: Optional[str] = Field(
        None, alias='address',
        description="Street address", example="Main Street 1"
    )
    city: Optional[str] = Field(
        None, alias='city',
        description="City name", example="Copenhagen"
    )
    postal_number: Optional[str] = Field(
        None, alias='postalNumber',
        description="Postal/ZIP code", example="2100"
    )
    mobile_phone: Optional[str] = Field(
        None, alias='mobilePhone',
        description="Mobile phone number", example="+45 12 34 56 78"
    )

    # Banking & payment
    konto_number: Optional[str] = Field(
        None, alias='kontoNumber',
        description="Bank account (konto) number", example="1234567890"
    )
    reg_number: Optional[str] = Field(
        None, alias='regNumber',
        description="Bank registration number", example="0001"
    )
    iban: Optional[str] = Field(
        None, alias='iban',
        description="International Bank Account Number", example="DK5000400440116243"
    )
    swift: Optional[str] = Field(
        None, alias='swift',
        description="SWIFT/BIC code", example="NDEADKKK"
    )

    # Miscellaneous personal settings
    language: Optional[EmployeeLanguage] = Field(
        None, alias='language',
        description="Preferred language object", example={"name": "English"}
    )
    country_code: Optional[str] = Field(
        None, alias='countryCode',
        description="ISO country code", example="DK"
    )

    # Flags
    is_foreign: Optional[bool] = Field(
        False, alias='isForeign',
        description="Is the employee foreign resident?", example=False
    )
    is_cpr_validated: Optional[bool] = Field(
        False, alias='isCprValidated',
        description="Whether CPR has been validated", example=False
    )

    # Employment details
    # employment_date: Optional[datetime] = Field(
    #     None, alias='employmentDate',
    #     description="Employment start date", example="2024-01-01T00:00:00Z"
    # )
    ancinity_date: Optional[datetime] = Field(
        None, alias='ancinityDate',
        description="Seniority date", example="2023-06-01T00:00:00Z"
    )
    employee_number: Optional[str] = Field(
       None, alias='employeeNumber',
       description="Internal employee number", example="E-1001"
    )
    extra_employee_number: Optional[str] = Field(
        None, alias='extraEmployeeNumber',
        description="Secondary employee number", example="EXT-55"
    )
    # department_id: Optional[int] = Field(
    #     None, alias='departmentId',
    #     description="Department numeric identifier", example=10
    # )
    company_department_uid: Optional[UUID] = Field(
        None,
        alias='companyDepartmentUid',
        description="Target department UID", example="00000000-0000-0000-0000-000000000000"
    )

    # Balances / saldo information (kept in a dedicated sub-object)
    start_saldo: Optional[StartSaldo] = Field(
        None, alias='startSaldo',
        description="Starting balances (saldo) object", example=None
    )

    # ------------------------- Added fields -------------------------
    salary_type: Optional[int] = Field(None, alias='salaryType', description="Salary type code", example=1)
    income_type: Optional[int] = Field(None, alias='incomeType', description="Income type code", example=0)
    tax: Optional[int] = Field(None, alias='tax', description="Tax code", example=0)
    revenue_type: Optional[int] = Field(None, alias='revenueType', description="Revenue type code", example=0)
    maternity_type: Optional[int] = Field(None, alias='maternityType', description="Maternity type code", example=0)
    atp_type: Optional[str] = Field(None, alias='atpType', description="ATP type string", example="A")
    additional_tax_rate: Optional[float] = Field(None, alias='additionalTaxRate', description="Additional tax rate (percentage)", example=3.5)
    enable_file_transfer: Optional[bool] = Field(None, alias='enableFileTransfer', description="Enable file transfer flag", example=False)
    insurance_category: Optional[int] = Field(None, alias='insuranceCategory', description="Insurance category code", example=0)
    company_cvr_number: Optional[str] = Field(None, alias='companyCvrNumber', description="Company CVR number", example="12345678")
    is_employee_look_like_other_employee: Optional[bool] = Field(None, alias='isEmployeeLookLikeOtherEmployee', description="Employee modeled after another employee", example=False)
    look_like_employee_uid: Optional[UUID] = Field(None, alias='lookLikeEmployeeUid', description="UID of the employee to mirror", example="00000000-0000-0000-0000-000000000000")
    # title: Optional[str] = Field(None, alias='title', description="Job title", example="Engineer")
    is_active: Optional[bool] = Field(None, alias='isActive', description="Active status", example=True)
    job_description: Optional[str] = Field(None, alias='jobDescription', description="Job description text", example="Backend developer")
    company_cost_center_uid: Optional[UUID] = Field(None, alias='companyCostCenterUid', description="Company cost center UID", example="00000000-0000-0000-0000-000000000000")
    company_profit_center_uid: Optional[UUID] = Field(None, alias='companyProfitCenterUid', description="Company profit center UID", example="00000000-0000-0000-0000-000000000000")
    booking_group_uid: Optional[UUID] = Field(None, alias='bookingGroupUid', description="Booking group UID", example="00000000-0000-0000-0000-000000000000")
    company_date: Optional[datetime] = Field(None, alias='companyDate', description="Company date (ISO 8601)", example="2023-06-15T00:00:00Z")
    holiday_pay_receiver_uid: Optional[UUID] = Field(None, alias='holidayPayReceiverUid', description="Holiday pay receiver UID", example="00000000-0000-0000-0000-000000000000")
    benefit_package_amount: Optional[float] = Field(None, alias='benefitPackageAmount', description="Benefit package amount", example=500.0)
    benefit_package_amount_type: Optional[int] = Field(None, alias='benefitPackageAmountType', description="Benefit package amount type code", example=0)
    holiday_payment_amount: Optional[float] = Field(None, alias='holidayPaymentAmount', description="Holiday payment amount", example=1000.0)
    holiday_payment_type: Optional[int] = Field(None, alias='holidayPaymentType', description="Holiday payment type code", example=0)
    benefit_package_type: Optional[int] = Field(None, alias='benefitPackageType', description="Benefit package type code", example=0)
    include_benefit_package_in_pension: Optional[bool] = Field(None, alias='includeBenefitPackageInPension', description="Include benefit package in pension base", example=True)
    holiday_pay_rate: Optional[float] = Field(None, alias='holidayPayRate', description="Holiday pay rate (percentage)", example=12.5)
    benefit_package_two_amount: Optional[float] = Field(None, alias='benefitPackageTwoAmount', description="Benefit package two amount", example=200.0)
    benefit_package_two_type: Optional[int] = Field(None, alias='benefitPackageTwoType', description="Benefit package two type code", example=0)
    include_benefit_package_two_in_pension: Optional[bool] = Field(None, alias='includeBenefitPackageTwoInPension', description="Include benefit package two in pension base", example=True)
    is_absence_freechoice_enabled: Optional[bool] = Field(None, alias='isAbsenceFreechoiceEnabled', description="Absence freechoice feature enabled", example=False)
    holiday_saved_rate: Optional[float] = Field(None, alias='holidaySavedRate', description="Holiday saved rate", example=1.0)
    sh_month_select: Optional[List[str]] = Field(None, alias='shMonthSelect', description="Selected SH months", example=["JAN","FEB"])
    benefit_package_payout_months: Optional[List[str]] = Field(None, alias='benefitPackagePayoutMonths', description="Benefit package payout months", example=["MAR","SEP"])
    horesta_supplement: Optional[float] = Field(None, alias='horestaSupplement', description="HORESTA supplement amount", example=50.0)
    sh_payout_netto_month_select: Optional[List[str]] = Field(None, alias='shPayoutNettoMonthSelect', description="Selected SH net payout months", example=["JUN","DEC"])
    transfer_netto: Optional[bool] = Field(None, alias='transferNetto', description="Transfer net option enabled", example=False)
    monthly_salary: Optional[float] = Field(None, alias='monthlySalary', description="Monthly salary", example=32000.0)
    salary_mode: Optional[int] = Field(None, alias='salaryMode', description="Salary mode code", example=0)
    kr_rate: Optional[float] = Field(None, alias='krRate', description="Krone rate", example=120.0)
    number_of_working_days: Optional[float] = Field(None, alias='numberOfWorkingDays', description="Number of working days", example=21.5)
    salary_payout_period: Optional[int] = Field(None, alias='salaryPayoutPeriod', description="Salary payout period code", example=1)
    holidays: Optional[float] = Field(None, alias='holidays', description="Holiday days", example=25.0)
    max_loan: Optional[float] = Field(None, alias='maxLoan', description="Maximum loan amount", example=5000.0)
    is_automatic_payroll: Optional[bool] = Field(None, alias='isAutomaticPayroll', description="Automatic payroll enabled", example=False)
    holiday_days_per_year: Optional[float] = Field(None, alias='holidayDaysPerYear', description="Holiday days per year", example=25.0)
    holiday_supplement: Optional[float] = Field(None, alias='holidaySupplement', description="Holiday supplement amount", example=1.5)
    additional_days_per_year: Optional[float] = Field(None, alias='additionalDaysPerYear', description="Additional days per year", example=5.0)
    care_days_per_year: Optional[float] = Field(None, alias='careDaysPerYear', description="Care days per year", example=2.0)
    maximum_number_of_days_used_in_advance: Optional[float] = Field(None, alias='maximumNumberOfDaysUsedInAdvance', description="Max days used in advance", example=5.0)
    holiday_registry_code: Optional[int] = Field(None, alias='holidayRegistryCode', description="Holiday registry code", example=0)
    holiday_handling_code: Optional[int] = Field(None, alias='holidayHandlingCode', description="Holiday handling code", example=0)
    group_insurance: Optional[float] = Field(None, alias='groupInsurance', description="Group insurance amount", example=300.0)
    is_insurance_taxable: Optional[bool] = Field(None, alias='isInsuranceTaxable', description="Insurance taxable flag", example=True)
    is_insurance_inclusive_in_pension: Optional[bool] = Field(None, alias='isInsuranceInclusiveInPension', description="Insurance included in pension", example=False)
    number_of_hours: Optional[float] = Field(None, alias='numberOfHours', description="Number of hours", example=160.0)
    number_of_hours_fixed: Optional[float] = Field(None, alias='numberOfHoursFixed', description="Fixed number of hours", example=160.0)
    # monthly_salary_fixed_base: Optional[float] = Field(None, alias='monthlySalaryFixedBase', description="Monthly salary fixed base", example=30000.0)
    pension_insitute_type: Optional[int] = Field(None, alias='pensionInsituteType', description="Pension institute type code", example=0)
    labour_company_pension: Optional[float] = Field(None, alias='labourCompanyPension', description="Company pension contribution", example=1000.0)
    labour_private_pension: Optional[float] = Field(None, alias='labourPrivatePension', description="Private pension contribution", example=500.0)
    labour_benefits_package_for_pension: Optional[float] = Field(None, alias='labourBenefitsPackageForPension', description="Benefits package amount for pension", example=300.0)
    labour_agreement_code: Optional[str] = Field(None, alias='labourAgreementCode', description="Labour agreement code", example="LA-01")
    extra_holiday_entitlement_per_payroll: Optional[float] = Field(None, alias='extraHolidayEntitlementPerPayroll', description="Extra holiday entitlement per payroll", example=0.5)
    # ----------------------- End added fields -----------------------

    class Config:
        populate_by_name = True

class EmployeeEmploymentDataUpdate(BaseModel):
    """Update schema for employee employment data. (employmentData)"""
    employee_number: Optional[str] = Field(
        None, alias='employeeNumber',
        description="Internal employee number", example="E-1001"
    )
    extra_employee_number: Optional[str] = Field(
        None, alias='extraEmployeeNumber',
        description="Secondary employee number", example="EXT-55"
    )
    employment_date: Optional[datetime] = Field(
        None, alias='employmentDate',
        description="Employment start date", example="2024-01-01T00:00:00Z"
    )
    department_id: Optional[int] = Field(
        None, alias='departmentId',
        description="Department numeric identifier", example=10
    )

    class Config:
        populate_by_name = True


class EmployeeEmploymentUpdate(BaseModel):
    """Update schema for employee employment data. (employeeEmployment)"""
    salary_type: Optional[int] = Field(None, alias='salaryType', description="Salary type code", example=1)
    p_number: Optional[str] = Field(None, alias='pNumber', description="Employee P-number", example="P12345")
    income_type: Optional[int] = Field(None, alias='incomeType', description="Income type code", example=0)
    tax: Optional[int] = Field(None, alias='tax', description="Tax code", example=0)
    revenue_type: Optional[int] = Field(None, alias='revenueType', description="Revenue type code", example=0)
    maternity_type: Optional[int] = Field(None, alias='maternityType', description="Maternity type code", example=0)
    atp_type: Optional[str] = Field(None, alias='atpType', description="ATP type string", example="A")
    additional_tax_rate: Optional[float] = Field(None, alias='additionalTaxRate', description="Additional tax rate (percentage)", example=3.5)
    enable_file_transfer: Optional[bool] = Field(None, alias='enableFileTransfer', description="Enable file transfer flag", example=False)
    insurance_category: Optional[int] = Field(None, alias='insuranceCategory', description="Insurance category code", example=0)
    company_cvr_number: Optional[str] = Field(None, alias='companyCvrNumber', description="Company CVR number", example="12345678")
    is_employee_look_like_other_employee: Optional[bool] = Field(None, alias='isEmployeeLookLikeOtherEmployee', description="Employee modeled after another employee", example=False)
    look_like_employee_uid: Optional[UUID] = Field(None, alias='lookLikeEmployeeUid', description="UID of the employee to mirror", example="00000000-0000-0000-0000-000000000000")
    title: Optional[str] = Field(None, alias='title', description="Job title", example="Engineer")
    employee_number: Optional[str] = Field(None, alias='employeeNumber', description="Internal employee number", example="E-1001")
    extra_employee_number: Optional[str] = Field(None, alias='extraEmployeeNumber', description="Secondary employee number", example="EXT-55")
    employment_date: Optional[datetime] = Field(None, alias='employmentDate', description="Employment start date", example="2025-10-21T00:00:00Z")
    ancinity_date: Optional[datetime] = Field(None, alias='ancinityDate', description="Seniority date", example="2023-06-01T00:00:00Z")
    is_active: Optional[bool] = Field(None, alias='isActive', description="Active status", example=True)
    job_description: Optional[str] = Field(None, alias='jobDescription', description="Job description text", example="Backend developer")
    company_department_uid: Optional[UUID] = Field(None, alias='companyDepartmentUid', description="Target department UID", example="00000000-0000-0000-0000-000000000000")
    company_cost_center_uid: Optional[UUID] = Field(None, alias='companyCostCenterUid', description="Company cost center UID", example="00000000-0000-0000-0000-000000000000")
    company_profit_center_uid: Optional[UUID] = Field(None, alias='companyProfitCenterUid', description="Company profit center UID", example="00000000-0000-0000-0000-000000000000")
    booking_group_uid: Optional[UUID] = Field(None, alias='bookingGroupUid', description="Booking group UID", example="00000000-0000-0000-0000-000000000000")
    company_date: Optional[datetime] = Field(None, alias='companyDate', description="Company date (ISO 8601)", example="2023-06-15T00:00:00Z")
    work_time_employment_info: Optional[str] = Field(None, alias='workTimeEmploymentInfo', description="Work time employment info", example="Full-time")

    class Config:
        populate_by_name = True


class EmployeeAdditionalUpdate(BaseModel):
    """Update schema for additional employee data. (employeeAditional)"""
    holiday_pay_receiver_uid: Optional[UUID] = Field(None, alias='holidayPayReceiverUid', description="Holiday pay receiver UID", example="00000000-0000-0000-0000-000000000000")
    benefit_package_amount: Optional[float] = Field(None, alias='benefitPackageAmount', description="Benefit package amount", example=500.0)
    benefit_package_amount_type: Optional[int] = Field(None, alias='benefitPackageAmountType', description="Benefit package amount type code", example=0)
    holiday_payment_amount: Optional[float] = Field(None, alias='holidayPaymentAmount', description="Holiday payment amount", example=1000.0)
    holiday_payment_type: Optional[int] = Field(None, alias='holidayPaymentType', description="Holiday payment type code", example=0)
    benefit_package_type: Optional[int] = Field(None, alias='benefitPackageType', description="Benefit package type code", example=0)
    include_benefit_package_in_pension: Optional[bool] = Field(None, alias='includeBenefitPackageInPension', description="Include benefit package in pension base", example=True)
    am_pension: Optional[Dict[str, Any]] = Field(None, alias='amPension', description="AM pension object")
    holiday_pay_rate: Optional[float] = Field(None, alias='holidayPayRate', description="Holiday pay rate (percentage)", example=12.5)
    benefit_package_two_amount: Optional[float] = Field(None, alias='benefitPackageTwoAmount', description="Benefit package two amount", example=200.0)
    benefit_package_two_type: Optional[int] = Field(None, alias='benefitPackageTwoType', description="Benefit package two type code", example=0)
    include_benefit_package_two_in_pension: Optional[bool] = Field(None, alias='includeBenefitPackageTwoInPension', description="Include benefit package two in pension base", example=True)
    is_absence_freechoice_enabled: Optional[bool] = Field(None, alias='isAbsenceFreechoiceEnabled', description="Absence freechoice feature enabled", example=False)
    holiday_saved_rate: Optional[float] = Field(None, alias='holidaySavedRate', description="Holiday saved rate", example=1.0)
    sh_month_select: Optional[List[str]] = Field(None, alias='shMonthSelect', description="Selected SH months", example=["JAN","FEB"])
    benefit_package_payout_months: Optional[List[str]] = Field(None, alias='benefitPackagePayoutMonths', description="Benefit package payout months", example=["MAR","SEP"])
    horesta_supplement: Optional[float] = Field(None, alias='horestaSupplement', description="HORESTA supplement amount", example=50.0)
    special_supplement_type: Optional[str] = Field(None, alias='specialSupplementType', description="Special supplement type", example="TYPE1")
    special_supplement_payout_months: Optional[List[str]] = Field(None, alias='specialSupplementPayoutMonths', description="Special supplement payout months", example=["APR","OCT"])
    sh_payout_netto_month_select: Optional[List[str]] = Field(None, alias='shPayoutNettoMonthSelect', description="Selected SH net payout months", example=["JUN","DEC"])
    transfer_netto: Optional[bool] = Field(None, alias='transferNetto', description="Transfer net option enabled", example=False)
    day_of_prayer_compensation: Optional[float] = Field(None, alias='dayOfPrayerCompensation', description="Day of prayer compensation", example=0.0)
    day_of_prayer_compensation_rule: Optional[str] = Field(None, alias='dayOfPrayerCompensationRule', description="Day of prayer compensation rule", example="RULE-1")
    monthly_salary: Optional[float] = Field(None, alias='monthlySalary', description="Monthly salary", example=32000.0)
    salary_mode: Optional[int] = Field(None, alias='salaryMode', description="Salary mode code", example=0)
    kr_rate: Optional[float] = Field(None, alias='krRate', description="Krone rate", example=120.0)
    number_of_working_days: Optional[float] = Field(None, alias='numberOfWorkingDays', description="Number of working days", example=21.5)
    salary_payout_period: Optional[int] = Field(None, alias='salaryPayoutPeriod', description="Salary payout period code", example=1)
    holidays: Optional[float] = Field(None, alias='holidays', description="Holiday days", example=25.0)
    max_loan: Optional[float] = Field(None, alias='maxLoan', description="Maximum loan amount", example=5000.0)
    is_automatic_payroll: Optional[bool] = Field(None, alias='isAutomaticPayroll', description="Automatic payroll enabled", example=False)
    holiday_days_per_year: Optional[float] = Field(None, alias='holidayDaysPerYear', description="Holiday days per year", example=25.0)
    holiday_supplement: Optional[float] = Field(None, alias='holidaySupplement', description="Holiday supplement amount", example=1.5)
    additional_days_per_year: Optional[float] = Field(None, alias='additionalDaysPerYear', description="Additional days per year", example=5.0)
    care_days_per_year: Optional[float] = Field(None, alias='careDaysPerYear', description="Care days per year", example=2.0)
    maximum_number_of_days_used_in_advance: Optional[float] = Field(None, alias='maximumNumberOfDaysUsedInAdvance', description="Max days used in advance", example=5.0)
    holiday_registry_code: Optional[int] = Field(None, alias='holidayRegistryCode', description="Holiday registry code", example=0)
    holiday_handling_code: Optional[int] = Field(None, alias='holidayHandlingCode', description="Holiday handling code", example=0)
    group_insurance: Optional[float] = Field(None, alias='groupInsurance', description="Group insurance amount", example=300.0)
    is_insurance_taxable: Optional[bool] = Field(None, alias='isInsuranceTaxable', description="Insurance taxable flag", example=True)
    is_insurance_inclusive_in_pension: Optional[bool] = Field(None, alias='isInsuranceInclusiveInPension', description="Insurance included in pension", example=False)
    number_of_hours: Optional[float] = Field(None, alias='numberOfHours', description="Number of hours", example=160.0)
    number_of_hours_fixed: Optional[float] = Field(None, alias='numberOfHoursFixed', description="Fixed number of hours", example=160.0)
    monthly_salary_fixed_base: Optional[float] = Field(None, alias='monthlySalaryFixedBase', description="Monthly salary fixed base", example=30000.0)
    pension_insitute_type: Optional[int] = Field(None, alias='pensionInsituteType', description="Pension institute type code", example=0)
    labour_company_pension: Optional[float] = Field(None, alias='labourCompanyPension', description="Company pension contribution", example=1000.0)
    labour_private_pension: Optional[float] = Field(None, alias='labourPrivatePension', description="Private pension contribution", example=500.0)
    labour_benefits_package_for_pension: Optional[float] = Field(None, alias='labourBenefitsPackageForPension', description="Benefits package amount for pension", example=300.0)
    labour_agreement_code: Optional[str] = Field(None, alias='labourAgreementCode', description="Labour agreement code", example="LA-01")
    ancinity_rate: Optional[float] = Field(None, alias='ancinityRate', description="Seniority rate", example=0.0)
    extra_holiday_entitlement_per_payroll: Optional[float] = Field(None, alias='extraHolidayEntitlementPerPayroll', description="Extra holiday entitlement per payroll", example=0.5)

    class Config:
        populate_by_name = True


class HolidayPayReceiver(BaseModel):
    cvr: str = Field(description="Holiday pay receiver CVR number", example="12345678")
    id: int = Field(description="Receiver ID (internal numeric)", example=1)
    name: str = Field(description="Receiver name", example="Feriekonto")
    type: int = Field(description="Receiver type code", example=0)
    uid: UUID = Field(description="Receiver UID", example="00000000-0000-0000-0000-000000000000")


class Company(BaseModel):
    association_id: int = Field(description="Association ID", example=12)
    cvr: str = Field(description="Company CVR number", example="12345678")
    extra_holiday_entitlement_in_hours: bool = Field(description="Extra holiday entitlement in hours flag", example=False)
    has_am_pension: bool = Field(description="AM pension enabled flag", example=True)
    has_benefit_package: bool = Field(description="Benefit package enabled flag", example=True)
    has_benefit_package_two: bool = Field(description="Benefit package two enabled flag", example=False)
    has_holiday_payment: bool = Field(description="Holiday payment enabled flag", example=True)
    has_holiday_payment_netto_transfer_or_payout: bool = Field(description="Holiday payment netto transfer or payout flag", example=False)
    id: int = Field(description="Company ID (internal numeric)", example=5)
    insurance_type: int = Field(description="Insurance type code", example=1)
    is_department_income_split_enabled: bool = Field(description="Department income split enabled flag", example=False)
    is_extra_holiday_entitlement_in_hours_enabled: bool = Field(description="Extra holiday entitlement in hours enabled", example=False)
    is_holiday_hindrance_enabled: bool = Field(description="Holiday hindrance enabled flag", example=False)
    is_horesta_supplement_enabled: bool = Field(description="HORESTA supplement enabled flag", example=False)
    is_sh_payout_netto_enabled: bool = Field(description="SH net payout enabled flag", example=False)
    is_transfer_fifth_holiday_week_enabled: bool = Field(description="Transfer fifth holiday week enabled flag", example=False)
    is_use_of_vacation_days_in_advance_enabled: bool = Field(description="Use of vacation days in advance enabled flag", example=False)
    logo_url: Optional[str] = Field(default=None, description="Company logo URL", example="https://example.com/logo.png")
    name: str = Field(description="Company name", example="Acme A/S")
    p_number: str = Field(description="Company P-number", example="P12345")
    uid: UUID = Field(description="Company UID", example="00000000-0000-0000-0000-000000000000")


class CostCenter(BaseModel):
    cost_center_code: str = Field(description="Cost center code", example="FIN")
    cost_center_name: str = Field(description="Cost center name", example="Finance")
    employee_uids: Optional[List[UUID]] = Field(default=None, description="Employee UIDs in the cost center", example=["00000000-0000-0000-0000-000000000000"])
    id: int = Field(description="Cost center ID (internal numeric)", example=10)
    number_of_employees: int = Field(description="Number of employees in cost center", example=42)
    type: Optional[str] = Field(default=None, description="Dimension type (cost/profit)", example="cost")
    uid: UUID = Field(description="Cost center UID", example="00000000-0000-0000-0000-000000000000")


class Department(BaseModel):
    has_work_schema: bool = Field(description="Whether department has a work schema", example=True)
    id: int = Field(description="Department ID (internal numeric)", example=15)
    name: str = Field(description="Department name", example="Sales")
    number: str = Field(description="Department number/code", example="D-100")
    uid: UUID = Field(description="Department UID", example="00000000-0000-0000-0000-000000000000")


class EmployeeDepartmentIncomeSplit(BaseModel):
    department_name: str
    department_number: str
    department_uid: UUID
    id: int
    percentage: float
    type: str
    uid: UUID


class CompanyGlobalValueReferenceUidsPair(BaseModel):
    company_global_value_uid: UUID
    reference_uid: Optional[UUID] = None


class GlobalValueInformation(BaseModel):
    company_global_value_reference_uids_pairs: List[CompanyGlobalValueReferenceUidsPair]
    is_available_in_company: bool
    is_employee_assigned: bool
    type: int


class CompanyGlobalValueInformation(BaseModel):
    company_global_value_name: str
    company_global_value_number: str
    company_global_value_uid: UUID
    reference_uid: Optional[UUID] = None


class GlobalValueInSetAssignmentDto(BaseModel):
    company_global_value_information: List[CompanyGlobalValueInformation]
    reference_uids: List[Optional[UUID]]
    type: int


class GlobalValueSetInformation(BaseModel):
    global_value_in_set_assignment_dto: List[GlobalValueInSetAssignmentDto]
    global_value_set_name: str
    global_value_set_number: str
    global_value_set_uid: UUID


class SaldoHolidayPeriod(BaseModel):
    can_edit_fifth_holiday_week_fields: bool
    has_fifth_holiday_week_payout: bool
    period_type: int
    saldo_type: int
    year: float


class PutEmployeeAsyncRequest(BaseModel):
    update_employee_base: Dict[str, Any] = Field(alias="updateEmployeeBase", description="Employee base fields to update", example={"name": "John"})
    start_saldo: Dict[str, Any] = Field(alias="startSaldo", description="Starting saldo fields", example={"startHours": 10})
    employee_employment: Dict[str, Any] = Field(alias="employeeEmployment", description="Employment fields payload", example={"departmentId": 10})
    employe_aditional: Dict[str, Any] = Field(alias="employeeAditional", description="Additional employee fields", example={"title": "Engineer"})
    class Config:
        populate_by_name = True




class EmployeePatch(BaseModel):
    """
    Flat schema for Employee PATCH operations.
    - All fields optional
    - Aliases correspond exactly to JSON Patch path property names (PascalCase)
    - This model allows extra fields for forward compatibility
    """

    # Identity & contact
    cpr: Optional[str] = Field(default=None, alias='Cpr')
    email: Optional[str] = Field(default=None, alias='Email')
    name: Optional[str] = Field(default=None, alias='Name')
    linked_in: Optional[str] = Field(default=None, alias='LinkedIn')
    car_registration_number: Optional[str] = Field(default=None, alias='CarRegistrationNumber')
    address: Optional[str] = Field(default=None, alias='Address')
    city: Optional[str] = Field(default=None, alias='City')
    postal_number: Optional[str] = Field(default=None, alias='PostalNumber')
    mobile_phone: Optional[str] = Field(default=None, alias='MobilePhone')

    # Banking & misc
    konto_number: Optional[str] = Field(default=None, alias='KontoNumber')
    reg_number: Optional[str] = Field(default=None, alias='RegNumber')
    iban: Optional[str] = Field(default=None, alias='Iban')
    swift: Optional[str] = Field(default=None, alias='Swift')
    country_code: Optional[str] = Field(default=None, alias='CountryCode')

    # Language as object
    language: Optional[str] = Field(default=None, alias='Language')

    # Flags
    is_foreign: Optional[bool] = Field(default=None, alias='IsForeign')
    is_cpr_validated: Optional[bool] = Field(default=None, alias='IsCprValidated')

    # Employment
    employment_date: Optional[Any] = Field(default=None, alias='EmploymentDate')
    ancinity_date: Optional[Any] = Field(default=None, alias='AncinityDate')
    employee_number: Optional[str] = Field(default=None, alias='EmployeeNumber')
    extra_employee_number: Optional[str] = Field(default=None, alias='ExtraEmployeeNumber')
    department_id: Optional[int] = Field(default=None, alias='DepartmentId')
    company_department_uid: Optional[str] = Field(default=None, alias='CompanyDepartmentUid')

    # Start saldo (subset; extend as needed)
    start_g_days: Optional[float] = Field(default=None, alias='StartGDays')
    start_hours: Optional[float] = Field(default=None, alias='StartHours')
    start_time_off_good: Optional[float] = Field(default=None, alias='StartTimeOffGood')
    start_time_off_amount: Optional[float] = Field(default=None, alias='StartTimeOffAmount')
    start_am_income: Optional[float] = Field(default=None, alias='StartAmIncome')
    start_contributory_income: Optional[float] = Field(default=None, alias='StartContributoryIncome')
    start_one_time_income: Optional[float] = Field(default=None, alias='StartOneTimeIncome')
    start_b_income_with_am: Optional[float] = Field(default=None, alias='StartBIncomeWithAm')
    start_b_income_without_am: Optional[float] = Field(default=None, alias='StartBIncomeWithoutAm')
    start_atp: Optional[float] = Field(default=None, alias='StartAtp')
    start_am: Optional[float] = Field(default=None, alias='StartAm')
    start_a_skat: Optional[float] = Field(default=None, alias='StartASkat')
    start_health_insurance: Optional[float] = Field(default=None, alias='StartHealthInsurance')
    start_company_car: Optional[float] = Field(default=None, alias='StartCompanyCar')
    start_company_lodging: Optional[float] = Field(default=None, alias='StartCompanyLodging')
    start_mileage: Optional[float] = Field(default=None, alias='StartMileage')
    start_mileage_low_rate: Optional[float] = Field(default=None, alias='StartMileageLowRate')
    start_travel_allowance: Optional[float] = Field(default=None, alias='StartTravelAllowance')
    start_personal_pension: Optional[float] = Field(default=None, alias='StartPersonalPension')
    start_pension_from_company: Optional[float] = Field(default=None, alias='StartPensionFromCompany')
    start_group_life: Optional[float] = Field(default=None, alias='StartGroupLife')
    start_group_life2: Optional[float] = Field(default=None, alias='StartGroupLife2')
    start_personal_amp: Optional[float] = Field(default=None, alias='StartPersonalAmp')
    start_company_amp: Optional[float] = Field(default=None, alias='StartCompanyAmp')
    start_net_holiday_pay: Optional[float] = Field(default=None, alias='StartNetHolidayPay')
    start_number_of_vacation_days: Optional[float] = Field(default=None, alias='StartNumberOfVacationDays')
    start_holiday_supplement_value: Optional[float] = Field(default=None, alias='StartHolidaySupplementValue')
    start_benefits_package_saldo: Optional[float] = Field(default=None, alias='StartBenefitsPackageSaldo')
    start_benefits_package_earned: Optional[float] = Field(default=None, alias='StartBenefitsPackageEarned')
    start_benefits_package_two_saldo: Optional[float] = Field(default=None, alias='StartBenefitsPackageTwoSaldo')
    start_benefits_package_two_earned: Optional[float] = Field(default=None, alias='StartBenefitsPackageTwoEarned')
    start_vacations_legitimate_salary: Optional[float] = Field(default=None, alias='StartVacationsLegitimateSalary')
    start_free_phone: Optional[float] = Field(default=None, alias='StartFreePhone')
    start_am_contributions_wages_and_holidaypay: Optional[float] = Field(default=None, alias='StartAmContributionsWagesAndHolidaypay')
    start_number_of_vacation_days_two_periods_before: Optional[float] = Field(default=None, alias='StartNumberOfVacationDaysTwoPeriodsBefore')
    start_number_of_vacation_days_previous_period: Optional[float] = Field(default=None, alias='StartNumberOfVacationDaysPreviousPeriod')
    start_number_of_vacation_days_frozen_period: Optional[float] = Field(default=None, alias='StartNumberOfVacationDaysFrozenPeriod')
    start_number_of_vacation_days_current_period: Optional[float] = Field(default=None, alias='StartNumberOfVacationDaysCurrentPeriod')
    start_holiday_supplement_two_periods_before: Optional[float] = Field(default=None, alias='StartHolidaySupplementTwoPeriodsBefore')
    start_holiday_supplement_previous_period: Optional[float] = Field(default=None, alias='StartHolidaySupplementPreviousPeriod')
    start_holiday_supplement_current_period: Optional[float] = Field(default=None, alias='StartHolidaySupplementCurrentPeriod')
    start_holiday_payment_saved: Optional[float] = Field(default=None, alias='StartHolidayPaymentSaved')
    start_holiday_payment_advance: Optional[float] = Field(default=None, alias='StartHolidayPaymentAdvance')
    start_holiday_payment_advance_year_before: Optional[float] = Field(default=None, alias='StartHolidayPaymentAdvanceYearBefore')
    start_holiday_payment_saved_year_before: Optional[float] = Field(default=None, alias='StartHolidayPaymentSavedYearBefore')
    start_holiday_payment_saved_netto_year_before: Optional[float] = Field(default=None, alias='StartHolidayPaymentSavedNettoYearBefore')
    start_holiday_payment_saved_netto: Optional[float] = Field(default=None, alias='StartHolidayPaymentSavedNetto')
    start_holiday_payment_saldo_netto: Optional[float] = Field(default=None, alias='StartHolidayPaymentSaldoNetto')
    start_used_vacation_day_units_current_period: Optional[float] = Field(default=None, alias='StartUsedVacationDayUnitsCurrentPeriod')
    start_used_vacation_day_units_previous_period: Optional[float] = Field(default=None, alias='StartUsedVacationDayUnitsPreviousPeriod')
    start_used_vacation_day_units_two_periods_before: Optional[float] = Field(default=None, alias='StartUsedVacationDayUnitsTwoPeriodsBefore')
    start_used_vacation_day_units_frozen_period: Optional[float] = Field(default=None, alias='StartUsedVacationDayUnitsFrozenPeriod')
    start_used_holiday_supplement_current_period: Optional[float] = Field(default=None, alias='StartUsedHolidaySupplementCurrentPeriod')
    start_used_holiday_supplement_previous_period: Optional[float] = Field(default=None, alias='StartUsedHolidaySupplementPreviousPeriod')
    start_used_holiday_supplement_two_periods_before: Optional[float] = Field(default=None, alias='StartUsedHolidaySupplementTwoPeriodsBefore')
    start_earned_vacations_legitimate_salary_amount_previous_period: Optional[float] = Field(default=None, alias='StartEarnedVacationsLegitimateSalaryAmountPreviousPeriod')
    start_earned_vacations_legitimate_salary_amount_two_periods_before: Optional[float] = Field(default=None, alias='StartEarnedVacationsLegitimateSalaryAmountTwoPeriodsBefore')
    start_earned_vacations_legitimate_salary_amount_frozen_period: Optional[float] = Field(default=None, alias='StartEarnedVacationsLegitimateSalaryAmountFrozenPeriod')
    start_earned_holiday_pay_net_amount_previous_period: Optional[float] = Field(default=None, alias='StartEarnedHolidayPayNetAmountPreviousPeriod')
    start_earned_holiday_pay_net_amount_two_periods_before: Optional[float] = Field(default=None, alias='StartEarnedHolidayPayNetAmountTwoPeriodsBefore')
    start_earned_holiday_pay_net_amount_frozen_period: Optional[float] = Field(default=None, alias='StartEarnedHolidayPayNetAmountFrozenPeriod')
    start_earned_holiday_pay_net_amount_current_period: Optional[float] = Field(default=None, alias='StartEarnedHolidayPayNetAmountCurrentPeriod')
    start_used_holiday_pay_net_amount_current_period: Optional[float] = Field(default=None, alias='StartUsedHolidayPayNetAmountCurrentPeriod')
    start_used_holiday_pay_net_amount_previous_period: Optional[float] = Field(default=None, alias='StartUsedHolidayPayNetAmountPreviousPeriod')
    start_used_holiday_pay_net_amount_two_periods_before: Optional[float] = Field(default=None, alias='StartUsedHolidayPayNetAmountTwoPeriodsBefore')
    start_used_holiday_pay_net_amount_frozen_period: Optional[float] = Field(default=None, alias='StartUsedHolidayPayNetAmountFrozenPeriod')
    start_earned_care_days_two_years_before: Optional[float] = Field(default=None, alias='StartEarnedCareDaysTwoYearsBefore')
    start_earned_care_days_year_before: Optional[float] = Field(default=None, alias='StartEarnedCareDaysYearBefore')
    start_earned_care_days_current_year: Optional[float] = Field(default=None, alias='StartEarnedCareDaysCurrentYear')
    start_used_care_days_two_years_before: Optional[float] = Field(default=None, alias='StartUsedCareDaysTwoYearsBefore')
    start_used_care_days_year_before: Optional[float] = Field(default=None, alias='StartUsedCareDaysYearBefore')
    start_used_care_days_current_year: Optional[float] = Field(default=None, alias='StartUsedCareDaysCurrentYear')
    start_earned_free_vacation_days_two_years_before: Optional[float] = Field(default=None, alias='StartEarnedFreeVacationDaysTwoYearsBefore')
    start_earned_free_vacation_days_year_before: Optional[float] = Field(default=None, alias='StartEarnedFreeVacationDaysYearBefore')
    start_earned_free_vacation_days_current_year: Optional[float] = Field(default=None, alias='StartEarnedFreeVacationDaysCurrentYear')
    start_used_free_vacation_days_two_years_before: Optional[float] = Field(default=None, alias='StartUsedFreeVacationDaysTwoYearsBefore')
    start_used_free_vacation_days_year_before: Optional[float] = Field(default=None, alias='StartUsedFreeVacationDaysYearBefore')
    start_used_free_vacation_days_current_year: Optional[float] = Field(default=None, alias='StartUsedFreeVacationDaysCurrentYear')
    start_earned_holiday_pay_gross_two_periods_before: Optional[float] = Field(default=None, alias='StartEarnedHolidayPayGrossTwoPeriodsBefore')
    start_earned_holiday_pay_gross_previous_period: Optional[float] = Field(default=None, alias='StartEarnedHolidayPayGrossPreviousPeriod')
    start_earned_holiday_pay_gross_current_period: Optional[float] = Field(default=None, alias='StartEarnedHolidayPayGrossCurrentPeriod')
    start_earned_holiday_pay_gross_frozen_period: Optional[float] = Field(default=None, alias='StartEarnedHolidayPayGrossFrozenPeriod')
    start_used_holiday_pay_gross_two_periods_before: Optional[float] = Field(default=None, alias='StartUsedHolidayPayGrossTwoPeriodsBefore')
    start_used_holiday_pay_gross_previous_period: Optional[float] = Field(default=None, alias='StartUsedHolidayPayGrossPreviousPeriod')
    start_used_holiday_pay_gross_current_period: Optional[float] = Field(default=None, alias='StartUsedHolidayPayGrossCurrentPeriod')
    start_used_holiday_pay_gross_frozen_period: Optional[float] = Field(default=None, alias='StartUsedHolidayPayGrossFrozenPeriod')
    start_flex_hours: Optional[float] = Field(default=None, alias='StartFlexHours')
    start_time_in_lieu_earned_hours: Optional[float] = Field(default=None, alias='StartTimeInLieuEarnedHours')
    start_time_in_lieu_earned_amount: Optional[float] = Field(default=None, alias='StartTimeInLieuEarnedAmount')
    start_health_insurance_no_am_pension: Optional[float] = Field(default=None, alias='StartHealthInsuranceNoAmPension')
    start_health_insurance_no_am_pension_no_vacation_entitled_money: Optional[float] = Field(default=None, alias='StartHealthInsuranceNoAmPensionNoVacationEntitledMoney')
    start_not_covered_by_triviality: Optional[float] = Field(default=None, alias='StartNotCoveredByTriviality')
    start_christmas_gifts_benefit: Optional[float] = Field(default=None, alias='StartChristmasGiftsBenefit')
    start_other_benefit: Optional[float] = Field(default=None, alias='StartOtherBenefit')
    start_negative_salary_saldo: Optional[float] = Field(default=None, alias='StartNegativeSalarySaldo')
    start_anniversary_bonus_saldo: Optional[float] = Field(default=None, alias='StartAnniversaryBonusSaldo')
    start_severance_saldo: Optional[float] = Field(default=None, alias='StartSeveranceSaldo')
    start_travel_allowance_without_payment: Optional[float] = Field(default=None, alias='StartTravelAllowanceWithoutPayment')
    start_holday_at_own_expense_two_years_before: Optional[float] = Field(default=None, alias='StartHoldayAtOwnExpenseTwoYearsBefore')
    start_holday_at_own_expense_year_before: Optional[float] = Field(default=None, alias='StartHoldayAtOwnExpenseYearBefore')
    start_holday_at_own_expense_current_year: Optional[float] = Field(default=None, alias='StartHoldayAtOwnExpenseCurrentYear')
    start_holday_at_own_expense_two_years_before_saldo: Optional[float] = Field(default=None, alias='StartHoldayAtOwnExpenseTwoYearsBeforeSaldo')
    start_holday_at_own_expense_year_before_saldo: Optional[float] = Field(default=None, alias='StartHoldayAtOwnExpenseYearBeforeSaldo')
    start_holday_at_own_expense_current_year_saldo: Optional[float] = Field(default=None, alias='StartHoldayAtOwnExpenseCurrentYearSaldo')
    start_number_of_vacation_days_fifth_holiday_week_two_years_before: Optional[float] = Field(default=None, alias='StartNumberOfVacationDaysFifthHolidayWeekTwoYearsBefore')
    start_number_used_vacation_days_fifth_holiday_week_two_years_before: Optional[float] = Field(default=None, alias='StartNumberUsedVacationDaysFifthHolidayWeekTwoYearsBefore')
    start_vacation_pay_gross_fifth_holiday_week_two_years_before: Optional[float] = Field(default=None, alias='StartVacationPayGrossFifthHolidayWeekTwoYearsBefore')
    start_vacations_legitimate_salary_fifth_holiday_week_two_years_before: Optional[float] = Field(default=None, alias='StartVacationsLegitimateSalaryFifthHolidayWeekTwoYearsBefore')
    start_vacation_supplement_earned_fifth_holiday_week_two_years_before: Optional[float] = Field(default=None, alias='StartVacationSupplementEarnedFifthHolidayWeekTwoYearsBefore')
    start_vacation_supplement_used_fifth_holiday_week_two_years_before: Optional[float] = Field(default=None, alias='StartVacationSupplementUsedFifthHolidayWeekTwoYearsBefore')
    start_number_of_vacation_days_fifth_holiday_week_three_years_before: Optional[float] = Field(default=None, alias='StartNumberOfVacationDaysFifthHolidayWeekThreeYearsBefore')
    start_number_used_vacation_days_fifth_holiday_week_three_years_before: Optional[float] = Field(default=None, alias='StartNumberUsedVacationDaysFifthHolidayWeekThreeYearsBefore')
    start_vacation_pay_gross_fifth_holiday_week_three_years_before: Optional[float] = Field(default=None, alias='StartVacationPayGrossFifthHolidayWeekThreeYearsBefore')
    start_vacations_legitimate_salary_fifth_holiday_week_three_years_before: Optional[float] = Field(default=None, alias='StartVacationsLegitimateSalaryFifthHolidayWeekThreeYearsBefore')
    start_vacation_supplement_earned_fifth_holiday_week_three_years_before: Optional[float] = Field(default=None, alias='StartVacationSupplementEarnedFifthHolidayWeekThreeYearsBefore')
    start_vacation_supplement_used_fifth_holiday_week_three_years_before: Optional[float] = Field(default=None, alias='StartVacationSupplementUsedFifthHolidayWeekThreeYearsBefore')
    start_vacation_pay_gross_used_fifth_holiday_week_two_years_before: Optional[float] = Field(default=None, alias='StartVacationPayGrossUsedFifthHolidayWeekTwoYearsBefore')
    start_vacation_pay_gross_used_fifth_holiday_week_three_years_before: Optional[float] = Field(default=None, alias='StartVacationPayGrossUsedFifthHolidayWeekThreeYearsBefore')
    start_holiday_hindrance_transferred_days_fifth_holiday_week_current_period: Optional[float] = Field(default=None, alias='StartHolidayHindranceTransferredDaysFifthHolidayWeekCurrentPeriod')
    start_payout_from_fifth_holiday_week_current_period: Optional[float] = Field(default=None, alias='StartPayoutFromFifthHolidayWeekCurrentPeriod')
    start_gross_holiday_pay_transferred_fifth_holiday_week_current_period: Optional[float] = Field(default=None, alias='StartGrossHolidayPayTransferredFifthHolidayWeekCurrentPeriod')
    start_lost_gross_holiday_pay_fifth_holiday_week_current_period: Optional[float] = Field(default=None, alias='StartLostGrossHolidayPayFifthHolidayWeekCurrentPeriod')
    start_paid_days_fifth_holiday_week_current_period: Optional[float] = Field(default=None, alias='StartPaidDaysFifthHolidayWeekCurrentPeriod')
    start_transferred_days_fifth_holiday_week_current_period: Optional[float] = Field(default=None, alias='StartTransferredDaysFifthHolidayWeekCurrentPeriod')
    start_transferred_days_used_fifth_holiday_week_current_period: Optional[float] = Field(default=None, alias='StartTransferredDaysUsedFifthHolidayWeekCurrentPeriod')
    start_gross_holiday_pay_transferred_fifth_holiday_week_previous_period: Optional[float] = Field(default=None, alias='StartGrossHolidayPayTransferredFifthHolidayWeekPreviousPeriod')
    start_holiday_hindrance_transferred_days_fifth_holiday_week_previous_period: Optional[float] = Field(default=None, alias='StartHolidayHindranceTransferredDaysFifthHolidayWeekPreviousPeriod')
    start_payout_from_fifth_holiday_week_previous_period: Optional[float] = Field(default=None, alias='StartPayoutFromFifthHolidayWeekPreviousPeriod')
    start_lost_gross_holiday_pay_fifth_holiday_week_previous_period: Optional[float] = Field(default=None, alias='StartLostGrossHolidayPayFifthHolidayWeekPreviousPeriod')
    start_paid_days_fifth_holiday_week_previous_period: Optional[float] = Field(default=None, alias='StartPaidDaysFifthHolidayWeekPreviousPeriod')
    start_transferred_days_fifth_holiday_week_previous_period: Optional[float] = Field(default=None, alias='StartTransferredDaysFifthHolidayWeekPreviousPeriod')
    start_transferred_days_used_fifth_holiday_week_previous_period: Optional[float] = Field(default=None, alias='StartTransferredDaysUsedFifthHolidayWeekPreviousPeriod')
    start_holiday_hindrance_transferred_days_fifth_holiday_week_two_periods_before: Optional[float] = Field(default=None, alias='StartHolidayHindranceTransferredDaysFifthHolidayWeekTwoPeriodsBefore')
    start_lost_gross_holiday_pay_fifth_holiday_week_two_periods_before: Optional[float] = Field(default=None, alias='StartLostGrossHolidayPayFifthHolidayWeekTwoPeriodsBefore')
    start_holiday_hindrance_transferred_days_fifth_holiday_week_three_periods_before: Optional[float] = Field(default=None, alias='StartHolidayHindranceTransferredDaysFifthHolidayWeekThreePeriodsBefore')
    start_transferred_days_fifth_holiday_week_three_periods_before: Optional[float] = Field(default=None, alias='StartTransferredDaysFifthHolidayWeekThreePeriodsBefore')
    start_transferred_days_used_fifth_holiday_week_three_periods_before: Optional[float] = Field(default=None, alias='StartTransferredDaysUsedFifthHolidayWeekThreePeriodsBefore')
    start_gross_holiday_pay_transferred_fifth_holiday_week_three_periods_before: Optional[float] = Field(default=None, alias='StartGrossHolidayPayTransferredFifthHolidayWeekThreePeriodsBefore')
    start_lost_gross_holiday_pay_fifth_holiday_week_three_periods_before: Optional[float] = Field(default=None, alias='StartLostGrossHolidayPayFifthHolidayWeekThreePeriodsBefore')
    start_earned_care_days_three_years_before: Optional[float] = Field(default=None, alias='StartEarnedCareDaysThreeYearsBefore')
    start_used_care_days_three_years_before: Optional[float] = Field(default=None, alias='StartUsedCareDaysThreeYearsBefore')
    start_earned_free_vacation_days_three_years_before: Optional[float] = Field(default=None, alias='StartEarnedFreeVacationDaysThreeYearsBefore')
    start_used_free_vacation_days_three_years_before: Optional[float] = Field(default=None, alias='StartUsedFreeVacationDaysThreeYearsBefore')
    start_holday_at_own_expense_three_years_before: Optional[float] = Field(default=None, alias='StartHoldayAtOwnExpenseThreeYearsBefore')
    start_holday_at_own_expense_three_years_before_saldo: Optional[float] = Field(default=None, alias='StartHoldayAtOwnExpenseThreeYearsBeforeSaldo')
    start_holiday_hindrance_used_days_fifth_holiday_week_two_periods_before: Optional[float] = Field(default=None, alias='StartHolidayHindranceUsedDaysFifthHolidayWeekTwoPeriodsBefore')
    start_holiday_hindrance_used_days_fifth_holiday_week_three_periods_before: Optional[float] = Field(default=None, alias='StartHolidayHindranceUsedDaysFifthHolidayWeekThreePeriodsBefore')
    start_holiday_pay_gross_used_fifth_holiday_week_current_period: Optional[float] = Field(default=None, alias='StartHolidayPayGrossUsedFifthHolidayWeekCurrentPeriod')
    start_holiday_pay_gross_used_fifth_holiday_week_previous_period: Optional[float] = Field(default=None, alias='StartHolidayPayGrossUsedFifthHolidayWeekPreviousPeriod')
    start_transferred_gross_holiday_pay_used_fifth_holiday_week_previous_period: Optional[float] = Field(default=None, alias='StartTransferredGrossHolidayPayUsedFifthHolidayWeekPreviousPeriod')
    start_transferred_gross_holiday_pay_used_fifth_holiday_week_three_periods_before: Optional[float] = Field(default=None, alias='StartTransferredGrossHolidayPayUsedFifthHolidayWeekThreePeriodsBefore')
    start_holiday_hindrance_used_days_fifth_holiday_week_previous_period: Optional[float] = Field(default=None, alias='StartHolidayHindranceUsedDaysFifthHolidayWeekPreviousPeriod')

    # Payroll related (subset)
    salary_type: Optional[int] = Field(default=None, alias='SalaryType')
    p_number: Optional[str] = Field(default=None, alias='PNumber')
    is_active: Optional[bool] = Field(default=None, alias='IsActive')
    job_description: Optional[str] = Field(default=None, alias='JobDescription')
    holiday_pay_rate: Optional[float] = Field(default=None, alias='HolidayPayRate')
    number_of_hours: Optional[float] = Field(default=None, alias='NumberOfHours')
    income_type: Optional[int] = Field(default=None, alias='IncomeType')
    tax: Optional[int] = Field(default=None, alias='Tax')
    revenue_type: Optional[int] = Field(default=None, alias='RevenueType')
    maternity_type: Optional[int] = Field(default=None, alias='MaternityType')
    atp_type: Optional[str] = Field(default=None, alias='AtpType')
    additional_tax_rate: Optional[float] = Field(default=None, alias='AdditionalTaxRate')
    enable_file_transfer: Optional[bool] = Field(default=None, alias='EnableFileTransfer')
    insurance_category: Optional[int] = Field(default=None, alias='InsuranceCategory')
    company_cvr_number: Optional[str] = Field(default=None, alias='CompanyCvrNumber')
    is_employee_look_like_other_employee: Optional[bool] = Field(default=None, alias='IsEmployeeLookLikeOtherEmployee')
    look_like_employee_uid: Optional[str] = Field(default=None, alias='LookLikeEmployeeUid')
    title: Optional[str] = Field(default=None, alias='Title')
    company_cost_center_uid: Optional[str] = Field(default=None, alias='CompanyCostCenterUid')
    company_profit_center_uid: Optional[str] = Field(default=None, alias='CompanyProfitCenterUid')
    booking_group_uid: Optional[str] = Field(default=None, alias='BookingGroupUid')
    company_date: Optional[Any] = Field(default=None, alias='CompanyDate')
    holiday_pay_receiver_uid: Optional[str] = Field(default=None, alias='HolidayPayReceiverUid')
    benefit_package_amount: Optional[float] = Field(default=None, alias='BenefitPackageAmount')
    benefit_package_amount_type: Optional[int] = Field(default=None, alias='BenefitPackageAmountType')
    holiday_payment_amount: Optional[float] = Field(default=None, alias='HolidayPaymentAmount')
    holiday_payment_type: Optional[int] = Field(default=None, alias='HolidayPaymentType')
    benefit_package_type: Optional[int] = Field(default=None, alias='BenefitPackageType')
    include_benefit_package_in_pension: Optional[bool] = Field(default=None, alias='IncludeBenefitPackageInPension')
    benefit_package_two_amount: Optional[float] = Field(default=None, alias='BenefitPackageTwoAmount')
    benefit_package_two_type: Optional[int] = Field(default=None, alias='BenefitPackageTwoType')
    include_benefit_package_two_in_pension: Optional[bool] = Field(default=None, alias='IncludeBenefitPackageTwoInPension')
    is_absence_freechoice_enabled: Optional[bool] = Field(default=None, alias='IsAbsenceFreechoiceEnabled')
    holiday_saved_rate: Optional[float] = Field(default=None, alias='HolidaySavedRate')
    sh_month_select: Optional[Any] = Field(default=None, alias='SHMonthSelect')
    benefit_package_payout_months: Optional[Any] = Field(default=None, alias='BenefitPackagePayoutMonths')
    horesta_supplement: Optional[float] = Field(default=None, alias='HorestaSupplement')
    sh_payout_netto_month_select: Optional[Any] = Field(default=None, alias='ShPayoutNettoMonthSelect')
    transfer_netto: Optional[bool] = Field(default=None, alias='TransferNetto')
    monthly_salary: Optional[float] = Field(default=None, alias='MonthlySalary')
    salary_mode: Optional[int] = Field(default=None, alias='SalaryMode')
    kr_rate: Optional[float] = Field(default=None, alias='KrRate')
    number_of_working_days: Optional[float] = Field(default=None, alias='NumberOfWorkingDays')
    salary_payout_period: Optional[int] = Field(default=None, alias='SalaryPayoutPeriod')
    holidays: Optional[float] = Field(default=None, alias='Holidays')
    max_loan: Optional[float] = Field(default=None, alias='MaxLoan')
    is_automatic_payroll: Optional[bool] = Field(default=None, alias='IsAutomaticPayroll')
    holiday_days_per_year: Optional[float] = Field(default=None, alias='HolidayDaysPerYear')
    holiday_supplement: Optional[float] = Field(default=None, alias='HolidaySupplement')
    additional_days_per_year: Optional[float] = Field(default=None, alias='AdditionalDaysPerYear')
    care_days_per_year: Optional[float] = Field(default=None, alias='CareDaysPerYear')
    maximum_number_of_days_used_in_advance: Optional[float] = Field(default=None, alias='MaximumNumberOfDaysUsedInAdvance')
    holiday_registry_code: Optional[int] = Field(default=None, alias='HolidayRegistryCode')
    holiday_handling_code: Optional[int] = Field(default=None, alias='HolidayHandlingCode')
    group_insurance: Optional[float] = Field(default=None, alias='GroupInsurance')
    is_insurance_taxable: Optional[bool] = Field(default=None, alias='IsInsuranceTaxable')
    is_insurance_inclusive_in_pension: Optional[bool] = Field(default=None, alias='IsInsuranceInclusiveInPension')
    number_of_hours_fixed: Optional[float] = Field(default=None, alias='NumberOfHoursFixed')
    monthly_salary_fixed_base: Optional[float] = Field(default=None, alias='MonthlySalaryFixedBase')
    pension_insitute_type: Optional[int] = Field(default=None, alias='PensionInsituteType')
    labour_company_pension: Optional[float] = Field(default=None, alias='LabourCompanyPension')
    labour_private_pension: Optional[float] = Field(default=None, alias='LabourPrivatePension')
    labour_benefits_package_for_pension: Optional[float] = Field(default=None, alias='LabourBenefitsPackageForPension')
    labour_agreement_code: Optional[str] = Field(default=None, alias='LabourAgreementCode')
    extra_holiday_entitlement_per_payroll: Optional[float] = Field(default=None, alias='ExtraHolidayEntitlementPerPayroll')

    class Config:
        populate_by_name = True
        extra = 'allow'

class PensionBase(BaseModel):
    name: Optional[str] = Field(default=None, description="Pension name", example="ATP Pension")
    resource_name: Optional[str] = Field(default=None, description="Resource name", example="ATP")
    pbs_number: Optional[str] = Field(default=None, description="PBS number", example="1234")
    type: Optional[int] = Field(default=None, description="Pension type code", example=1)
    id: Optional[int] = Field(default=None, description="Internal numeric identifier", example=10)
    uid: Optional[UUID] = Field(default=None, description="Pension UID", example="00000000-0000-0000-0000-000000000000")

    class Config:
        populate_by_name = True


class BenefitBase(BaseModel):
    name: Optional[str] = Field(default=None, description="Benefit name", example="Health Insurance")
    type: Optional[int] = Field(default=None, description="Benefit type code", example=1)
    resource: Optional[str] = Field(default=None, description="Resource identifier", example="BENEFIT_RES")
    included_in_pension_base: Optional[bool] = Field(default=None, description="Included in pension base", example=True)
    included_in_am_pension_base: Optional[bool] = Field(default=None, description="Included in AM pension base", example=True)
    included_in_holiday_entitlement_salary_base: Optional[bool] = Field(default=None, description="Included in holiday entitlement salary base", example=False)
    id: Optional[int] = Field(default=None, description="Internal numeric identifier", example=20)
    uid: Optional[UUID] = Field(default=None, description="Benefit UID", example="00000000-0000-0000-0000-000000000000")

    class Config:
        populate_by_name = True


class CompanyDepartmentBase(BaseModel):
    name: Optional[str] = Field(default=None, description="Department name", example="Sales")
    number: Optional[str] = Field(default=None, description="Department number/code", example="D-100")
    has_work_schema: Optional[bool] = Field(default=None, description="Whether department has a work schema", example=True)
    id: Optional[int] = Field(default=None, description="Internal numeric identifier", example=15)
    uid: Optional[UUID] = Field(default=None, description="Department UID", example="00000000-0000-0000-0000-000000000000")

    class Config:
        populate_by_name = True


class Dimension(BaseModel):
    id: Optional[int] = Field(default=None, description="Dimension ID", example=1)
    uid: Optional[UUID] = Field(default=None, description="Dimension UID", example="00000000-0000-0000-0000-000000000000")
    name: Optional[str] = Field(default=None, description="Dimension name", example="Profit Center")
    number: Optional[str] = Field(default=None, description="Dimension number/code", example="PC-01")
    type: Optional[str] = Field(default=None, description="Dimension type", example="profit")

    class Config:
        populate_by_name = True


class CompanyCostCenter(BaseModel):
    number_of_employees: Optional[int] = Field(default=None, description="Number of employees", example=42)
    employee_uids: Optional[List[UUID]] = Field(default=None, description="Employee UIDs", example=["00000000-0000-0000-0000-000000000000"])
    cost_center_name: Optional[str] = Field(default=None, description="Cost center name", example="Finance")
    cost_center_code: Optional[str] = Field(default=None, description="Cost center code", example="FIN")
    type: Optional[str] = Field(default=None, description="Type (cost/profit)", example="cost")
    id: Optional[int] = Field(default=None, description="Internal numeric identifier", example=10)
    uid: Optional[UUID] = Field(default=None, description="Cost center UID", example="00000000-0000-0000-0000-000000000000")

    class Config:
        populate_by_name = True


class EmployeeResignation(BaseModel):
    date_of_resignation: Optional[datetime] = Field(default=None, description="Resignation date (ISO 8601)", example="2024-05-31T00:00:00Z")
    deleted_on: Optional[datetime] = Field(default=None, description="Soft delete timestamp (ISO 8601)", example="2024-06-01T00:00:00Z")
    reason: Optional[int] = Field(default=None, description="Resignation reason code", example=0)
    resigned_by: Optional[int] = Field(default=None, description="Resigned by user ID", example=100)
    note: Optional[str] = Field(default=None, description="Resignation note", example="Personal reasons")
    is_processed: Optional[bool] = Field(default=None, description="Resignation processed flag", example=False)
    last_work_day: Optional[datetime] = Field(default=None, description="Last working day (ISO 8601)", example="2024-05-30T00:00:00Z")
    id: Optional[int] = Field(default=None, description="Internal numeric identifier", example=1)
    uid: Optional[UUID] = Field(default=None, description="Resignation UID", example="00000000-0000-0000-0000-000000000000")

    class Config:
        populate_by_name = True


class EmployeeAmPension(BaseModel):
    pension: Optional[PensionBase] = Field(default=None, description="Pension base object")
    company_amount: Optional[float] = Field(default=None, description="Company contribution amount", example=1000.0)
    employee_amount: Optional[float] = Field(default=None, description="Employee contribution amount", example=500.0)
    amount_type: Optional[int] = Field(default=None, description="Amount type code", example=0)
    union_code: Optional[str] = Field(default=None, description="Union code", example="UN-1")
    benefit_package_to_pension_percentage: Optional[float] = Field(default=None, description="Benefit package to pension %", example=10.0)
    group_life_amount: Optional[float] = Field(default=None, description="Group life amount", example=250.0)
    is_group_life_amount_taxable: Optional[bool] = Field(default=None, description="Group life amount taxable flag", example=True)
    is_group_life_amount_inclusive_pension_contribution: Optional[bool] = Field(default=None, description="Group life amount inclusive in pension contribution", example=False)
    additional_contribution_amount_type: Optional[int] = Field(default=None, description="Additional contribution amount type", example=0)
    additional_contribution_amount: Optional[float] = Field(default=None, description="Additional contribution amount", example=100.0)
    employee_wage_code: Optional[str] = Field(default=None, description="Employee wage code", example="E100")
    company_wage_code: Optional[str] = Field(default=None, description="Company wage code", example="C100")
    insurance_amount: Optional[float] = Field(default=None, description="Insurance amount", example=250.0)
    insurance_union_code: Optional[str] = Field(default=None, description="Insurance union code", example="IU-1")
    id: Optional[int] = Field(default=None, description="Internal numeric identifier", example=1)
    uid: Optional[UUID] = Field(default=None, description="AM pension UID", example="00000000-0000-0000-0000-000000000000")

    class Config:
        populate_by_name = True


class EmployeeBenefitBase(BaseModel):
    price_per_month: Optional[float] = None
    benefit_base: Optional[BenefitBase] = None
    name: Optional[str] = None
    is_editable: Optional[bool] = None
    pbs_number: Optional[str] = None
    company_contribution: Optional[float] = None
    included_in_pension_base: Optional[bool] = None
    included_in_am_pension_base: Optional[bool] = None
    included_in_holiday_entitlement_salary_base: Optional[bool] = None
    id: Optional[int] = None
    uid: Optional[UUID] = None

    class Config:
        populate_by_name = True


class EmployeeTaxCard(BaseModel):
    created_on: Optional[datetime] = Field(default=None, description="Created on (ISO 8601)", example="2024-01-15T12:00:00Z")
    valid_from: Optional[datetime] = Field(default=None, description="Valid from (ISO 8601)", example="2024-02-01T00:00:00Z")
    tax_percentage: Optional[float] = Field(default=None, description="Tax percentage", example=38.5)
    free_card_deduction_main_card: Optional[float] = Field(default=None, description="Free card deduction (main card)", example=0.0)
    fair_deduction_main_card: Optional[float] = Field(default=None, description="Fair deduction (main card)", example=0.0)
    ugefradrag_main_card: Optional[float] = Field(default=None, description="Weekly deduction (main card)", example=0.0)
    fourteen_day_deduction_main_card: Optional[float] = Field(default=None, description="14-day deduction (main card)", example=0.0)
    monthly_deduction_main_card: Optional[float] = Field(default=None, description="Monthly deduction (main card)", example=0.0)
    type_of_card: Optional[int] = Field(default=None, description="Type of card code", example=0)
    status: Optional[int] = Field(default=None, description="Status code", example=0)
    date_of_creating_of_currente_skattekort_sn: Optional[datetime] = Field(default=None, description="Date of creating current skattekort SN", example="2024-01-20T00:00:00Z")
    skattekort_serial_number: Optional[str] = Field(default=None, description="Skattekort serial number", example="SK-123")
    date_of_received_skat_message_response: Optional[datetime] = Field(default=None, description="Date of received SKAT message response", example="2024-01-22T00:00:00Z")
    skat_message: Optional[str] = Field(default=None, description="SKAT message", example="OK")
    id: Optional[int] = Field(default=None, description="Internal numeric identifier", example=1)
    uid: Optional[UUID] = Field(default=None, description="Tax card UID", example="00000000-0000-0000-0000-000000000000")

    class Config:
        populate_by_name = True


class EmployeePension(BaseModel):
    account_number: Optional[str] = Field(default=None, description="Pension account number", example="1234567890")
    register_number: Optional[str] = Field(default=None, description="Bank registration number", example="0001")
    employee_fk: Optional[int] = Field(default=None, description="Employee FK", example=100)
    private_pension: Optional[float] = Field(default=None, description="Private pension amount", example=500.0)
    company_pension: Optional[float] = Field(default=None, description="Company pension amount", example=1000.0)
    policy_reference_number: Optional[str] = Field(default=None, description="Policy reference number", example="POL-123")
    tax_pension_amount: Optional[bool] = Field(default=None, description="Tax pension amount flag", example=True)
    pension_value_type: Optional[int] = Field(default=None, description="Pension value type code", example=1)
    pension: Optional[PensionBase] = Field(default=None, description="Pension base object")
    union_code: Optional[str] = Field(default=None, description="Union code", example="UN-1")
    coverage_base_salary: Optional[float] = Field(default=None, description="Coverage base salary", example=35000.0)
    employee_wage_code: Optional[str] = Field(default=None, description="Employee wage code", example="E100")
    company_wage_code: Optional[str] = Field(default=None, description="Company wage code", example="C100")
    insurance_amount: Optional[float] = Field(default=None, description="Insurance amount", example=250.0)
    group_life_agreement_number: Optional[str] = Field(default=None, description="Group life agreement number", example="GL-001")
    calculate_from_am_pension: Optional[bool] = Field(default=None, description="Calculate from AM pension flag", example=True)
    additional_contribution_amount_type: Optional[int] = Field(default=None, description="Additional contribution amount type", example=0)
    additional_contribution_amount: Optional[float] = Field(default=None, description="Additional contribution amount", example=100.0)
    id: Optional[int] = Field(default=None, description="Internal numeric identifier", example=1)
    uid: Optional[UUID] = Field(default=None, description="Employee pension UID", example="00000000-0000-0000-0000-000000000000")

    class Config:
        populate_by_name = True


class RelativeBase(BaseModel):
    employee_id: Optional[int] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    relation: Optional[str] = None
    id: Optional[int] = None
    uid: Optional[UUID] = None

    class Config:
        populate_by_name = True


class HolidayPayReceiverBase(BaseModel):
    name: Optional[str] = None
    type: Optional[int] = None
    cvr: Optional[str] = None
    id: Optional[int] = None
    uid: Optional[UUID] = None

    class Config:
        populate_by_name = True


class EmployeeSaldoHolidayPeriods(BaseModel):
    year: Optional[int] = None
    period_type: Optional[int] = None
    saldo_type: Optional[int] = None
    can_edit_fifth_holiday_week_fields: Optional[bool] = None
    has_fifth_holiday_week_payout: Optional[bool] = None

    class Config:
        populate_by_name = True


class CompanyModel(BaseModel):
    association_id: Optional[int] = None
    p_number: Optional[str] = None
    cvr: Optional[str] = None
    has_holiday_payment: Optional[bool] = None
    has_benefit_package: Optional[bool] = None
    has_benefit_package_two: Optional[bool] = None
    has_am_pension: Optional[bool] = None
    is_department_income_split_enabled: Optional[bool] = None
    insurance_type: Optional[int] = None
    is_use_of_vacation_days_in_advance_enabled: Optional[bool] = None
    is_horesta_supplement_enabled: Optional[bool] = None
    has_holiday_payment_netto_transfer_or_payout: Optional[bool] = None
    is_sh_payout_netto_enabled: Optional[bool] = None
    is_transfer_fifth_holiday_week_enabled: Optional[bool] = None
    is_holiday_hindrance_enabled: Optional[bool] = None
    extra_holiday_entitlement_in_hours: Optional[bool] = None
    id: Optional[int] = None
    uid: Optional[UUID] = None
    name: Optional[str] = None
    logo_url: Optional[str] = None

    class Config:
        populate_by_name = True


class User(BaseModel):
    is_active: Optional[bool] = None
    email: Optional[str] = None
    name: Optional[str] = None
    photo_url: Optional[str] = None
    id: Optional[int] = None
    uid: Optional[UUID] = None

    class Config:
        populate_by_name = True




class GetEmployeeAsyncResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    resignation: Optional[EmployeeResignation] = None
    am_pension: Optional[EmployeeAmPension] = None
    benefits: Optional[List[EmployeeBenefitBase]] = None
    paychecks: Optional[List[Dict[str, Any]]] = None  # PayCheckDto is too complex, using Dict for now
    tax_cards: Optional[List[EmployeeTaxCard]] = None
    pensions: Optional[List[EmployeePension]] = None
    relatives: Optional[List[RelativeBase]] = None
    extra_hours_payments: Optional[List[Dict[str, Any]]] = None  # ExtraHoursPaymentDto is too complex, using Dict for now
    holiday_pay_receiver: Optional[HolidayPayReceiverBase] = Field(default=None, description="Holiday pay receiver object")
    personal_identification_number: Optional[str] = Field(default=None, description="Personal identification number (CPR)", example="010190-1234")
    address: Optional[str] = Field(default=None, description="Street address", example="Main Street 1")
    city: Optional[str] = Field(default=None, description="City name", example="Copenhagen")
    kr_rate: Optional[float] = Field(default=None, description="Krone rate", example=120.0)
    monthly_salary: Optional[float] = Field(default=None, description="Monthly salary", example=32000.0)
    monthly_salary_fixed_base: Optional[float] = Field(default=None, description="Monthly salary fixed base", example=30000.0)
    holiday_days_per_year: Optional[float] = Field(default=None, description="Holiday days per year", example=25.0)
    holiday_supplement: Optional[float] = Field(default=None, description="Holiday supplement amount", example=1.5)
    care_days_per_year: Optional[float] = Field(default=None, description="Care days per year", example=2.0)
    additional_days_per_year: Optional[float] = Field(default=None, description="Additional days per year", example=5.0)
    maximum_number_of_days_used_in_advance: Optional[float] = Field(default=None, description="Max days used in advance", example=5.0)
    holidays: Optional[float] = Field(default=None, description="Holiday days", example=25.0)
    max_loan: Optional[float] = Field(default=None, description="Maximum loan amount", example=5000.0)
    is_automatic_payroll: Optional[bool] = Field(default=None, description="Automatic payroll enabled", example=False)
    holiday_registry_code: Optional[int] = Field(default=None, description="Holiday registry code", example=0)
    holiday_handling_code: Optional[int] = Field(default=None, description="Holiday handling code", example=0)
    group_insurance: Optional[float] = Field(default=None, description="Group insurance amount", example=300.0)
    is_insurance_taxable: Optional[bool] = Field(default=None, description="Insurance taxable flag", example=True)
    is_insurance_inclusive_in_pension: Optional[bool] = Field(default=None, description="Insurance included in pension", example=False)
    job_description: Optional[str] = Field(default=None, description="Job description text", example="Backend developer")
    p_number: Optional[str] = Field(default=None, description="Employee P-number", example="P12345")
    invitation_text: Optional[str] = Field(default=None, description="Invitation message text", example="Welcome to Zenegy")
    start_g_days: Optional[float] = None
    start_am_income: Optional[float] = None
    start_contributory_income: Optional[float] = None
    start_one_time_income: Optional[float] = None
    start_b_income_with_am: Optional[float] = None
    start_b_income_without_am: Optional[float] = None
    start_hours: Optional[float] = None
    start_atp: Optional[float] = None
    start_am: Optional[float] = None
    start_a_skat: Optional[float] = None
    start_health_insurance: Optional[float] = None
    start_company_car: Optional[float] = None
    start_company_lodging: Optional[float] = None
    start_mileage: Optional[float] = None
    start_mileage_low_rate: Optional[float] = None
    start_travel_allowance: Optional[float] = None
    start_personal_pension: Optional[float] = None
    start_pension_from_company: Optional[float] = None
    start_group_life: Optional[float] = None
    start_group_life2: Optional[float] = None
    start_personal_amp: Optional[float] = None
    start_company_amp: Optional[float] = None
    start_free_phone: Optional[float] = None
    number_of_hours: Optional[float] = None
    number_of_hours_fixed: Optional[float] = None
    pension_institute_type: Optional[int] = None
    labour_company_pension: Optional[float] = None
    labour_private_pension: Optional[float] = None
    labour_benefits_package_for_pension: Optional[float] = None
    labour_agreement_code: Optional[str] = None
    has_maternity_participation: Optional[bool] = None
    atp_type: Optional[str] = None
    show_relatives_and_documents: Optional[bool] = None
    start_net_holiday_pay: Optional[float] = None
    start_number_of_vacation_days: Optional[float] = None
    start_holiday_supplement_value: Optional[float] = None
    start_am_contributions_wages_and_holidaypay: Optional[float] = None
    start_number_of_vacation_days_two_periods_before: Optional[float] = None
    start_number_of_vacation_days_three_periods_before: Optional[float] = None
    start_number_of_vacation_days_previous_period: Optional[float] = None
    start_number_of_vacation_days_current_period: Optional[float] = None
    start_number_of_vacation_days_frozen_period: Optional[float] = None
    start_holiday_supplement_three_periods_before: Optional[float] = None
    start_holiday_supplement_two_periods_before: Optional[float] = None
    start_holiday_supplement_previous_period: Optional[float] = None
    start_holiday_supplement_current_period: Optional[float] = None
    start_earned_vacations_legitimate_salary_amount_current_period: Optional[float] = None
    start_holiday_payment_saved: Optional[float] = None
    start_holiday_payment_advance: Optional[float] = None
    start_holiday_payment_advance_year_before: Optional[float] = None
    start_holiday_payment_saved_year_before: Optional[float] = None
    start_holiday_payment_saved_netto_year_before: Optional[float] = None
    start_holiday_payment_saved_netto: Optional[float] = None
    start_holiday_payment_saldo_netto: Optional[float] = None
    start_used_vacation_day_units_current_period: Optional[float] = None
    start_used_vacation_day_units_previous_period: Optional[float] = None
    start_used_vacation_day_units_two_periods_before: Optional[float] = None
    start_used_vacation_day_units_three_periods_before: Optional[float] = None
    start_used_vacation_day_units_frozen_period: Optional[float] = None
    start_used_holiday_supplement_current_period: Optional[float] = None
    start_used_holiday_supplement_previous_period: Optional[float] = None
    start_used_holiday_supplement_two_periods_before: Optional[float] = None
    start_used_holiday_supplement_three_periods_before: Optional[float] = None
    start_earned_vacations_legitimate_salary_amount_previous_period: Optional[float] = None
    start_earned_vacations_legitimate_salary_amount_two_periods_before: Optional[float] = None
    start_earned_vacations_legitimate_salary_amount_three_periods_before: Optional[float] = None
    start_earned_vacations_legitimate_salary_amount_frozen_period: Optional[float] = None
    start_earned_holiday_pay_net_amount_previous_period: Optional[float] = None
    start_earned_holiday_pay_net_amount_two_periods_before: Optional[float] = None
    start_earned_holiday_pay_net_amount_frozen_period: Optional[float] = None
    start_earned_holiday_pay_net_amount_current_period: Optional[float] = None
    start_used_holiday_pay_net_amount_current_period: Optional[float] = None
    start_used_holiday_pay_net_amount_previous_period: Optional[float] = None
    start_used_holiday_pay_net_amount_two_periods_before: Optional[float] = None
    start_used_holiday_pay_net_amount_frozen_period: Optional[float] = None
    benefit_package_amount: Optional[float] = None
    holiday_payment_amount: Optional[float] = None
    is_absence_freechoice_enabled: Optional[bool] = None
    start_used_vacation_day_units_current_period: Optional[float] = None
    start_used_vacation_day_units_previous_period: Optional[float] = None
    start_used_vacation_day_units_two_periods_before: Optional[float] = None
    start_used_vacation_day_units_frozen_period: Optional[float] = None
    start_used_holiday_supplement_current_period: Optional[float] = None
    start_used_holiday_supplement_previous_period: Optional[float] = None
    start_used_holiday_supplement_two_periods_before: Optional[float] = None
    start_earned_vacations_legitimate_salary_amount_previous_period: Optional[float] = None
    start_earned_vacations_legitimate_salary_amount_two_periods_before: Optional[float] = None
    start_earned_vacations_legitimate_salary_amount_frozen_period: Optional[float] = None
    start_earned_holiday_pay_net_amount_previous_period: Optional[float] = None
    start_earned_holiday_pay_net_amount_two_periods_before: Optional[float] = None
    start_earned_holiday_pay_net_amount_frozen_period: Optional[float] = None
    start_earned_holiday_pay_net_amount_current_period: Optional[float] = None
    start_used_holiday_pay_net_amount_current_period: Optional[float] = None
    start_used_holiday_pay_net_amount_previous_period: Optional[float] = None
    start_used_holiday_pay_net_amount_two_periods_before: Optional[float] = None
    start_used_holiday_pay_net_amount_frozen_period: Optional[float] = None
    benefit_package_amount_type: Optional[int] = None
    holiday_payment_type: Optional[int] = None
    benefit_package_type: Optional[int] = None
    include_benefit_package_in_pension: Optional[bool] = None
    last_time_skat_card_updated: Optional[datetime] = None
    additional_tax_rate: Optional[float] = None
    roles: Optional[List[int]] = None
    enable_file_transfer: Optional[bool] = None
    is_e_boks_enabled: Optional[bool] = None
    maternity_type: Optional[int] = None
    holiday_pay_rate: Optional[float] = None
    start_earned_care_days_two_years_before: Optional[float] = None
    start_earned_care_days_year_before: Optional[float] = None
    start_earned_care_days_current_year: Optional[float] = None
    start_used_care_days_two_years_before: Optional[float] = None
    start_used_care_days_year_before: Optional[float] = None
    start_used_care_days_current_year: Optional[float] = None
    start_earned_free_vacation_days_two_years_before: Optional[float] = None
    start_earned_free_vacation_days_year_before: Optional[float] = None
    start_earned_free_vacation_days_current_year: Optional[float] = None
    start_used_free_vacation_days_two_years_before: Optional[float] = None
    start_used_free_vacation_days_year_before: Optional[float] = None
    start_used_free_vacation_days_current_year: Optional[float] = None
    number_of_working_days: Optional[float] = None
    start_earned_holiday_pay_gross_current_period: Optional[float] = None
    start_earned_holiday_pay_gross_previous_period: Optional[float] = None
    start_earned_holiday_pay_gross_two_periods_before: Optional[float] = None
    start_earned_holiday_pay_gross_three_periods_before: Optional[float] = None
    start_earned_holiday_pay_gross_frozen_period: Optional[float] = None
    start_used_holiday_pay_gross_current_period: Optional[float] = None
    start_used_holiday_pay_gross_previous_period: Optional[float] = None
    start_used_holiday_pay_gross_two_periods_before: Optional[float] = None
    start_used_holiday_pay_gross_three_periods_before: Optional[float] = None
    start_used_holiday_pay_gross_frozen_period: Optional[float] = None
    start_flex_hours: Optional[float] = None
    insurance_category: Optional[int] = None
    ancinity_date: Optional[datetime] = None
    start_saldo_holiday_periods: Optional[List[EmployeeSaldoHolidayPeriods]] = None
    can_change_holiday_pay_receiver: Optional[bool] = None
    global_value_information: Optional[List[Dict[str, Any]]] = None  # GlobalValueEmployeeInformationDto is too complex, using Dict for now
    nem_konto_payment: Optional[str] = None
    global_value_set_information: Optional[Dict[str, Any]] = None  # GlobalValueSetInformation is too complex, using Dict for now
    standard_rate: Optional[float] = None
    standard_rate_hourly: Optional[float] = None
    benefit_package_two_amount: Optional[float] = None
    benefit_package_two_type: Optional[int] = None
    include_benefit_package_two_in_pension: Optional[bool] = None
    company_cost_center: Optional[CompanyCostCenter] = None
    company_profit_center: Optional[CompanyCostCenter] = None
    company_cost_center_fk: Optional[int] = None
    start_time_in_lieu_earned_hours: Optional[float] = None
    start_time_in_lieu_earned_amount: Optional[float] = None
    start_health_insurance_no_am_pension: Optional[float] = None
    start_health_insurance_no_am_pension_no_vacation_entitled_money: Optional[float] = None
    start_not_covered_by_triviality: Optional[float] = None
    start_christmas_gifts_benefit: Optional[float] = None
    start_other_benefit: Optional[float] = None
    holiday_saved_rate: Optional[float] = None
    show_current_saldo: Optional[bool] = None
    start_negative_salary_saldo: Optional[float] = None
    is_tracking_negative_salary_enabled: Optional[bool] = None
    company_cvr_number: Optional[str] = None
    sh_months_select: Optional[List[str]] = None
    benefit_package_payout_months: Optional[List[str]] = None
    employee_values_information: Optional[List[Dict[str, Any]]] = None  # EmployeeValueEmployeeInformationDto is too complex, using Dict for now
    start_anniversary_bonus_saldo: Optional[float] = None
    start_severance_saldo: Optional[float] = None
    start_travel_allowance_without_payment: Optional[float] = None
    employee_department_income_splits: Optional[List[Dict[str, Any]]] = None  # EmployeeDepartmentIncomeSplitDto is too complex, using Dict for now
    horesta_supplement: Optional[float] = None
    special_supplement_type: Optional[str] = None
    special_supplement_payout_months: Optional[List[str]] = None
    start_holiday_at_own_expense_two_years_before: Optional[float] = None
    start_holiday_at_own_expense_year_before: Optional[float] = None
    start_holiday_at_own_expense_current_year: Optional[float] = None
    start_holiday_at_own_expense_two_years_before_saldo: Optional[float] = None
    start_holiday_at_own_expense_year_before_saldo: Optional[float] = None
    start_holiday_at_own_expense_current_year_saldo: Optional[float] = None
    is_after_september_2021: Optional[bool] = None
    sh_payout_netto_months_select: Optional[List[str]] = None
    transfer_netto: Optional[bool] = None
    booking_group: Optional[Dict[str, Any]] = None  # BookingGroupBaseDto is too complex, using Dict for now
    start_number_of_vacation_days_fifth_holiday_week_two_years_before: Optional[float] = None
    start_number_used_vacation_days_fifth_holiday_week_two_years_before: Optional[float] = None
    start_vacation_pay_gross_fifth_holiday_week_two_years_before: Optional[float] = None
    start_vacations_legitimate_salary_fifth_holiday_week_two_years_before: Optional[float] = None
    start_vacation_supplement_earned_fifth_holiday_week_two_years_before: Optional[float] = None
    start_vacation_supplement_used_fifth_holiday_week_two_years_before: Optional[float] = None
    start_number_of_vacation_days_fifth_holiday_week_three_years_before: Optional[float] = None
    start_number_used_vacation_days_fifth_holiday_week_three_years_before: Optional[float] = None
    start_vacation_pay_gross_fifth_holiday_week_three_years_before: Optional[float] = None
    start_vacations_legitimate_salary_fifth_holiday_week_three_years_before: Optional[float] = None
    start_vacation_supplement_earned_fifth_holiday_week_three_years_before: Optional[float] = None
    start_vacation_supplement_used_fifth_holiday_week_three_years_before: Optional[float] = None
    start_vacation_pay_gross_used_fifth_holiday_week_two_years_before: Optional[float] = None
    start_vacation_pay_gross_used_fifth_holiday_week_three_years_before: Optional[float] = None
    start_holiday_hindrance_transferred_days_fifth_holiday_week_current_period: Optional[float] = None
    start_holiday_hindrance_used_days_fifth_holiday_week_current_period: Optional[float] = None
    start_days_to_payout_or_transfer_fifth_holiday_week_current_period: Optional[float] = None
    start_paid_days_fifth_holiday_week_current_period: Optional[float] = None
    start_days_for_transfer_fifth_holiday_week_current_period: Optional[float] = None
    start_transferred_days_fifth_holiday_week_current_period: Optional[float] = None
    start_transferred_days_used_fifth_holiday_week_current_period: Optional[float] = None
    start_lost_days_fifth_holiday_week_current_period: Optional[float] = None
    start_holiday_pay_gross_used_fifth_holiday_week_current_period: Optional[float] = None
    start_gross_holiday_pay_per_day_fifth_holiday_week_current_period: Optional[float] = None
    start_value_for_days_to_payout_fifth_holiday_week_current_period: Optional[float] = None
    start_payout_from_fifth_holiday_week_current_period: Optional[float] = None
    start_gross_holiday_pay_for_transfer_fifth_holiday_week_current_period: Optional[float] = None
    start_gross_holiday_pay_transferred_fifth_holiday_week_current_period: Optional[float] = None
    start_transferred_gross_holiday_pay_used_fifth_holiday_week_current_period: Optional[float] = None
    start_transferred_gross_holiday_pay_value_per_day_fifth_holiday_week_current_period: Optional[float] = None
    start_lost_gross_holiday_pay_fifth_holiday_week_current_period: Optional[float] = None
    start_vacation_supplement_value_per_day_fifth_holiday_week_current_period: Optional[float] = None
    start_holiday_hindrance_transferred_days_fifth_holiday_week_previous_period: Optional[float] = None
    start_holiday_hindrance_used_days_fifth_holiday_week_previous_period: Optional[float] = None
    start_days_to_payout_or_transfer_fifth_holiday_week_previous_period: Optional[float] = None
    start_paid_days_fifth_holiday_week_previous_period: Optional[float] = None
    start_days_for_transfer_fifth_holiday_week_previous_period: Optional[float] = None
    start_transferred_days_fifth_holiday_week_previous_period: Optional[float] = None
    start_transferred_days_used_fifth_holiday_week_previous_period: Optional[float] = None
    start_lost_days_fifth_holiday_week_previous_period: Optional[float] = None
    start_holiday_pay_gross_used_fifth_holiday_week_previous_period: Optional[float] = None
    start_gross_holiday_pay_per_day_fifth_holiday_week_previous_period: Optional[float] = None
    start_value_for_days_to_payout_fifth_holiday_week_previous_period: Optional[float] = None
    start_payout_from_fifth_holiday_week_previous_period: Optional[float] = None
    start_gross_holiday_pay_for_transfer_fifth_holiday_week_previous_period: Optional[float] = None
    start_gross_holiday_pay_transferred_fifth_holiday_week_previous_period: Optional[float] = None
    start_transferred_gross_holiday_pay_used_fifth_holiday_week_previous_period: Optional[float] = None
    start_transferred_gross_holiday_pay_value_per_day_fifth_holiday_week_previous_period: Optional[float] = None
    start_lost_gross_holiday_pay_fifth_holiday_week_previous_period: Optional[float] = None
    start_vacation_supplement_value_per_day_fifth_holiday_week_previous_period: Optional[float] = None
    start_holiday_hindrance_transferred_days_fifth_holiday_week_two_periods_before: Optional[float] = None
    start_holiday_hindrance_used_days_fifth_holiday_week_two_periods_before: Optional[float] = None
    start_lost_days_fifth_holiday_week_two_periods_before: Optional[float] = None
    start_holiday_pay_gross_used_fifth_holiday_week_two_periods_before: Optional[float] = None
    start_gross_holiday_pay_per_day_fifth_holiday_week_two_periods_before: Optional[float] = None
    start_lost_gross_holiday_pay_fifth_holiday_week_two_periods_before: Optional[float] = None
    start_vacation_supplement_value_per_day_fifth_holiday_week_two_periods_before: Optional[float] = None
    start_holiday_hindrance_transferred_days_fifth_holiday_week_three_periods_before: Optional[float] = None
    start_holiday_hindrance_used_days_fifth_holiday_week_three_periods_before: Optional[float] = None
    start_transferred_days_fifth_holiday_week_three_periods_before: Optional[float] = None
    start_transferred_days_used_fifth_holiday_week_three_periods_before: Optional[float] = None
    start_lost_days_fifth_holiday_week_three_periods_before: Optional[float] = None
    start_holiday_pay_gross_used_fifth_holiday_week_three_periods_before: Optional[float] = None
    start_gross_holiday_pay_per_day_fifth_holiday_week_three_periods_before: Optional[float] = None
    start_gross_holiday_pay_transferred_fifth_holiday_week_three_periods_before: Optional[float] = None
    start_transferred_gross_holiday_pay_used_fifth_holiday_week_three_periods_before: Optional[float] = None
    start_transferred_gross_holiday_pay_value_per_day_fifth_holiday_week_three_periods_before: Optional[float] = None
    start_lost_gross_holiday_pay_fifth_holiday_week_three_periods_before: Optional[float] = None
    start_vacation_supplement_value_per_day_fifth_holiday_week_three_periods_before: Optional[float] = None
    start_paid_days_fifth_holiday_week_two_periods_before: Optional[float] = None
    start_paid_days_fifth_holiday_week_three_periods_before: Optional[float] = None
    start_transferred_days_fifth_holiday_week_two_periods_before: Optional[float] = None
    start_transferred_days_used_fifth_holiday_week_two_periods_before: Optional[float] = None
    start_payout_from_fifth_holiday_week_two_periods_before: Optional[float] = None
    start_payout_from_fifth_holiday_week_three_periods_before: Optional[float] = None
    start_gross_holiday_pay_transferred_fifth_holiday_week_two_periods_before: Optional[float] = None
    start_transferred_gross_holiday_pay_used_fifth_holiday_week_two_periods_before: Optional[float] = None
    start_days_to_payout_or_transfer_fifth_holiday_week_two_periods_before: Optional[float] = None
    start_days_to_payout_or_transfer_fifth_holiday_week_three_periods_before: Optional[float] = None
    start_value_for_days_to_payout_fifth_holiday_week_two_periods_before: Optional[float] = None
    start_value_for_days_to_payout_fifth_holiday_week_three_periods_before: Optional[float] = None
    start_transferred_gross_holiday_pay_value_per_day_fifth_holiday_week_two_periods_before: Optional[float] = None
    start_earned_care_days_three_years_before: Optional[float] = None
    start_used_care_days_three_years_before: Optional[float] = None
    start_earned_free_vacation_days_three_years_before: Optional[float] = None
    start_used_free_vacation_days_three_years_before: Optional[float] = None
    start_holiday_at_own_expense_three_years_before: Optional[float] = None
    start_holiday_at_own_expense_three_years_before_saldo: Optional[float] = None
    extra_holiday_entitlement_per_payroll: Optional[float] = None
    company_date: Optional[datetime] = None
    global_values_set_uid: Optional[UUID] = None
    is_employee_look_like_other_employee: Optional[bool] = None
    look_like_employee_uid: Optional[UUID] = None
    has_active_or_finished_payrolls: Optional[bool] = None
    start_gross_holiday_pay_for_transfer_fifth_holiday_week_two_periods_before: Optional[float] = None
    start_gross_holiday_pay_for_transfer_fifth_holiday_week_three_periods_before: Optional[float] = None
    tin_number: Optional[str] = None
    day_of_prayer_compensation: Optional[float] = None
    day_of_prayer_compensation_rule: Optional[str] = None
    start_current_year_day_of_prayer_compensation_earned: Optional[float] = None
    start_current_year_day_of_prayer_compensation_paidout: Optional[float] = None
    start_year_before_day_of_prayer_compensation_earned: Optional[float] = None
    start_year_before_day_of_prayer_compensation_paidout: Optional[float] = None
    start_days_for_transfer_fifth_holiday_week_three_periods_before: Optional[float] = None
    start_days_for_transfer_fifth_holiday_week_two_periods_before: Optional[float] = None
    work_time_employment_info: Optional[str] = None
    created_on: Optional[datetime] = None
    image_url: Optional[str] = None
    is_foreign: Optional[bool] = None
    company: Optional[CompanyModel] = None
    invited_by_email: Optional[int] = None
    has_payroll: Optional[bool] = None
    postal_number: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    linked_in: Optional[str] = None
    konto_number: Optional[str] = None
    reg_number: Optional[str] = None
    iban: Optional[str] = None
    swift: Optional[str] = None
    is_cpr_validated: Optional[bool] = None
    tax: Optional[int] = None
    has_profile_image: Optional[bool] = None
    user: Optional[User] = None
    has_user: Optional[bool] = None
    is_resigned_with_registrations: Optional[bool] = None
    salary_mode: Optional[int] = None
    employment_date: Optional[datetime] = None
    global_value_set_number: Optional[str] = None
    title: Optional[str] = None
    is_active: Optional[bool] = None
    is_resigned: Optional[bool] = None
    cpr: Optional[str] = None
    salary_type: Optional[int] = None
    contact_phone: Optional[str] = None
    email: Optional[str] = None
    department: Optional[CompanyDepartmentBase] = None
    cost_center: Optional[Dimension] = None
    profit_center: Optional[Dimension] = None
    car_registration_number: Optional[str] = None
    type: Optional[int] = None
    salary_payout_period: Optional[int] = None
    revenue_type: Optional[int] = None
    income_type: Optional[int] = None
    holiday_pay_receiver_type: Optional[int] = None
    extra_holiday_entitlement_rule: Optional[str] = None
    name: Optional[str] = None
    employee_number: Optional[str] = None
    extra_employee_number: Optional[str] = None
    id: Optional[int] = None
    uid: Optional[UUID] = None


class EmployeesGet(BrynQPanderaDataFrameModel):
    """Flattened schema for Zenegy Employees Output data"""

    # Employee Identification
    uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee unique identifier", alias="uid")
    id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee ID", alias="id")
    employee_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee number", alias="employeeNumber")
    extra_employee_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Extra employee number", alias="extraEmployeeNumber")

    # Basic Information
    name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee name", alias="name")
    title: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee title", alias="title")
    cpr: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="CPR number", alias="cpr")

    # Contact Information
    email: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Contact email", alias="contactEmail")
    contact_phone: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Contact phone", alias="contactPhone")
    address: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Address", alias="address")
    city: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="City", alias="city")
    postal_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Postal number", alias="postalNumber")
    mobile_phone: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Mobile phone", alias="mobilePhone")

    # Employment Information
    employment_date: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employment date", alias="employmentDate")
    date_of_resignation: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Date of resignation", alias="dateOfResignation")
    last_work_day: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Last work day", alias="lastWorkDay")
    salary_mode: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Salary mode", alias="salaryMode")
    salary_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Salary type", alias="salaryType")
    salary_payout_period: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Salary payout period", alias="salaryPayoutPeriod")

    # Status Flags
    is_active: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is active", alias="isActive")
    is_resigned: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is resigned", alias="isResigned")
    is_foreign: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is foreign", alias="isForeign")
    is_cpr_validated: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is CPR validated", alias="isCprValidated")
    has_payroll: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Has payroll", alias="hasPayroll")
    has_user: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Has user", alias="hasUser")
    has_profile_image: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Has profile image", alias="hasProfileImage")
    is_resigned_within_last_year: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is resigned within last year", alias="isResignedWithinLastyear")
    is_resigned_with_registrations: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is resigned with registrations", alias="isResignedWithRegistrations")

    # Company Information (nested object)
    company_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company UID", alias="company__uid")
    company_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company name", alias="company__name")
    company_cvr: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company CVR", alias="company__cvr")
    company_association_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Company association ID", alias="company__associationId")
    company_p_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company P number", alias="company__pNumber")
    company_has_holiday_payment: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Company has holiday payment", alias="company__hasHolidayPayment")
    company_has_benefit_package: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Company has benefit package", alias="company__hasBenefitPackage")
    company_has_benefit_package_two: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Company has benefit package two", alias="company__hasBenefitPackageTwo")
    company_has_am_pension: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Company has AM pension", alias="company__hasAmPension")
    company_is_department_income_split_enabled: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Company is department income split enabled", alias="company__isDepartmentIncomeSplitEnabled")
    company_insurance_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Company insurance type", alias="company__insuranceType")
    company_is_use_of_vacation_days_in_advance_enabled: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Company is use of vacation days in advance enabled", alias="company__isUseOfVacationDaysInAdvanceEnabled")
    company_is_horesta_supplement_enabled: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Company is horesta supplement enabled", alias="company__isHorestaSupplementEnabled")
    company_has_holiday_payment_netto_transfer_or_payout: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Company has holiday payment netto transfer or payout", alias="company__hasHolidayPaymentNettoTransferOrPayout")
    company_is_sh_payout_netto_enabled: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Company is SH payout netto enabled", alias="company__isShPayoutNettoEnabled")
    company_is_transfer_fifth_holiday_week_enabled: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Company is transfer fifth holiday week enabled", alias="company__isTransferFifthHolidayWeekEnabled")
    company_is_holiday_hindrance_enabled: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Company is holiday hindrance enabled", alias="company__isHolidayHindranceEnabled")
    company_is_extra_holiday_entitlement_in_hours_enabled: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Company is extra holiday entitlement in hours enabled", alias="company__isExtraHolidayEntitlementInHoursEnabled")
    company_extra_holiday_entitlement_in_hours: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Company extra holiday entitlement in hours", alias="company__extraHolidayEntitlementInHours")
    company_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Company ID", alias="company__id")
    company_logo_url: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company logo URL", alias="company__logoUrl")
    company_cvr_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company CVR Number", alias="companyCvrNumber")

    # Department Information (nested object)
    department_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Department UID", alias="department__uid")
    department_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Department name", alias="department__name")
    department_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Department number", alias="department__number")
    department_has_work_schema: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Department has work schema", alias="department__hasWorkSchema")
    department_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Department ID", alias="department__id")

    # Cost Center Information (nested object)
    cost_center_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Cost center UID", alias="costCenter__uid")
    cost_center_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Cost center name", alias="costCenter__name")
    cost_center_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Cost center number", alias="costCenter__number")
    cost_center_type: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Cost center type", alias="costCenter__type")
    cost_center_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Cost center ID", alias="costCenter__id")

    # Profit Center Information (nested object)
    profit_center_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Profit center UID", alias="profitCenter__uid")
    profit_center_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Profit center name", alias="profitCenter__name")
    profit_center_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Profit center number", alias="profitCenter__number")
    profit_center_type: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Profit center type", alias="profitCenter__type")
    profit_center_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Profit center ID", alias="profitCenter__id")

    # Company Cost Center Information (nested object)
    company_cost_center_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company cost center UID", alias="companyCostCenter__uid")
    company_cost_center_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company cost center name", alias="companyCostCenter__costCenterName")
    company_cost_center_code: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company cost center code", alias="companyCostCenter__costCenterCode")
    company_cost_center_type: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company cost center type", alias="companyCostCenter__type")
    company_cost_center_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Company cost center ID", alias="companyCostCenter__id")
    company_cost_center_number_of_employees: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Company cost center number of employees", alias="companyCostCenter__numberOfEmployees")
    company_cost_center_employee_uids: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company cost center employee UIDs", alias="companyCostCenter__employeeUids")
    company_cost_center_fk: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company cost center FK", alias="companyCostCenterFk")

    # Company Profit Center Information (nested object)
    company_profit_center_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company profit center UID", alias="companyProfitCenter__uid")
    company_profit_center_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company profit center name", alias="companyProfitCenter__costCenterName")
    company_profit_center_code: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company profit center code", alias="companyProfitCenter__costCenterCode")
    company_profit_center_type: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company profit center type", alias="companyProfitCenter__type")
    company_profit_center_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Company profit center ID", alias="companyProfitCenter__id")
    company_profit_center_number_of_employees: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Company profit center number of employees", alias="companyProfitCenter__numberOfEmployees")
    company_profit_center_employee_uids: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company profit center employee UIDs", alias="companyProfitCenter__employeeUids")

    # User Information (nested object)
    user_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="User UID", alias="user__uid")
    user_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="User name", alias="user__name")
    user_email: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="User email", alias="user__email")
    user_is_active: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="User is active", alias="user__isActive")
    user_photo_url: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="User photo URL", alias="user__photoUrl")
    user_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="User ID", alias="user__id")

    # Additional Information
    car_registration_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Car registration number", alias="carRegistrationNumber")
    linked_in: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="LinkedIn profile", alias="linkedIn")
    konto_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Konto number", alias="kontoNumber")
    reg_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Registration number", alias="regNumber")
    country_code: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Country code", alias="country")
    language: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Language", alias="language")
    iban: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="IBAN", alias="iban")
    swift: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="SWIFT/BIC", alias="swift")
    tax: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Tax code", alias="tax")
    image_url: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Image URL", alias="imageUrl")
    created_on: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Created on", alias="createdOn")
    global_value_set_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Global value set number", alias="globalValueSetNumber")
    revenue_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Revenue type", alias="revenueType")
    income_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Income type", alias="incomeType")
    holiday_pay_receiver_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Holiday pay receiver type", alias="holidayPayReceiverType")
    can_change_holiday_pay_receiver: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Can change holiday pay receiver", alias="canChangeHolidayPayReceiver")
    extra_holiday_entitlement_rule: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Extra holiday entitlement rule", alias="extraHolidayEntitlementRule")
    type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee type", alias="type")
    invited_by_email: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Invited by email", alias="invitedByEmail")

    # Raw nested objects presence (optional, to map top-level fields if provided)
    cost_center: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Raw cost center object", alias="costCenter")
    profit_center: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Raw profit center object", alias="profitCenter")
    company_profit_center: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Raw company profit center object", alias="companyProfitCenter")
    company_cost_center: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Raw company cost center object", alias="companyCostCenter")

    class _Annotation:
        primary_key = "uid"
        foreign_keys = {
            "company_uid": {
                "parent_schema": "CompaniesGet",
                "parent_column": "uid",
                "cardinality": "N:1",
            },
            "department_uid": {
                "parent_schema": "DepartmentsGet",
                "parent_column": "uid",
                "cardinality": "N:1",
            },
            "cost_center_uid": {
                "parent_schema": "CostCentersGet",
                "parent_column": "uid",
                "cardinality": "N:1",
            },
            "profit_center_uid": {
                "parent_schema": "CostCentersGet",
                "parent_column": "uid",
                "cardinality": "N:1",
            },
            "company_cost_center_uid": {
                "parent_schema": "CostCentersGet",
                "parent_column": "uid",
                "cardinality": "N:1",
            },
            "company_profit_center_uid": {
                "parent_schema": "CostCentersGet",
                "parent_column": "uid",
                "cardinality": "N:1",
            },
        }


class EmployeesGetById(BrynQPanderaDataFrameModel):
    """Detailed flattened schema for Zenegy Employee (get_by_id) output data"""

    # Reuse base identification and common fields from EmployeesGet
    uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee unique identifier", alias="uid")
    id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee ID", alias="id")
    employee_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee number", alias="employeeNumber")
    extra_employee_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Extra employee number", alias="extraEmployeeNumber")
    name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee name", alias="name")
    title: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee title", alias="title")
    cpr: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="CPR number", alias="cpr")
    email: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Contact email", alias="contactEmail")
    contact_phone: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Contact phone", alias="contactPhone")
    address: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Address", alias="address")
    city: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="City", alias="city")
    postal_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Postal number", alias="postalNumber")
    mobile_phone: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Mobile phone", alias="mobilePhone")
    employment_date: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employment date", alias="employmentDate")
    date_of_resignation: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Date of resignation", alias="dateOfResignation")
    last_work_day: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Last work day", alias="lastWorkDay")
    salary_mode: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Salary mode", alias="salaryMode")
    salary_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Salary type", alias="salaryType")
    salary_payout_period: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Salary payout period", alias="salaryPayoutPeriod")
    is_active: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is active", alias="isActive")
    is_resigned: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is resigned", alias="isResigned")
    is_foreign: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is foreign", alias="isForeign")
    is_cpr_validated: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is CPR validated", alias="isCprValidated")
    has_payroll: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Has payroll", alias="hasPayroll")
    has_user: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Has user", alias="hasUser")
    has_profile_image: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Has profile image", alias="hasProfileImage")
    is_resigned_within_last_year: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is resigned within last year", alias="isResignedWithinLastyear")
    is_resigned_with_registrations: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is resigned with registrations", alias="isResignedWithRegistrations")

    # Nested: company
    company_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company UID", alias="company__uid")
    company_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company name", alias="company__name")
    company_cvr: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company CVR", alias="company__cvr")
    company_association_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Company association ID", alias="company__associationId")
    company_p_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company P number", alias="company__pNumber")
    company_insurance_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Company insurance type", alias="company__insuranceType")
    company_is_department_income_split_enabled: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Company dept income split", alias="company__isDepartmentIncomeSplitEnabled")
    company_is_holiday_hindrance_enabled: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Company holiday hindrance", alias="company__isHolidayHindranceEnabled")
    company_is_horesta_supplement_enabled: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Company horesta supplement", alias="company__isHorestaSupplementEnabled")
    company_is_sh_payout_netto_enabled: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Company SH payout netto", alias="company__isShPayoutNettoEnabled")
    company_is_transfer_fifth_holiday_week_enabled: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Company transfer 5th week", alias="company__isTransferFifthHolidayWeekEnabled")
    company_is_use_of_vacation_days_in_advance_enabled: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Company vacation in advance", alias="company__isUseOfVacationDaysInAdvanceEnabled")
    company_has_holiday_payment: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Company has holiday payment", alias="company__hasHolidayPayment")
    company_has_benefit_package: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Company benefit package", alias="company__hasBenefitPackage")
    company_has_benefit_package_two: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Company benefit package two", alias="company__hasBenefitPackageTwo")
    company_has_am_pension: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Company AM pension", alias="company__hasAmPension")
    company_extra_holiday_entitlement_in_hours: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Company extra holiday entitlement in hours", alias="company__extraHolidayEntitlementInHours")
    company_logo_url: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company logo URL", alias="company__logoUrl")

    # Department (nested)
    department_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Department UID", alias="department__uid")
    department_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Department name", alias="department__name")
    department_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Department number", alias="department__number")
    department_has_work_schema: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Department has work schema", alias="department__hasWorkSchema")
    department_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Department ID", alias="department__id")

    # Company Cost/Profit Center (nested)
    company_cost_center_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company cost center UID", alias="companyCostCenter__uid")
    company_cost_center_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company cost center name", alias="companyCostCenter__costCenterName")
    company_cost_center_code: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company cost center code", alias="companyCostCenter__costCenterCode")
    company_cost_center_type: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company cost center type", alias="companyCostCenter__type")
    company_cost_center_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Company cost center ID", alias="companyCostCenter__id")
    company_cost_center_number_of_employees: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Company cost center num employees", alias="companyCostCenter__numberOfEmployees")
    company_profit_center_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company profit center UID", alias="companyProfitCenter__uid")
    company_profit_center_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company profit center name", alias="companyProfitCenter__costCenterName")
    company_profit_center_code: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company profit center code", alias="companyProfitCenter__costCenterCode")
    company_profit_center_type: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company profit center type", alias="companyProfitCenter__type")
    company_profit_center_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Company profit center ID", alias="companyProfitCenter__id")

    # User (nested)
    user_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="User UID", alias="user__uid")
    user_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="User name", alias="user__name")
    user_email: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="User email", alias="user__email")
    user_is_active: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="User is active", alias="user__isActive")
    user_photo_url: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="User photo URL", alias="user__photoUrl")
    user_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="User ID", alias="user__id")

    # Additional high-detail fields
    p_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee pNumber", alias="pNumber")
    ancinity_date: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Ancininity date", alias="ancinityDate")
    atp_type: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="ATP Type", alias="atpType")
    additional_tax_rate: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Additional tax rate", alias="additionalTaxRate")
    benefit_package_amount: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Benefit package amount", alias="benefitPackageAmount")
    benefit_package_amount_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Benefit package amount type", alias="benefitPackageAmountType")
    benefit_package_two_amount: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Benefit package two amount", alias="benefitPackageTwoAmount")
    benefit_package_two_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Benefit package two type", alias="benefitPackageTwoType")
    benefit_package_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Benefit package type", alias="benefitPackageType")
    benefit_package_payout_months: Optional[Series[object]] = pa.Field(coerce=True, nullable=True, description="Benefit package payout months", alias="benefitPackagePayoutMonths")
    include_benefit_package_in_pension: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Include benefit package in pension", alias="includeBenefitPackageInPension")
    include_benefit_package_two_in_pension: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Include benefit package two in pension", alias="includeBenefitPackageTwoInPension")
    enable_file_transfer: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Enable file transfer", alias="enableFileTransfer")
    invitation_text: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Invitation text", alias="invitationText")
    is_absence_freechoice_enabled: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Absence freechoice enabled", alias="isAbsenceFreechoiceEnabled")
    is_after_september_2021: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="After September 2021", alias="isAfterSeptember2021")
    is_automatic_payroll: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Automatic payroll", alias="isAutomaticPayroll")
    is_e_boks_enabled: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="e-Boks enabled", alias="isEBoksEnabled")
    is_employee_look_like_other_employee: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Employee look like other", alias="isEmployeeLookLikeOtherEmployee")
    is_insurance_inclusive_in_pension: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Insurance inclusive in pension", alias="isInsuranceInclusiveInPension")
    is_insurance_taxable: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Insurance taxable", alias="isInsuranceTaxable")
    is_tracking_negative_salary_enabled: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Tracking negative salary enabled", alias="isTrackingNegativeSalaryEnabled")
    job_description: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Job description", alias="jobDescription")
    kr_rate: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="KR rate", alias="krRate")
    labour_agreement_code: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Labour agreement code", alias="labourAgreementCode")
    labour_benefits_package_for_pension: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Labour benefits package for pension", alias="labourBenefitsPackageForPension")
    labour_company_pension: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Labour company pension", alias="labourCompanyPension")
    labour_private_pension: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Labour private pension", alias="labourPrivatePension")
    last_time_skat_card_updated: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Last time skat card updated", alias="lastTimeSkatCardUpdated")
    look_like_employee_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Look like employee uid", alias="lookLikeEmployeeUid")
    max_loan: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Max loan", alias="maxLoan")
    maximum_number_of_days_used_in_advance: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Max days used in advance", alias="maximumNumberOfDaysUsedInAdvance")
    monthly_salary: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Monthly salary", alias="monthlySalary")
    monthly_salary_fixed_base: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Monthly salary fixed base", alias="monthlySalaryFixedBase")
    nem_konto_payment: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="NemKonto payment", alias="nemKontoPayment")
    number_of_hours: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Number of hours", alias="numberOfHours")
    number_of_hours_fixed: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Number of hours fixed", alias="numberOfHoursFixed")
    number_of_working_days: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Number of working days", alias="numberOfWorkingDays")
    pension_institute_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Pension institute type", alias="pensionInstituteType")
    roles: Optional[Series[object]] = pa.Field(coerce=True, nullable=True, description="Roles", alias="roles")
    sh_months_select: Optional[Series[object]] = pa.Field(coerce=True, nullable=True, description="SH months select", alias="shMonthsSelect")
    sh_payout_netto_months_select: Optional[Series[object]] = pa.Field(coerce=True, nullable=True, description="SH payout netto months select", alias="shPayoutNettoMonthsSelect")
    show_current_saldo: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Show current saldo", alias="showCurrentSaldo")
    show_relatives_and_documents: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Show relatives and documents", alias="showRelativesAndDocuments")
    special_supplement_payout_months: Optional[Series[object]] = pa.Field(coerce=True, nullable=True, description="Special supplement payout months", alias="specialSupplementPayoutMonths")
    special_supplement_type: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Special supplement type", alias="specialSupplementType")
    standard_rate: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Standard rate", alias="standardRate")
    standard_rate_hourly: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Standard rate hourly", alias="standardRateHourly")
    booking_group: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Booking group", alias="bookingGroup")
    tin_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="TIN number", alias="tinNumber")
    transfer_netto: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Transfer netto", alias="transferNetto")
    work_time_employment_info: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Work time employment info", alias="workTimeEmploymentInfo")

    # Holiday pay receiver (nested object)
    holiday_pay_receiver_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Holiday pay receiver uid", alias="holidayPayReceiver__uid")
    holiday_pay_receiver_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Holiday pay receiver id", alias="holidayPayReceiver__id")
    holiday_pay_receiver_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Holiday pay receiver name", alias="holidayPayReceiver__name")
    holiday_pay_receiver_cvr: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Holiday pay receiver cvr", alias="holidayPayReceiver__cvr")
    holiday_pay_receiver_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Holiday pay receiver type", alias="holidayPayReceiver__type")

    # Global value set information (nested)
    global_value_set_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Global value set name", alias="globalValueSetInformation__globalValueSetName")
    global_value_set_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Global value set number", alias="globalValueSetInformation__globalValueSetNumber")
    global_value_set_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Global value set uid", alias="globalValueSetInformation__globalValueSetUid")
    global_value_set_information__global_value_in_set_assignment_dto: Optional[Series[object]] = pa.Field(coerce=True, nullable=True, description="Global value in set assignment DTO", alias="globalValueSetInformation__globalValueInSetAssignmentDto")
    global_value_information: Optional[Series[object]] = pa.Field(coerce=True, nullable=True, description="Global value information", alias="globalValueInformation")

    # Financials present only in detailed view
    group_insurance: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Group insurance", alias="groupInsurance")
    holiday_days_per_year: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Holiday days per year", alias="holidayDaysPerYear")
    holiday_saved_rate: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Holiday saved rate", alias="holidaySavedRate")
    holiday_pay_rate: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Holiday pay rate", alias="holidayPayRate")
    holiday_payment_amount: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Holiday payment amount", alias="holidayPaymentAmount")
    holiday_payment_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Holiday payment type", alias="holidayPaymentType")
    holiday_registry_code: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Holiday registry code", alias="holidayRegistryCode")
    holiday_handling_code: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Holiday handling code", alias="holidayHandlingCode")
    holidays: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Holidays", alias="holidays")
    horesta_supplement: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Horesta supplement", alias="horestaSupplement")
    insurance_category: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Insurance category", alias="insuranceCategory")

    # Tax cards and complex arrays
    tax_cards: Optional[Series[object]] = pa.Field(coerce=True, nullable=True, description="Tax cards", alias="taxCards")
    employee_department_income_splits: Optional[Series[object]] = pa.Field(coerce=True, nullable=True, description="Employee department income splits", alias="employeeDepartmentIncomeSplits")
    employee_values_information: Optional[Series[object]] = pa.Field(coerce=True, nullable=True, description="Employee values information", alias="employeeValuesInformation")
    extra_hours_payments: Optional[Series[object]] = pa.Field(coerce=True, nullable=True, description="Extra hours payments", alias="extraHoursPayments")
    benefits: Optional[Series[object]] = pa.Field(coerce=True, nullable=True, description="Benefits", alias="benefits")
    paychecks: Optional[Series[object]] = pa.Field(coerce=True, nullable=True, description="Paychecks", alias="paychecks")
    pensions: Optional[Series[object]] = pa.Field(coerce=True, nullable=True, description="Pensions", alias="pensions")
    relatives: Optional[Series[object]] = pa.Field(coerce=True, nullable=True, description="Relatives", alias="relatives")
    resignation: Optional[Series[object]] = pa.Field(coerce=True, nullable=True, description="Resignation data", alias="resignation")
    am_pension: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="AM pension", alias="amPension")
    personal_identification_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Personal identification number", alias="personalIdentificationNumber")
    holiday_supplement: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Holiday supplement", alias="holidaySupplement")
    care_days_per_year: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Care days per year", alias="careDaysPerYear")
    additional_days_per_year: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Additional days per year", alias="additionalDaysPerYear")
    maximum_number_of_days_used_in_advance: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Maximum number of days used in advance", alias="maximumNumberOfDaysUsedInAdvance")
    max_loan: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Maximum loan", alias="maxLoan")
    maternity_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Maternity type", alias="maternityType")
    start_saldo_holiday_periods: Optional[Series[object]] = pa.Field(coerce=True, nullable=True, description="Start saldo holiday periods", alias="startSaldoHolidayPeriods")

    # Massive set of start* numeric fields (float)
    start_a_skat: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startASkat")
    start_am: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startAm")
    start_am_contributions_wages_and_holidaypay: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startAmContributionsWagesAndHolidaypay")
    start_am_income: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startAmIncome")
    start_anniversary_bonus_saldo: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startAnniversaryBonusSaldo")
    start_atp: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startAtp")
    start_b_in_come_without_am: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startBInComeWithoutAm")
    start_b_income_with_am: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startBIncomeWithAm")
    start_benefits_package_earned: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startBenefitsPackageEarned")
    start_benefits_package_saldo: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startBenefitsPackageSaldo")
    start_benefits_package_two_earned: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startBenefitsPackageTwoEarned")
    start_benefits_package_two_saldo: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startBenefitsPackageTwoSaldo")
    start_christmas_gifts_benefit: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startChristmasGiftsBenefit")
    start_company_amp: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startCompanyAmp")
    start_company_car: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startCompanyCar")
    start_company_lodging: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startCompanyLodging")
    start_contributory_income: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startContributoryIncome")
    start_current_year_day_of_prayer_compensation_earned: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startCurrentYearDayOfPrayerCompensationEarned")
    start_current_year_day_of_prayer_compensation_paidout: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startCurrentYearDayOfPrayerCompensationPaidout")
    start_days_for_transfer_fifth_holiday_week_current_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startDaysForTransferFifthHolidayWeekCurrentPeriod")
    start_days_for_transfer_fifth_holiday_week_previous_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startDaysForTransferFifthHolidayWeekPreviousPeriod")
    start_days_for_transfer_fifth_holiday_week_three_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startDaysForTransferFifthHolidayWeekThreePeriodsBefore")
    start_days_for_transfer_fifth_holiday_week_two_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startDaysForTransferFifthHolidayWeekTwoPeriodsBefore")
    start_days_to_payout_or_transfer_fifth_holiday_week_current_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startDaysToPayoutOrTransferFifthHolidayWeekCurrentPeriod")
    start_days_to_payout_or_transfer_fifth_holiday_week_previous_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startDaysToPayoutOrTransferFifthHolidayWeekPreviousPeriod")
    start_days_to_payout_or_transfer_fifth_holiday_week_three_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startDaysToPayoutOrTransferFifthHolidayWeekThreePeriodsBefore")
    start_days_to_payout_or_transfer_fifth_holiday_week_two_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startDaysToPayoutOrTransferFifthHolidayWeekTwoPeriodsBefore")
    start_earned_care_days_current_year: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startEarnedCareDaysCurrentYear")
    start_earned_care_days_three_years_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startEarnedCareDaysThreeYearsBefore")
    start_earned_care_days_two_years_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startEarnedCareDaysTwoYearsBefore")
    start_earned_care_days_year_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startEarnedCareDaysYearBefore")
    start_earned_free_vacation_days_current_year: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startEarnedFreeVacationDaysCurrentYear")
    start_earned_free_vacation_days_three_years_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startEarnedFreeVacationDaysThreeYearsBefore")
    start_earned_free_vacation_days_two_years_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startEarnedFreeVacationDaysTwoYearsBefore")
    start_earned_free_vacation_days_year_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startEarnedFreeVacationDaysYearBefore")
    start_earned_holiday_pay_gross_current_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startEarnedHolidayPayGrossCurrentPeriod")
    start_earned_holiday_pay_gross_frozen_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startEarnedHolidayPayGrossFrozenPeriod")
    start_earned_holiday_pay_gross_previous_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startEarnedHolidayPayGrossPreviousPeriod")
    start_earned_holiday_pay_gross_three_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startEarnedHolidayPayGrossThreePeriodsBefore")
    start_earned_holiday_pay_gross_two_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startEarnedHolidayPayGrossTwoPeriodsBefore")
    start_earned_holiday_pay_net_amount_current_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startEarnedHolidayPayNetAmountCurrentPeriod")
    start_earned_holiday_pay_net_amount_frozen_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startEarnedHolidayPayNetAmountFrozenPeriod")
    start_earned_holiday_pay_net_amount_previous_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startEarnedHolidayPayNetAmountPreviousPeriod")
    start_earned_holiday_pay_net_amount_two_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startEarnedHolidayPayNetAmountTwoPeriodsBefore")
    start_earned_vacations_legitimate_salary_amount_current_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startEarnedVacationsLegitimateSalaryAmountCurrentPeriod")
    start_earned_vacations_legitimate_salary_amount_frozen_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startEarnedVacationsLegitimateSalaryAmountFrozenPeriod")
    start_earned_vacations_legitimate_salary_amount_previous_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startEarnedVacationsLegitimateSalaryAmountPreviousPeriod")
    start_earned_vacations_legitimate_salary_amount_three_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startEarnedVacationsLegitimateSalaryAmountThreePeriodsBefore")
    start_earned_vacations_legitimate_salary_amount_two_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startEarnedVacationsLegitimateSalaryAmountTwoPeriodsBefore")
    start_flex_hours: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startFlexHours")
    start_free_phone: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startFreePhone")
    start_g_days: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startGDays")
    start_gross_holiday_pay_for_transfer_fifth_holiday_week_current_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startGrossHolidayPayForTransferFifthHolidayWeekCurrentPeriod")
    start_gross_holiday_pay_for_transfer_fifth_holiday_week_previous_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startGrossHolidayPayForTransferFifthHolidayWeekPreviousPeriod")
    start_gross_holiday_pay_for_transfer_fifth_holiday_week_three_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startGrossHolidayPayForTransferFifthHolidayWeekThreePeriodsBefore")
    start_gross_holiday_pay_for_transfer_fifth_holiday_week_two_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startGrossHolidayPayForTransferFifthHolidayWeekTwoPeriodsBefore")
    start_gross_holiday_pay_per_day_fifth_holiday_week_current_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startGrossHolidayPayPerDayFifthHolidayWeekCurrentPeriod")
    start_gross_holiday_pay_per_day_fifth_holiday_week_previous_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startGrossHolidayPayPerDayFifthHolidayWeekPreviousPeriod")
    start_gross_holiday_pay_per_day_fifth_holiday_week_three_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startGrossHolidayPayPerDayFifthHolidayWeekThreePeriodsBefore")
    start_gross_holiday_pay_per_day_fifth_holiday_week_two_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startGrossHolidayPayPerDayFifthHolidayWeekTwoPeriodsBefore")
    start_gross_holiday_pay_transferred_fifth_holiday_week_current_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startGrossHolidayPayTransferredFifthHolidayWeekCurrentPeriod")
    start_gross_holiday_pay_transferred_fifth_holiday_week_previous_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startGrossHolidayPayTransferredFifthHolidayWeekPreviousPeriod")
    start_gross_holiday_pay_transferred_fifth_holiday_week_three_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startGrossHolidayPayTransferredFifthHolidayWeekThreePeriodsBefore")
    start_gross_holiday_pay_transferred_fifth_holiday_week_two_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startGrossHolidayPayTransferredFifthHolidayWeekTwoPeriodsBefore")
    start_group_life: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startGroupLife")
    start_group_life_2: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startGroupLife2")
    start_health_insurance: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHealthInsurance")
    start_health_insurance_no_am_pension: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHealthInsuranceNoAmPension")
    start_health_insurance_no_am_pension_no_vacation_entitled_money: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHealthInsuranceNoAmPensionNoVacationEntitledMoney")
    start_holday_at_own_expense_current_year: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHoldayAtOwnExpenseCurrentYear")
    start_holday_at_own_expense_current_year_saldo: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHoldayAtOwnExpenseCurrentYearSaldo")
    start_holday_at_own_expense_three_years_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHoldayAtOwnExpenseThreeYearsBefore")
    start_holday_at_own_expense_three_years_before_saldo: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHoldayAtOwnExpenseThreeYearsBeforeSaldo")
    start_holday_at_own_expense_two_years_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHoldayAtOwnExpenseTwoYearsBefore")
    start_holday_at_own_expense_two_years_before_saldo: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHoldayAtOwnExpenseTwoYearsBeforeSaldo")
    start_holday_at_own_expense_year_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHoldayAtOwnExpenseYearBefore")
    start_holday_at_own_expense_year_before_saldo: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHoldayAtOwnExpenseYearBeforeSaldo")
    start_holiday_hindrance_transferred_days_fifth_holiday_week_current_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHolidayHindranceTransferredDaysFifthHolidayWeekCurrentPeriod")
    start_holiday_hindrance_transferred_days_fifth_holiday_week_previous_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHolidayHindranceTransferredDaysFifthHolidayWeekPreviousPeriod")
    start_holiday_hindrance_transferred_days_fifth_holiday_week_three_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHolidayHindranceTransferredDaysFifthHolidayWeekThreePeriodsBefore")
    start_holiday_hindrance_transferred_days_fifth_holiday_week_two_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHolidayHindranceTransferredDaysFifthHolidayWeekTwoPeriodsBefore")
    start_holiday_hindrance_used_days_fifth_holiday_week_current_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHolidayHindranceUsedDaysFifthHolidayWeekCurrentPeriod")
    start_holiday_hindrance_used_days_fifth_holiday_week_previous_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHolidayHindranceUsedDaysFifthHolidayWeekPreviousPeriod")
    start_holiday_hindrance_used_days_fifth_holiday_week_three_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHolidayHindranceUsedDaysFifthHolidayWeekThreePeriodsBefore")
    start_holiday_hindrance_used_days_fifth_holiday_week_two_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHolidayHindranceUsedDaysFifthHolidayWeekTwoPeriodsBefore")
    start_holiday_pay_gross_used_fifth_holiday_week_current_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHolidayPayGrossUsedFifthHolidayWeekCurrentPeriod")
    start_holiday_pay_gross_used_fifth_holiday_week_previous_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHolidayPayGrossUsedFifthHolidayWeekPreviousPeriod")
    start_holiday_pay_gross_used_fifth_holiday_week_three_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHolidayPayGrossUsedFifthHolidayWeekThreePeriodsBefore")
    start_holiday_pay_gross_used_fifth_holiday_week_two_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHolidayPayGrossUsedFifthHolidayWeekTwoPeriodsBefore")
    start_holiday_payment_advance: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHolidayPaymentAdvance")
    start_holiday_payment_advance_year_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHolidayPaymentAdvanceYearBefore")
    start_holiday_payment_saldo_netto: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHolidayPaymentSaldoNetto")
    start_holiday_payment_saved: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHolidayPaymentSaved")
    start_holiday_payment_saved_netto: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHolidayPaymentSavedNetto")
    start_holiday_payment_saved_netto_year_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHolidayPaymentSavedNettoYearBefore")
    start_holiday_payment_saved_year_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHolidayPaymentSavedYearBefore")
    start_holiday_supplement_current_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHolidaySupplementCurrentPeriod")
    start_holiday_supplement_previous_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHolidaySupplementPreviousPeriod")
    start_holiday_supplement_three_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHolidaySupplementThreePeriodsBefore")
    start_holiday_supplement_two_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHolidaySupplementTwoPeriodsBefore")
    start_holiday_supplement_value: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHolidaySupplementValue")
    start_hours: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startHours")
    start_lost_days_fifth_holiday_week_current_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startLostDaysFifthHolidayWeekCurrentPeriod")
    start_lost_days_fifth_holiday_week_previous_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startLostDaysFifthHolidayWeekPreviousPeriod")
    start_lost_days_fifth_holiday_week_three_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startLostDaysFifthHolidayWeekThreePeriodsBefore")
    start_lost_days_fifth_holiday_week_two_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startLostDaysFifthHolidayWeekTwoPeriodsBefore")
    start_lost_gross_holiday_pay_fifth_holiday_week_current_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startLostGrossHolidayPayFifthHolidayWeekCurrentPeriod")
    start_lost_gross_holiday_pay_fifth_holiday_week_previous_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startLostGrossHolidayPayFifthHolidayWeekPreviousPeriod")
    start_lost_gross_holiday_pay_fifth_holiday_week_three_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startLostGrossHolidayPayFifthHolidayWeekThreePeriodsBefore")
    start_lost_gross_holiday_pay_fifth_holiday_week_two_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startLostGrossHolidayPayFifthHolidayWeekTwoPeriodsBefore")
    start_mileage: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startMileage")
    start_mileage_low_rate: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startMileageLowRate")
    start_negative_salary_saldo: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startNegativeSalarySaldo")
    start_net_holiday_pay: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startNetHolidayPay")
    start_not_covered_by_triviality: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startNotCoveredByTriviality")
    start_number_of_vacation_days: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startNumberOfVacationDays")
    start_number_of_vacation_days_current_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startNumberOfVacationDaysCurrentPeriod")
    start_number_of_vacation_days_fifth_holiday_week_three_years_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startNumberOfVacationDaysFifthHolidayWeekThreeYearsBefore")
    start_number_of_vacation_days_fifth_holiday_week_two_years_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startNumberOfVacationDaysFifthHolidayWeekTwoYearsBefore")
    start_number_of_vacation_days_frozen_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startNumberOfVacationDaysFrozenPeriod")
    start_number_of_vacation_days_previous_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startNumberOfVacationDaysPreviousPeriod")
    start_number_of_vacation_days_three_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startNumberOfVacationDaysThreePeriodsBefore")
    start_number_of_vacation_days_two_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startNumberOfVacationDaysTwoPeriodsBefore")
    start_number_used_vacation_days_fifth_holiday_week_three_years_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startNumberUsedVacationDaysFifthHolidayWeekThreeYearsBefore")
    start_number_used_vacation_days_fifth_holiday_week_two_years_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startNumberUsedVacationDaysFifthHolidayWeekTwoYearsBefore")
    start_one_time_income: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startOneTimeIncome")
    start_other_benefit: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startOtherBenefit")
    start_paid_days_fifth_holiday_week_current_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startPaidDaysFifthHolidayWeekCurrentPeriod")
    start_paid_days_fifth_holiday_week_previous_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startPaidDaysFifthHolidayWeekPreviousPeriod")
    start_paid_days_fifth_holiday_week_three_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startPaidDaysFifthHolidayWeekThreePeriodsBefore")
    start_paid_days_fifth_holiday_week_two_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startPaidDaysFifthHolidayWeekTwoPeriodsBefore")
    start_payout_from_fifth_holiday_week_current_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startPayoutFromFifthHolidayWeekCurrentPeriod")
    start_payout_from_fifth_holiday_week_previous_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startPayoutFromFifthHolidayWeekPreviousPeriod")
    start_payout_from_fifth_holiday_week_three_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startPayoutFromFifthHolidayWeekThreePeriodsBefore")
    start_payout_from_fifth_holiday_week_two_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startPayoutFromFifthHolidayWeekTwoPeriodsBefore")
    start_pension_from_company: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startPensionFromCompany")
    start_personal_amp: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startPersonalAmp")
    start_personal_pension: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startPersonalPension")
    start_severance_saldo: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startSeveranceSaldo")
    start_special_supplement_earned: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startSpecialSupplementEarned")
    start_special_supplement_saldo: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startSpecialSupplementSaldo")
    start_time_in_lieu_earned_amount: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startTimeInLieuEarnedAmount")
    start_time_in_lieu_earned_hours: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startTimeInLieuEarnedHours")
    start_transferred_days_fifth_holiday_week_current_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startTransferredDaysFifthHolidayWeekCurrentPeriod")
    start_transferred_days_fifth_holiday_week_previous_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startTransferredDaysFifthHolidayWeekPreviousPeriod")
    start_transferred_days_fifth_holiday_week_three_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startTransferredDaysFifthHolidayWeekThreePeriodsBefore")
    start_transferred_days_fifth_holiday_week_two_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startTransferredDaysFifthHolidayWeekTwoPeriodsBefore")
    start_transferred_days_used_fifth_holiday_week_current_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startTransferredDaysUsedFifthHolidayWeekCurrentPeriod")
    start_transferred_days_used_fifth_holiday_week_previous_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startTransferredDaysUsedFifthHolidayWeekPreviousPeriod")
    start_transferred_days_used_fifth_holiday_week_three_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startTransferredDaysUsedFifthHolidayWeekThreePeriodsBefore")
    start_transferred_days_used_fifth_holiday_week_two_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startTransferredDaysUsedFifthHolidayWeekTwoPeriodsBefore")
    start_transferred_gross_holiday_pay_used_fifth_holiday_week_current_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startTransferredGrossHolidayPayUsedFifthHolidayWeekCurrentPeriod")
    start_transferred_gross_holiday_pay_used_fifth_holiday_week_previous_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startTransferredGrossHolidayPayUsedFifthHolidayWeekPreviousPeriod")
    start_transferred_gross_holiday_pay_used_fifth_holiday_week_three_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startTransferredGrossHolidayPayUsedFifthHolidayWeekThreePeriodsBefore")
    start_transferred_gross_holiday_pay_used_fifth_holiday_week_two_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startTransferredGrossHolidayPayUsedFifthHolidayWeekTwoPeriodsBefore")
    start_transferred_gross_holiday_pay_value_per_day_fifth_holiday_week_current_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startTransferredGrossHolidayPayValuePerDayFifthHolidayWeekCurrentPeriod")
    start_transferred_gross_holiday_pay_value_per_day_fifth_holiday_week_previous_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startTransferredGrossHolidayPayValuePerDayFifthHolidayWeekPreviousPeriod")
    start_transferred_gross_holiday_pay_value_per_day_fifth_holiday_week_three_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startTransferredGrossHolidayPayValuePerDayFifthHolidayWeekThreePeriodsBefore")
    start_transferred_gross_holiday_pay_value_per_day_fifth_holiday_week_two_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startTransferredGrossHolidayPayValuePerDayFifthHolidayWeekTwoPeriodsBefore")
    start_travel_allowance: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startTravelAllowance")
    start_travel_allowance_without_payment: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startTravelAllowanceWithoutPayment")
    start_used_care_days_current_year: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startUsedCareDaysCurrentYear")
    start_used_care_days_three_years_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startUsedCareDaysThreeYearsBefore")
    start_used_care_days_two_years_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startUsedCareDaysTwoYearsBefore")
    start_used_care_days_year_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startUsedCareDaysYearBefore")
    start_used_free_vacation_days_current_year: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startUsedFreeVacationDaysCurrentYear")
    start_used_free_vacation_days_three_years_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startUsedFreeVacationDaysThreeYearsBefore")
    start_used_free_vacation_days_two_years_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startUsedFreeVacationDaysTwoYearsBefore")
    start_used_free_vacation_days_year_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startUsedFreeVacationDaysYearBefore")
    start_used_holiday_pay_gross_current_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startUsedHolidayPayGrossCurrentPeriod")
    start_used_holiday_pay_gross_frozen_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startUsedHolidayPayGrossFrozenPeriod")
    start_used_holiday_pay_gross_previous_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startUsedHolidayPayGrossPreviousPeriod")
    start_used_holiday_pay_gross_three_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startUsedHolidayPayGrossThreePeriodsBefore")
    start_used_holiday_pay_gross_two_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startUsedHolidayPayGrossTwoPeriodsBefore")
    start_used_holiday_pay_net_amount_current_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startUsedHolidayPayNetAmountCurrentPeriod")
    start_used_holiday_pay_net_amount_frozen_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startUsedHolidayPayNetAmountFrozenPeriod")
    start_used_holiday_pay_net_amount_previous_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startUsedHolidayPayNetAmountPreviousPeriod")
    start_used_holiday_pay_net_amount_two_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startUsedHolidayPayNetAmountTwoPeriodsBefore")
    start_used_holiday_supplement_current_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startUsedHolidaySupplementCurrentPeriod")
    start_used_holiday_supplement_previous_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startUsedHolidaySupplementPreviousPeriod")
    start_used_holiday_supplement_three_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startUsedHolidaySupplementThreePeriodsBefore")
    start_used_holiday_supplement_two_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startUsedHolidaySupplementTwoPeriodsBefore")
    start_used_vacation_day_units_current_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startUsedVacationDayUnitsCurrentPeriod")
    start_used_vacation_day_units_frozen_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startUsedVacationDayUnitsFrozenPeriod")
    start_used_vacation_day_units_previous_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startUsedVacationDayUnitsPreviousPeriod")
    start_used_vacation_day_units_three_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startUsedVacationDayUnitsThreePeriodsBefore")
    start_used_vacation_day_units_two_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startUsedVacationDayUnitsTwoPeriodsBefore")
    start_vacation_pay_gross_fifth_holiday_week_three_years_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startVacationPayGrossFifthHolidayWeekThreeYearsBefore")
    start_vacation_pay_gross_fifth_holiday_week_two_years_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startVacationPayGrossFifthHolidayWeekTwoYearsBefore")
    start_vacation_pay_gross_used_fifth_holiday_week_three_years_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startVacationPayGrossUsedFifthHolidayWeekThreeYearsBefore")
    start_vacation_pay_gross_used_fifth_holiday_week_two_years_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startVacationPayGrossUsedFifthHolidayWeekTwoYearsBefore")
    start_vacation_supplement_earned_fifth_holiday_week_three_years_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startVacationSupplementEarnedFifthHolidayWeekThreeYearsBefore")
    start_vacation_supplement_earned_fifth_holiday_week_two_years_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startVacationSupplementEarnedFifthHolidayWeekTwoYearsBefore")
    start_vacation_supplement_used_fifth_holiday_week_three_years_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startVacationSupplementUsedFifthHolidayWeekThreeYearsBefore")
    start_vacation_supplement_used_fifth_holiday_week_two_years_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startVacationSupplementUsedFifthHolidayWeekTwoYearsBefore")
    start_vacation_supplement_value_per_day_fifth_holiday_week_current_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startVacationSupplementValuePerDayFifthHolidayWeekCurrentPeriod")
    start_vacation_supplement_value_per_day_fifth_holiday_week_previous_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startVacationSupplementValuePerDayFifthHolidayWeekPreviousPeriod")
    start_vacation_supplement_value_per_day_fifth_holiday_week_three_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startVacationSupplementValuePerDayFifthHolidayWeekThreePeriodsBefore")
    start_vacation_supplement_value_per_day_fifth_holiday_week_two_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startVacationSupplementValuePerDayFifthHolidayWeekTwoPeriodsBefore")
    start_vacations_legitimate_salary_fifth_holiday_week_three_years_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startVacationsLegitimateSalaryFifthHolidayWeekThreeYearsBefore")
    start_vacations_legitimate_salary_fifth_holiday_week_two_years_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startVacationsLegitimateSalaryFifthHolidayWeekTwoYearsBefore")
    start_value_for_days_to_payout_fifth_holiday_week_current_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startValueForDaysToPayoutFifthHolidayWeekCurrentPeriod")
    start_value_for_days_to_payout_fifth_holiday_week_previous_period: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startValueForDaysToPayoutFifthHolidayWeekPreviousPeriod")
    start_value_for_days_to_payout_fifth_holiday_week_three_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startValueForDaysToPayoutFifthHolidayWeekThreePeriodsBefore")
    start_value_for_days_to_payout_fifth_holiday_week_two_periods_before: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startValueForDaysToPayoutFifthHolidayWeekTwoPeriodsBefore")
    start_year_before_day_of_prayer_compensation_earned: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startYearBeforeDayOfPrayerCompensationEarned")
    start_year_before_day_of_prayer_compensation_paidout: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, alias="startYearBeforeDayOfPrayerCompensationPaidout")

    # Existing Workers fields from EmployeesGet not re-listed here are intentionally omitted to avoid duplication
    # but the above covers additional detailed fields present in get_by_id responses.

    class _Annotation:
        primary_key = "uid"
        foreign_keys = {}
