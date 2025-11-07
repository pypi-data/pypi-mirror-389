from .schemas.supplements_and_deductions_rates import SupplementRatesGet, SupplementRegistrationsGet
from uuid import UUID
from typing import Dict, Any, List, Tuple
import pandas as pd
from brynq_sdk_functions import Functions

class SupplementsAndDeductionsRates:
    """
    Handles all companysupplementsanddeductionsrates-related operations in Zenegy API
    """
    def __init__(self, zenegy):
        """
        Initialize the SupplementsAndDeductionsRates class.

        Args:
            zenegy: The Zenegy instance to use for API calls
        """
        self.zenegy = zenegy
        self.endpoint = f"api/companies/{self.zenegy.company_uid}/supplementsanddeductions/rates"

    def get(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        GetSupplementRatesListDtoAsync
        Returns:
            Tuple of (valid_data, invalid_data) DataFrames
        """
        endpoint = f"{self.endpoint}/list"
        try:
            content = self.zenegy.get(endpoint=endpoint)

            # Get data from response
            data = content.get("data", [])
            if data:
                # Normalize the data
                df = pd.json_normalize(
                    data,
                    sep='__'
                )
                # Validate data using schema
                valid_data, invalid_data = Functions.validate_data(df, SupplementRatesGet)
                return valid_data, invalid_data
            return pd.DataFrame(), pd.DataFrame()
        except Exception as e:
            raise Exception(f"Failed to retrieve supplement rates: {str(e)}") from e

    def get_registrations(self, employee_uid: UUID) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        GetRegistrationDtoQueryAsync
        Args:
            employee_uid (UUID): The employee uid
        Returns:
            Tuple of (valid_data, invalid_data) DataFrames
        """
        endpoint = f"api/companies/{self.zenegy.company_uid}/employees/{employee_uid}/supplementsanddeductions/registrations"
        try:
            content = self.zenegy.get(endpoint=endpoint)

            # Get data from response
            data = content.get("data", [])
            if data:
                # Normalize the data with nested objects
                df = pd.json_normalize(
                    data,
                    sep='__'
                )
                # Validate data using schema
                valid_data, invalid_data = Functions.validate_data(df, SupplementRegistrationsGet)
                return valid_data, invalid_data
            return pd.DataFrame(), pd.DataFrame()
        except Exception as e:
            raise Exception(f"Failed to retrieve supplement registrations: {str(e)}") from e
