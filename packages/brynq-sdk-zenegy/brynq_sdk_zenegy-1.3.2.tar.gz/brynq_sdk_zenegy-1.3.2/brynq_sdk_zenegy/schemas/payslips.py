# Generated schemas for tag: Payslip

from typing import Optional

# BrynQ Pandera DataFrame Model for Payslips
from pandera.typing import Series
import pandera as pa
import pandas as pd
from brynq_sdk_functions import BrynQPanderaDataFrameModel

class PayslipsGet(BrynQPanderaDataFrameModel):
    """Flattened schema for Zenegy Payslips Output data"""
    # Basic payslip fields
    payroll_number: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Payroll number", alias="payrollNumber")
    for_payment: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="For payment", alias="forPayment")
    gross_income: Optional[Series[pd.Float64Dtype]] = pa.Field(coerce=True, nullable=True, description="Gross income", alias="grossIncome")
    type: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Payslip type", alias="type")
    payslip_calculation_status: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Payslip calculation status", alias="payslipCalculationStatus")
    extra_payroll_run: Optional[Series[pd.BooleanDtype]] = pa.Field(coerce=True, nullable=True, description="Extra payroll run", alias="extraPayrollRun")
    id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Payslip ID", alias="id")
    uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Payslip UID", alias="uid")

    # Payroll base fields (nested object)
    payroll_base_period_from: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Payroll base period from", alias="payrollBase__periodFrom")
    payroll_base_period_to: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Payroll base period to", alias="payrollBase__periodTo")
    payroll_base_disposition_date: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Payroll base disposition date", alias="payrollBase__dispositionDate")
    payroll_base_id: Optional[Series[pd.Int64Dtype]] = pa.Field(coerce=True, nullable=True, description="Payroll base ID", alias="payrollBase__id")
    payroll_base_uid: Optional[Series[pd.StringDtype]] = pa.Field(coerce=True, nullable=True, description="Payroll base UID", alias="payrollBase__uid")

    class _Annotation:
        primary_key = "uid"
        foreign_keys = {}
