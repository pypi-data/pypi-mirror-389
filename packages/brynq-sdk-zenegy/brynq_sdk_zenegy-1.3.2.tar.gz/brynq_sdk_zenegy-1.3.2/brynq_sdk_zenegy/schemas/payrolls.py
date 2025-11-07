# Generated schemas for tag: Payroll

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from uuid import UUID

# BrynQ Pandera DataFrame Model for Payrolls
from pandera.typing import Series
import pandera as pa
import pandas as pd
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class PayrollsGet(BrynQPanderaDataFrameModel):
    """Flattened schema for Zenegy Payrolls Output data"""
    # Basic payroll fields
    uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Payroll UID", alias="uid")
    type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Payroll type", alias="type")
    period_from: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Period from", alias="periodFrom")
    period_to: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Period to", alias="periodTo")
    disposition_date: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Disposition date", alias="dispositionDate")
    status: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Payroll status", alias="status")
    has_holiday_payment: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Has holiday payment", alias="hasHolidayPayment")
    has_benefit_package: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Has benefit package", alias="hasBenefitPackage")
    has_benefit_package_two: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Has benefit package two", alias="hasBenefitPackageTwo")
    has_am_pension: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Has AM pension", alias="hasAmPension")
    has_approval_flow_enabled: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Has approval flow enabled", alias="hasApprovalFlowEnabled")
    has_holiday_supplement_payout: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Has holiday supplement payout", alias="hasHolidaySupplementPayout")
    disable_payslip_notification: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Disable payslip notification", alias="disablePayslipNotification")
    send_payslip_notification_on: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Send payslip notification on", alias="sendPayslipNotificationOn")
    has_holiday_payment_payout: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Has holiday payment payout", alias="hasHolidayPaymentPayout")
    has_holiday_payment_to_holiday_pay_payout: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Has holiday payment to holiday pay payout", alias="hasHolidayPaymentToHolidayPayPayout")
    has_benefit_package_payout: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Has benefit package payout", alias="hasBenefitPackagePayout")
    has_benefit_package_two_payout: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Has benefit package two payout", alias="hasBenefitPackageTwoPayout")
    is_already_paid: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is already paid", alias="isAlreadyPaid")
    is_eligible_for_revert: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is eligible for revert", alias="isEligibleForRevert")
    note: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Note", alias="note")
    is_forced: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is forced", alias="isForced")
    has_time_in_lieu_payout: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Has time in lieu payout", alias="hasTimeInLieuPayout")
    payslip_status: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Payslip status", alias="payslipStatus")
    is_payroll_approval_enabled_for_payroll: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is payroll approval enabled for payroll", alias="isPayrollApprovalEnabledForPayroll")
    disable_payslip_generation: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Disable payslip generation", alias="disablePayslipGeneration")
    is_tracking_negative_salary_enabled: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is tracking negative salary enabled", alias="isTrackingNegativeSalaryEnabled")
    is_company_extra_entitlement_in_hours: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is company extra entitlement in hours", alias="isCompanyExtraEntitlementInHours")
    is_extra_holiday_entitlement_in_hours_enabled: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is extra holiday entitlement in hours enabled", alias="isExtraHolidayEntitlementInHoursEnabled")
    revert_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Revert type", alias="revertType")
    has_holiday_payment_taxation_and_transfer_to_next_year: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Has holiday payment taxation and transfer to next year", alias="hasHolidayPaymentTaxationAndTransferToNextYear")
    has_holiday_payment_netto_payout: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Has holiday payment netto payout", alias="hasHolidayPaymentNettoPayout")
    has_transfer_sh_netto_and_payout: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Has transfer SH netto and payout", alias="hasTransferShNettoAndPayout")
    has_sh_net_payout: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Has SH net payout", alias="hasShNetPayout")
    has_fifth_holiday_week_payout: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Has fifth holiday week payout", alias="hasFifthHolidayWeekPayout")
    extra_payroll_run: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Extra payroll run", alias="extraPayrollRun")
    is_completed_with_am_accounting: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Is completed with AM accounting", alias="isCompletedWithAmAccounting")
    failed_payroll_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Failed payroll UID", alias="failedPayrollUid")

    # Company fields (nested object)
    company_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company name", alias="company__name")
    company_vat_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company VAT number", alias="company__vatNumber")
    company_company_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Company company type", alias="company__companyType")
    company_transfer_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Company transfer type", alias="company__transferType")
    company_transfer_sh_netto_amount: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Company transfer SH netto amount", alias="company__transferShNettoAmount")
    company_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Company ID", alias="company__id")
    company_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company UID", alias="company__uid")

    # Employees (as JSON string since it's a list of objects)
    employees: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employees list", alias="employees")

    # Employee fields (flattened from employees array)
    employee_personal_identification_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee personal identification number", alias="employee__personalIdentificationNumber")
    employee_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee UID", alias="employee__employeeUid")
    employee_konto_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee konto number", alias="employee__kontoNumber")
    employee_reg_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee reg number", alias="employee__regNumber")
    employee_for_payment: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee for payment", alias="employee__forPayment")
    employee_is_updated: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Employee is updated", alias="employee__isUpdated")
    employee_note: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee note", alias="employee__note")
    employee_payslip_status: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee payslip status", alias="employee__payslipStatus")
    employee_email: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee email", alias="employee__email")
    employee_is_resigned: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Employee is resigned", alias="employee__isResigned")
    employee_has_payroll: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Employee has payroll", alias="employee__hasPayroll")
    employee_salary_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee salary type", alias="employee__salaryType")
    employee_has_errors: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Employee has errors", alias="employee__hasErrors")
    employee_has_warnings: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Employee has warnings", alias="employee__hasWarnings")
    employee_employment_date: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee employment date", alias="employee__employmentDate")
    employee_is_resigned_within_last_year: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Employee is resigned within last year", alias="employee__isResignedWithinLastyear")
    employee_is_resigned_with_registrations: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Employee is resigned with registrations", alias="employee__isResignedWithRegistrations")
    employee_title: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee title", alias="employee__title")
    employee_has_profile_image: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Employee has profile image", alias="employee__hasProfileImage")
    employee_income_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee income type", alias="employee__incomeType")
    employee_holiday_pay_receiver_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee holiday pay receiver type", alias="employee__holidayPayReceiverType")
    employee_extra_holiday_entitlement_rule: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee extra holiday entitlement rule", alias="employee__extraHolidayEntitlementRule")
    employee_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee name", alias="employee__name")
    employee_employee_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee number", alias="employee__employeeNumber")
    employee_extra_employee_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee extra employee number", alias="employee__extraEmployeeNumber")
    employee_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee ID", alias="employee__id")
    employee_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee UID", alias="employee__uid")

    # Employee department fields (nested object)
    employee_department_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee department name", alias="employee__department__name")
    employee_department_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee department number", alias="employee__department__number")
    employee_department_has_work_schema: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Employee department has work schema", alias="employee__department__hasWorkSchema")
    employee_department_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee department ID", alias="employee__department__id")
    employee_department_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee department UID", alias="employee__department__uid")

    # Employee user fields (nested object)
    employee_user_email: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee user email", alias="employee__user__email")
    employee_user_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee user name", alias="employee__user__name")
    employee_user_photo_url: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee user photo URL", alias="employee__user__photoUrl")
    employee_user_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee user ID", alias="employee__user__id")
    employee_user_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee user UID", alias="employee__user__uid")

    # Employee deparment fields (nested object - note the typo in API)
    employee_deparment_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee deparment name", alias="employee__deparment__name")
    employee_deparment_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee deparment number", alias="employee__deparment__number")
    employee_deparment_has_work_schema: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Employee deparment has work schema", alias="employee__deparment__hasWorkSchema")
    employee_deparment_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee deparment ID", alias="employee__deparment__id")
    employee_deparment_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee deparment UID", alias="employee__deparment__uid")

    # Payroll registration periods (as JSON string since it's a list of objects)
    payroll_registration_periods: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Payroll registration periods", alias="payrollRegistrationPeriods")

    class _Annotation:
        primary_key = "uid"
        foreign_keys = {
            "company_uid": {
                "parent_schema": "CompaniesGet",
                "parent_column": "uid",
                "cardinality": "N:1",
            },
            "employee_uid": {
                "parent_schema": "EmployeesGet",
                "parent_column": "uid",
                "cardinality": "N:1",
            },
        }
