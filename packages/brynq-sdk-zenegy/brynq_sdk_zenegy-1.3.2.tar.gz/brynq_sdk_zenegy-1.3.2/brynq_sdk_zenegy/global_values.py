from .schemas.global_values import (GlobalValuesGet, CompanyGlobalValueCreate, CompanyGlobalValueUpdate, GlobalValueAssign, AssignedGlobalValuesGet, GetAssignedEmployeesToGlobalValueAsyncRequest, AssignedEmployeesToGlobalValueGet)
from typing import Tuple, Dict, Any, List
import pandas as pd
from brynq_sdk_functions import Functions
import requests
from uuid import UUID

class GlobalValues:
    """
    Handles all globalvalues-related operations in Zenegy API
    """
    def __init__(self, zenegy):
        """
        Initialize the GlobalValues class.

        Args:
            zenegy: The Zenegy instance to use for API calls
        """
        self.zenegy = zenegy
        self.endpoint = f"api/companies/{self.zenegy.company_uid}/global-values"

    def get(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        GetGlobalValuesPerCompanyAsync
        Returns:
            Tuple of (valid_data, invalid_data) DataFrames with global values information
        """
        try:
            # Make the API request and get raw response
            content = self.zenegy.get(endpoint=self.endpoint)

            # Normalize the data with expanded effectiveFrom and effectiveTo
            df = pd.json_normalize(
                content,
                sep='__'
            )

            if df.empty:
                return pd.DataFrame(), pd.DataFrame()

            # Validate data using schema
            valid_data, invalid_data = Functions.validate_data(df, GlobalValuesGet)
            return valid_data, invalid_data

        except Exception as e:
            raise Exception(f"Failed to retrieve global values: {str(e)}") from e

    def create(self, data: Dict[str, Any]) -> requests.Response:
        """
        CreateGlobalValueAsync
        Args:
            data (Dict[str, Any]): The global value data to create
        Returns:
            requests.Response: The API response
        """
        try:
            # Convert flat dictionary to nested structure based on Pydantic model
            nested_data = Functions.flat_dict_to_nested_dict(data, CompanyGlobalValueCreate)

            # Validate the data using Pydantic
            valid_data = CompanyGlobalValueCreate(**nested_data)
            req_body = valid_data.model_dump(by_alias=True, mode='json', exclude_none=True)

            response = self.zenegy.post(endpoint=self.endpoint, json=req_body)
            self.zenegy.raise_for_status_with_details(response)
            return response

        except Exception as e:
            raise Exception(f"Failed to create global value: {str(e)}") from e

    def get_by_id(self, global_value_uid: UUID) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        GetGlobalValueByIdAsync
        Args:
            global_value_uid (UUID): The global value UID to retrieve
        Returns:
            Tuple of (valid_data, invalid_data) DataFrames with global value information
        """
        try:
            endpoint = f"{self.endpoint}/{global_value_uid}"
            content = self.zenegy.get(endpoint=endpoint)

            # Normalize the data with expanded effectiveFrom and effectiveTo
            df = pd.json_normalize(
                [content],  # Wrap in list since it's a single object
                sep='__'
            )

            if df.empty:
                return pd.DataFrame(), pd.DataFrame()

            # Validate data using schema
            valid_data, invalid_data = Functions.validate_data(df, GlobalValuesGet)
            return valid_data, invalid_data
        except Exception as e:
            raise Exception(f"Failed to retrieve global value by ID: {str(e)}") from e

    def get_assigned_global_values(self, employee_uid: UUID) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        GetAssignedGlobalValuesAsync
        Args:
            employee_uid (UUID): The employee UID to get assigned global values for
        Returns:
            Tuple of (valid_data, invalid_data) DataFrames with assigned global values information
        """
        try:
            endpoint = f"{self.endpoint}/assignedGlobalValues/{employee_uid}"
            content = self.zenegy.get(endpoint=endpoint)

            # Normalize the data with expanded companyGlobalValueReferenceUidsPairs
            df = pd.json_normalize(
                content,
                record_path='companyGlobalValueReferenceUidsPairs',
                meta=['type', 'isAvailableInCompany', 'isEmployeeAssigned'],
                record_prefix='companyGlobalValueReferenceUidsPairs__',
                sep='__'
            )

            if df.empty:
                return pd.DataFrame(), pd.DataFrame()

            # Validate data using schema
            valid_data, invalid_data = Functions.validate_data(df, AssignedGlobalValuesGet)
            return valid_data, invalid_data
        except Exception as e:
            raise Exception(f"Failed to retrieve assigned global values for employee: {str(e)}") from e

    def get_assigned_employees(self, global_value_uid: UUID, filters: Dict[str, Any] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Get employees assigned to a global value with optional filters.

        Args:
            global_value_uid (UUID): The global value UID to get assigned employees for
            filters (Dict[str, Any], optional): Filter criteria for employees

        Returns:
            Tuple of (valid_data, invalid_data) DataFrames with assigned employee information
        """
        try:
            if filters is None:
                filters = {"skip": 0, "take": 50}

            # Validate the filter data using Pydantic
            valid_filter = GetAssignedEmployeesToGlobalValueAsyncRequest(**filters)
            req_body = valid_filter.model_dump(by_alias=True, mode='json', exclude_none=True)

            endpoint = f"{self.endpoint}/{global_value_uid}/assigned"
            response = self.zenegy.post(endpoint=endpoint, json=req_body)
            self.zenegy.raise_for_status_with_details(response)

            content = response.json()
            data = content.get("data", [])

            if not data:
                return pd.DataFrame(), pd.DataFrame()

            # Normalize the data with expanded department and user fields
            df = pd.json_normalize(data, sep='__')

            if df.empty:
                return pd.DataFrame(), pd.DataFrame()

            # Validate data using schema
            valid_data, invalid_data = Functions.validate_data(df, AssignedEmployeesToGlobalValueGet)
            return valid_data, invalid_data

        except Exception as e:
            raise Exception(f"Failed to get assigned employees for global value: {str(e)}") from e

    def update(self, global_value_uid: UUID, data: Dict[str, Any]) -> requests.Response:
        """
        Update a global value by UID.

        Args:
            global_value_uid (UUID): The global value UID to update
            data (Dict[str, Any]): The global value data to update

        Returns:
            requests.Response: The API response
        """
        try:
            # Convert flat dictionary to nested structure based on Pydantic model
            nested_data = Functions.flat_dict_to_nested_dict(data, CompanyGlobalValueUpdate)

            # Validate the data using Pydantic
            valid_data = CompanyGlobalValueUpdate(**nested_data)
            req_body = valid_data.model_dump(by_alias=True, mode='json', exclude_none=True)
            endpoint = f"{self.endpoint}/{global_value_uid}"

            response = self.zenegy.patch(endpoint=endpoint, json=req_body)
            self.zenegy.raise_for_status_with_details(response)
            return response

        except Exception as e:
            raise Exception(f"Failed to update global value: {str(e)}") from e

    def assign_to_employees(self, global_value_uid: UUID, data: Dict[str, Any]) -> requests.Response:
        """
        Assign a global value to multiple employees with optional settings.

        Args:
            global_value_uid (UUID): The global value UID to assign
            data (Dict[str, Any]): The assignment data with employee UIDs and optional settings

        Returns:
            requests.Response: The API response (204 No Content on success)
        """
        try:
            # Convert flat dictionary to nested structure based on Pydantic model
            nested_data = Functions.flat_dict_to_nested_dict(data, GlobalValueAssign)

            # Validate the data using Pydantic
            valid_data = GlobalValueAssign(**nested_data)
            req_body = valid_data.model_dump(by_alias=True, mode='json', exclude_none=True)
            endpoint = f"{self.endpoint}/{global_value_uid}/assign"

            response = self.zenegy.post(endpoint=endpoint, json=req_body)
            self.zenegy.raise_for_status_with_details(response)
            return response

        except Exception as e:
            raise Exception(f"Failed to assign global value to employees: {str(e)}") from e

    def unassign_from_employees(self, global_value_uid: UUID, employee_uids: List[str]) -> requests.Response:
        """
        Unassign a global value from multiple employees.

        Args:
            global_value_uid (UUID): The global value UID to unassign
            employee_uids (List[str]): List of employee UIDs to unassign from

        Returns:
            requests.Response: The API response (204 No Content on success)
        """
        try:
            # API expects a simple Array[string] as body
            endpoint = f"{self.endpoint}/{global_value_uid}/unassign"
            req_body = employee_uids

            response = self.zenegy.post(endpoint=endpoint, json=employee_uids)
            self.zenegy.raise_for_status_with_details(response)
            return response

        except Exception as e:
            raise Exception(f"Failed to unassign global value from employees: {str(e)}") from e

    def delete(self, global_value_uid: UUID) -> requests.Response:
        """
        Delete a global value.

        Args:
            global_value_uid (UUID): The global value UID to delete

        Returns:
            requests.Response: The API response (204 No Content on success)
        """
        try:
            endpoint = f"{self.endpoint}/{global_value_uid}"

            response = self.zenegy.delete(endpoint=endpoint)
            self.zenegy.raise_for_status_with_details(response)
            return response

        except Exception as e:
            raise Exception(f"Failed to delete global value: {str(e)}") from e
