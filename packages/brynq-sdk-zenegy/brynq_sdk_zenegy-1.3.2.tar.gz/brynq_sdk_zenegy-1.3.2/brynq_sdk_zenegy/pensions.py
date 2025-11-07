import requests
from uuid import UUID
from .schemas.employee_pensions import (EmployeePensionCreate,
                                        PensionGet)
from brynq_sdk_functions import Functions
from typing import Dict, Any, List, Tuple
import pandas as pd


class Pensions:
    """
    Handles all employeepensions-related operations in Zenegy API
    """
    def __init__(self, zenegy):
        """
        Initialize the Employeepensions class.

        Args:
            zenegy: The Zenegy instance to use for API calls
        """
        self.zenegy = zenegy
        self.endpoint = f"api/companies/{self.zenegy.company_uid}/pensions/bulk"

    def get(self, employee_uid: UUID) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        GetEmployeePensionsAsync
        Args:
            employee_uid (UUID): The employee uid
        Returns:
            Tuple of (valid_data, invalid_data) DataFrames
        """
        try:
            endpoint = f"api/companies/{self.zenegy.company_uid}/employees/{employee_uid}/pensions"
            content = self.zenegy.get(endpoint=endpoint)

            # Get data from response
            data = content.get("data", [])
            if data:
                # Normalize the data
                df = pd.json_normalize(
                    data,
                    sep='__'
                )
                if df.empty:
                    return pd.DataFrame(), pd.DataFrame()
                # Validate data using schema
                valid_data, invalid_data = Functions.validate_data(df, PensionGet)
                return valid_data, invalid_data
            return pd.DataFrame(), pd.DataFrame()
        except Exception as e:
            raise Exception(f"Failed to retrieve pensions: {str(e)}") from e

    def get_by_id(self, employee_uid: UUID, employee_pension_uid: UUID) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        GetEmployeePensionAsync
        Args:
            employee_uid (UUID): The employee uid
            employee_pension_uid (UUID): The employee pension uid
        Returns:
            Tuple of (valid_data, invalid_data) DataFrames
        """
        try:
            endpoint = f"api/companies/{self.zenegy.company_uid}/employees/{employee_uid}/pensions/{employee_pension_uid}"
            content = self.zenegy.get(endpoint=endpoint)

            # Normalize the data (content is already a dict)
            df = pd.json_normalize(
                [content],  # Wrap single object in list for normalization
                sep='__'
            )
            if df.empty:
                return pd.DataFrame(), pd.DataFrame()

            # Validate data using schema
            valid_data, invalid_data = Functions.validate_data(df, PensionGet)
            return valid_data, invalid_data
        except Exception as e:
            raise Exception(f"Failed to retrieve pension by ID: {str(e)}") from e

    def create(self, employee_uid: UUID, data: Dict[str, Any]) -> requests.Response:
        """
        InsertEmployeePensionAsync
        Args:
            employee_uid (UUID): The employee uid
        Args:
            data (Dict[str, Any]): The data
        Returns:
            requests.Response: The API response
        """
        endpoint = f"api/companies/{self.zenegy.company_uid}/employees/{employee_uid}/pensions"
        # Validate the data using Pydantic
        try:
            valid_data = EmployeePensionCreate(**data)
            if valid_data:
                req_body = valid_data.model_dump(by_alias=True, exclude_none=True,mode="json")
                response = self.zenegy.post(endpoint=endpoint, json=req_body)
                self.zenegy.raise_for_status_with_details(response)
                return response
        except Exception as e:
            raise Exception(f"Error creating pension data: {str(e)}")

    def delete(self, employee_uid: UUID, employee_pension_uid: UUID) -> requests.Response:
        """
        DeleteEmployeePensionAsync
        Args:
            employee_uid (UUID): The employee uid
        Args:
            employee_pension_uid (UUID): The employee pension uid
        Returns:
            requests.Response: The API response
        """
        endpoint = f"api/companies/{self.zenegy.company_uid}/employees/{employee_uid}/pensions/{employee_pension_uid}"
        try:
            response = self.zenegy.delete(endpoint=endpoint)
            self.zenegy.raise_for_status_with_details(response)
            return response
        except Exception as e:
            raise Exception(f"Failed to delete pension: {str(e)}")
