from uuid import UUID
from .schemas.company_departments import DepartmentsGet
from typing import Tuple
import pandas as pd
from brynq_sdk_functions import Functions


class CompanyDepartments:
    """
    Handles all companydepartment-related operations in Zenegy API
    """

    def __init__(self, zenegy):
        """
        Initialize the CompanyDepartments class.

        Args:
            zenegy: The Zenegy instance to use for API calls
        """
        self.zenegy = zenegy
        self.endpoint = f"api/companies/{self.zenegy.company_uid}/departments"

    def get(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        GetCompanyDepartmentsAsync
        Returns:
            Tuple of (valid_data, invalid_data) DataFrames with department information
        """
        try:
            # Make the API request and get raw response
            content = self.zenegy.get(endpoint=self.endpoint)

            # Get data from response
            data = content.get("data", [])

            df = pd.json_normalize(
                data,
                sep='__'
            )

            if df.empty:
                return pd.DataFrame(), pd.DataFrame()

            # Validate data using schema
            valid_data, invalid_data = Functions.validate_data(df, DepartmentsGet)
            return valid_data, invalid_data

        except Exception as e:
            raise Exception(f"Failed to retrieve departments: {str(e)}") from e

    def get_by_id(self, company_department_uid: UUID) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        GetCompanyDepartment
        Args:
            company_department_uid (UUID): The company department uid
        Returns:
            Tuple of (valid_data, invalid_data) DataFrames with department information
        """
        try:
            endpoint = f"{self.endpoint}/{company_department_uid}"
            # Make the API request and get raw response
            content = self.zenegy.get(endpoint=endpoint)

            df = pd.json_normalize(
                content,
                sep='__'
            )

            if df.empty:
                return pd.DataFrame(), pd.DataFrame()

            # Validate data using schema
            valid_data, invalid_data = Functions.validate_data(df, DepartmentsGet)
            return valid_data, invalid_data

        except Exception as e:
            raise Exception(f"Failed to retrieve department by ID: {str(e)}") from e
