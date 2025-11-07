from .schemas.payrolls import PayrollsGet
import requests
from uuid import UUID
from typing import Tuple
import pandas as pd
from brynq_sdk_functions import Functions


class Payrolls:
    """
    Handles all payroll-related operations in Zenegy API
    """

    def __init__(self, zenegy):
        """
        Initialize the Payrolls class.

        Args:
            zenegy: The Zenegy instance to use for API calls
        """
        self.zenegy = zenegy
        self.endpoint = f"api/companies/{self.zenegy.company_uid}/payroll"

    def get_employee_payrolls(self, payroll_uid: UUID, employee_uid: UUID) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Get employee payrolls for a specific payroll and employee.

        Args:
            payroll_uid (UUID): The payroll uid
            employee_uid (UUID): The employee uid
        Returns:
            Tuple of (valid_data, invalid_data) DataFrames
        """
        try:
            endpoint = f"{self.endpoint}/{payroll_uid}/employees/{employee_uid}"
            content = self.zenegy.get(endpoint=endpoint)

            # Normalize the response (direct list of dicts)
            df = pd.DataFrame(content)
            if df.empty:
                return pd.DataFrame(), pd.DataFrame()

            # Validate against schema
            valid_data, invalid_data = Functions.validate_data(df, PayrollsGet)

            return valid_data, invalid_data
        except Exception as e:
            raise Exception(f"Failed to retrieve employee payrolls: {str(e)}") from e

    def get_by_id(self, payroll_uid: UUID) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        GetPayroll

        Args:
            payroll_uid (UUID): The payroll uid
        Returns:
            Tuple of (valid_data, invalid_data) DataFrames
        """
        try:
            endpoint = f"{self.endpoint}/{payroll_uid}"
            content = self.zenegy.get(endpoint=endpoint)

            # Normalize the response using record_path for employees array
            df = pd.json_normalize(
                [content],
                record_path='employees',
                meta=['uid', 'type', 'periodFrom', 'periodTo', 'dispositionDate', 'status', 'hasHolidayPayment', 'hasBenefitPackage', 'hasBenefitPackageTwo', 'hasAmPension', 'hasApprovalFlowEnabled', 'company', 'hasHolidaySupplementPayout', 'disablePayslipNotification', 'sendPayslipNotificationOn', 'hasHolidayPaymentPayout', 'hasHolidayPaymentToHolidayPayPayout', 'hasBenefitPackagePayout', 'hasBenefitPackageTwoPayout', 'isAlreadyPaid', 'isEligibleForRevert', 'payrollRegistrationPeriods', 'note', 'isForced', 'hasTimeInLieuPayout', 'payslipStatus', 'isPayrollApprovalEnabledForPayroll', 'disablePayslipGeneration', 'isTrackingNegativeSalaryEnabled', 'isCompanyExtraEntitlementInHours', 'isExtraHolidayEntitlementInHoursEnabled', 'revertType', 'hasHolidayPaymentTaxationAndTransferToNextYear', 'hasHolidayPaymentNettoPayout', 'hasTransferShNettoAndPayout', 'hasShNetPayout', 'hasFifthHolidayWeekPayout', 'extraPayrollRun', 'isCompletedWithAmAccounting', 'failedPayrollUid'],
                record_prefix='employee__',
                sep='__'
            )
            if df.empty:
                return pd.DataFrame(), pd.DataFrame()

            # Validate against schema
            valid_data, invalid_data = Functions.validate_data(df, PayrollsGet)

            return valid_data, invalid_data
        except Exception as e:
            raise Exception(f"Failed to retrieve payroll by ID: {str(e)}") from e

    def delete(self, payroll_uid: UUID) -> requests.Response:
        """
        CancelPayroll

        Args:
            company_uid (UUID): The company uid
        Args:
            payroll_uid (UUID): The payroll uid
        Returns:
            requests.Response: The API response
        """
        endpoint = f"{self.endpoint}/{payroll_uid}"
        try:
            response = self.zenegy.delete(endpoint=endpoint)
            self.zenegy.raise_for_status_with_details(response)
            return response
        except Exception as e:
            raise Exception(f"Failed to delete payroll: {str(e)}")

    def delete_employee_payroll(self, payroll_uid: UUID,
                                      employee_payroll_uid: UUID) -> requests.Response:
        """
        DeleteEmployeePayrollAsync
        Args:
            payroll_uid (UUID): The payroll uid
        Args:
            employee_payroll_uid (UUID): The employee payroll uid
        Returns:
            requests.Response: The API response
        """
        endpoint_path = f"{self.endpoint}/{payroll_uid}/employees/{employee_payroll_uid}"
        try:
            response = self.zenegy.delete(endpoint=endpoint_path)
            self.zenegy.raise_for_status_with_details(response)
            return response
        except Exception as e:
            raise Exception(f"Failed to delete employee payroll: {str(e)}")
