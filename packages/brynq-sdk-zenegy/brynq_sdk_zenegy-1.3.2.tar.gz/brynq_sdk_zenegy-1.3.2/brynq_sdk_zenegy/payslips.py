from .schemas.payslips import PayslipsGet
from uuid import UUID
from typing import Tuple
import pandas as pd
from brynq_sdk_functions import Functions

class Payslips:
    """
    Handles all payslip-related operations in Zenegy API
    """

    def __init__(self, zenegy):
        """
        Initialize the Payslips class.

        Args:
            zenegy: The Zenegy instance to use for API calls
        """
        self.zenegy = zenegy

    def get(self, employee_uid: UUID) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        GetEmployeePayslips
        Args:
            employee_uid (UUID): The employee uid
        Returns:
            Tuple of (valid_data, invalid_data) DataFrames
        """
        try:
            endpoint = f"api/companies/{self.zenegy.company_uid}/employees/{employee_uid}/payslips"
            content = self.zenegy.get(endpoint=endpoint)

            # Normalize the response (data field contains the list)
            df = pd.json_normalize(content.get("data", []), sep='__')
            if df.empty:
                return pd.DataFrame(), pd.DataFrame()

            # Validate against schema
            valid_data, invalid_data = Functions.validate_data(df, PayslipsGet)

            return valid_data, invalid_data
        except Exception as e:
            raise Exception(f"Failed to retrieve payslips: {str(e)}") from e
