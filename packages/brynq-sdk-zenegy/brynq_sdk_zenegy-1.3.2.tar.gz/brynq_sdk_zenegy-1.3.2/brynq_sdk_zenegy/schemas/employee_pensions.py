# Generated schemas for tag: EmployeePensions

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from uuid import UUID

class Pension(BaseModel):
    """Schema for pension information."""
    identifier: Optional[str] = Field(default=None, description="Pension identifier", example="PEN-001")
    payment_day_type: Optional[int] = Field(alias="paymentDayType", default=None, description="Payment day type code", example=1)
    info_type: Optional[int] = Field(alias="infoType", default=None, description="Info type code", example=0)
    pbs_is_in_regular_and_am_pension: Optional[bool] = Field(alias="pbsIsInRegularAndAmPension", default=None, description="PBS is in regular and AM pension flag", example=True)
    name: Optional[str] = Field(default=None, description="Pension name", example="ATP Pension")
    resource_name: Optional[str] = Field(alias="resourceName", default=None, description="Resource name", example="ATP")
    pbs_number: Optional[str] = Field(alias="pbsNumber", default=None, description="PBS number", example="1234")
    type: Optional[int] = Field(default=None, description="Pension type code", example=1)
    id: Optional[int] = Field(default=None, description="Internal numeric identifier", example=10)
    uid: Optional[UUID] = Field(example="00000000-0000-0000-0000-000000000000", default=None, description="Pension UID")

    class Config:
        populate_by_name = True

class EmployeePensionCreate(BaseModel):
    pension_uid: Optional[UUID] = Field(
        example="00000000-0000-0000-0000-000000000000", alias="pensionUid", default=None,
        description="Target pension UID (if updating an existing pension)"
    )
    pension: Pension = Field(
        default=None,
        description="Pension master data (name, type, PBS codes)",
        example={"name": "ATP Pension"}
    )
    account_number: Optional[str] = Field(
        alias="accountNumber", default=None,
        description="Employee pension account number", example="1234567890"
    )
    register_number: Optional[str] = Field(
        alias="registerNumber", default=None,
        description="Bank registration number", example="0001"
    )
    private_pension: Optional[float] = Field(
        alias="privatePension", default=None,
        description="Employee private pension contribution", example=500.0
    )
    company_pension: Optional[float] = Field(
        alias="companyPension", default=None,
        description="Company pension contribution", example=1000.0
    )
    policy_reference_number: Optional[str] = Field(
        alias="policyReferenceNumber", default=None,
        description="Policy reference number", example="POL-123"
    )
    pension_value_type: Optional[int] = Field(
        alias="pensionValueType", default=None,
        description="Value type code for pension", example=1
    )
    tax_pension_amount: Optional[bool] = Field(
        alias="taxPensionAmount", default=None,
        description="Whether pension amount is taxable", example=True
    )
    union_code: Optional[str] = Field(
        alias="unionCode", default=None,
        description="Union code", example="UN-1"
    )
    coverage_base_salary: Optional[float] = Field(
        alias="coverageBaseSalary", default=None,
        description="Coverage base salary", example=35000.0
    )
    employee_wage_code: Optional[str] = Field(
        alias="employeeWageCode", default=None,
        description="Employee wage code", example="E100"
    )
    company_wage_code: Optional[str] = Field(
        alias="companyWageCode", default=None,
        description="Company wage code", example="C100"
    )
    insurance_amount: Optional[float] = Field(
        alias="insuranceAmount", default=None,
        description="Insurance amount", example=250.0
    )
    group_life_agreement_number: Optional[str] = Field(
        alias="groupLifeAgreementNumber", default=None,
        description="Group life agreement number", example="GL-001"
    )
    calculate_from_am_pension: Optional[bool] = Field(
        alias="calculateFromAmPension", default=None,
        description="Calculate contributions from AM pension base", example=True
    )
    uid: Optional[UUID] = Field(
        example="00000000-0000-0000-0000-000000000000", default=None,
        description="Inserted employee pension UID"
    )

    class Config:
        populate_by_name = True

# BrynQ Pandera DataFrame Model for Pensions
from pandera.typing import Series
import pandera as pa
import pandas as pd
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class PensionGet(BrynQPanderaDataFrameModel):
    """Flattened schema for Zenegy Pension Output data (single response)"""
    # Basic pension fields
    account_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Account number", alias="accountNumber")
    register_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Register number", alias="registerNumber")
    employee_payroll_fk: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee payroll FK", alias="employeePayrollFk")
    employee_fk: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Employee FK", alias="employeeFk")
    private_pension: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Private pension amount", alias="privatePension")
    company_pension: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Company pension amount", alias="companyPension")
    policy_reference_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Policy reference number", alias="policyReferenceNumber")
    tax_pension_amount: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Tax pension amount", alias="taxPensionAmount")
    pension_value_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Pension value type", alias="pensionValueType")
    union_code: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Union code", alias="unionCode")
    coverage_base_salary: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Coverage base salary", alias="coverageBaseSalary")
    employee_wage_code: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Employee wage code", alias="employeeWageCode")
    company_wage_code: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Company wage code", alias="companyWageCode")
    insurance_amount: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Insurance amount", alias="insuranceAmount")
    group_life_agreement_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Group life agreement number", alias="groupLifeAgreementNumber")
    calculate_from_am_pension: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Calculate from AM pension", alias="calculateFromAmPension")
    id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Pension ID", alias="id")
    uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Pension UID", alias="uid")

    # Pension fields (nested object)
    pension_identifier: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Pension identifier", alias="pension__identifier")
    pension_payment_day_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Pension payment day type", alias="pension__paymentDayType")
    pension_info_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Pension info type", alias="pension__infoType")
    pension_pbs_is_in_regular_and_am_pension: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Pension PBS is in regular and AM pension", alias="pension__pbsIsInRegularAndAmPension")
    pension_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Pension name", alias="pension__name")
    pension_resource_name: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Pension resource name", alias="pension__resourceName")
    pension_pbs_number: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Pension PBS number", alias="pension__pbsNumber")
    pension_type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Pension type", alias="pension__type")
    pension_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Pension ID", alias="pension__id")
    pension_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Pension UID", alias="pension__uid")

    class _Annotation:
        primary_key = "uid"
        foreign_keys = {}
