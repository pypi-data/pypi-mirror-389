from .schemas.global_value_sets import GlobalValueSetsGet, GlobalValueSetCreate, GlobalValueSetUpdate, GlobalValueSetEmployeeAssignment, GlobalValueSetEmployeeAssignmentResponse, RemoveGlobalValuesFromSetRequest, GetAssignedEmployeesRequest, AssignedEmployeesGet, AddCompanyGlobalValueRequest, CompanyGlobalValuesGet
from typing import Tuple, Dict, Any, List
import pandas as pd
from brynq_sdk_functions import Functions
import requests
from uuid import UUID

class GlobalValueSets:
    """
    Handles all global value sets-related operations in Zenegy API
    """
    def __init__(self, zenegy):
        """
        Initialize the GlobalValueSets class.

        Args:
            zenegy: The Zenegy instance to use for API calls
        """
        self.zenegy = zenegy
        self.endpoint = f"api/companies/{self.zenegy.company_uid}/global-value-sets"

    def get(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        GetGlobalValueSetsPerCompanyAsync
        Returns:
            Tuple of (valid_data, invalid_data) DataFrames with global value sets information
        """
        try:
            content = self.zenegy.get(endpoint=self.endpoint)

            df = pd.json_normalize(
                content,
                sep='__'
            )
            if df.empty:
                return pd.DataFrame(), pd.DataFrame()

            # Validate against schema
            valid_data, invalid_data = Functions.validate_data(df, GlobalValueSetsGet)

            return valid_data, invalid_data
        except Exception as e:
            raise Exception(f"Failed to retrieve global value sets: {str(e)}") from e

    def get_by_id(self, global_value_set_uid: UUID) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        GetGlobalValueSetByIdAsync
        Args:
            global_value_set_uid (UUID): The global value set UID to retrieve
        Returns:
            Tuple of (valid_data, invalid_data) DataFrames with global value set information
        """
        try:
            endpoint = f"{self.endpoint}/{global_value_set_uid}"
            content = self.zenegy.get(endpoint=endpoint)

            # Normalize the data
            df = pd.json_normalize(
                [content],  # Wrap in list since it's a single object
                sep='__'
            )

            if df.empty:
                return pd.DataFrame(), pd.DataFrame()

            # Validate data using schema
            valid_data, invalid_data = Functions.validate_data(df, GlobalValueSetsGet)
            return valid_data, invalid_data
        except Exception as e:
            raise Exception(f"Failed to retrieve global value set by ID: {str(e)}") from e

    def get_assigned_employees(self, global_value_set_uid: UUID, filters: Dict[str, Any] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Get employees assigned to a global value set with optional filters.

        Args:
            global_value_set_uid (UUID): The global value set UID to get assigned employees for
            filters (Dict[str, Any], optional): Filter criteria for employees

        Returns:
            Tuple of (valid_data, invalid_data) DataFrames with assigned employee information
        """
        try:
            # Default filter if none provided
            if filters is None:
                filters = {"skip": 0, "take": 50}

            # Validate the filter data using Pydantic
            valid_filter = GetAssignedEmployeesRequest(**filters)
            req_body = valid_filter.model_dump(by_alias=True, mode='json', exclude_none=True)

            endpoint = f"{self.endpoint}/{global_value_set_uid}/assigned"
            response = self.zenegy.post(endpoint=endpoint, json=req_body)
            self.zenegy.raise_for_status_with_details(response)

            content = response.json()

            # Get data from response
            data = content.get("data", [])

            if not data:
                return pd.DataFrame(), pd.DataFrame()

            # Normalize the data with expanded department fields
            df = pd.json_normalize(
                data,
                sep='__'
            )

            if df.empty:
                return pd.DataFrame(), pd.DataFrame()

            # Validate data using schema
            valid_data, invalid_data = Functions.validate_data(df, AssignedEmployeesGet)
            return valid_data, invalid_data

        except Exception as e:
            raise Exception(f"Failed to get assigned employees for global value set: {str(e)}") from e

    def create(self, data: Dict[str, Any]) -> requests.Response:
        """
        Create a new global value set.

        Args:
            data (Dict[str, Any]): The global value set data to create

        Returns:
            requests.Response: The API response
        """
        try:
            # Convert flat dictionary to nested structure based on Pydantic model
            nested_data = Functions.flat_dict_to_nested_dict(data, GlobalValueSetCreate)

            valid_data = GlobalValueSetCreate(**nested_data)
            req_body = valid_data.model_dump(by_alias=True, mode='json', exclude_none=True)

            response = self.zenegy.post(endpoint=self.endpoint, json=req_body)
            self.zenegy.raise_for_status_with_details(response)
            return response

        except Exception as e:
            raise Exception(f"Failed to create global value set: {str(e)}") from e

    def delete(self, global_value_set_uid: UUID) -> requests.Response:
        """
        Delete a global value set by UID.

        Args:
            global_value_set_uid (UUID): The global value set UID to delete

        Returns:
            requests.Response: The API response
        """
        try:
            endpoint = f"{self.endpoint}/{global_value_set_uid}"

            response = self.zenegy.delete(endpoint=endpoint)
            self.zenegy.raise_for_status_with_details(response)
            return response

        except Exception as e:
            raise Exception(f"Failed to delete global value set: {str(e)}") from e

    def update(self, global_value_set_uid: UUID, data: Dict[str, Any]) -> requests.Response:
        """
        Update a global value set by UID.

        Args:
            global_value_set_uid (UUID): The global value set UID to update
            data (Dict[str, Any]): The global value set data to update

        Returns:
            requests.Response: The API response
        """
        try:
            # Convert flat dictionary to nested structure based on Pydantic model
            nested_data = Functions.flat_dict_to_nested_dict(data, GlobalValueSetUpdate)

            valid_data = GlobalValueSetUpdate(**nested_data)
            req_body = valid_data.model_dump(by_alias=True, mode='json', exclude_none=True)
            endpoint = f"{self.endpoint}/{global_value_set_uid}"

            response = self.zenegy.patch(endpoint=endpoint, json=req_body)
            self.zenegy.raise_for_status_with_details(response)
            return response

        except Exception as e:
            raise Exception(f"Failed to update global value set: {str(e)}") from e

    def manage_employees(self, global_value_set_uid: UUID, data: Dict[str, Any]) -> requests.Response:
        """
        Manage employee assignments for a global value set (add and/or remove employees).

        Args:
            global_value_set_uid (UUID): The global value set UID to manage employees for
            data (Dict[str, Any]): The employee assignment data (add_employees and/or remove_employees)

        Returns:
            requests.Response: The API response with assignment results
        """
        try:
            # Convert flat dictionary to nested structure based on Pydantic model
            nested_data = Functions.flat_dict_to_nested_dict(data, GlobalValueSetEmployeeAssignment)

            valid_data = GlobalValueSetEmployeeAssignment(**nested_data)
            req_body = valid_data.model_dump(by_alias=True, mode='json', exclude_none=True)
            endpoint = f"{self.endpoint}/{global_value_set_uid}/employees"

            response = self.zenegy.put(endpoint=endpoint, json=req_body)
            self.zenegy.raise_for_status_with_details(response)
            return response

        except Exception as e:
            raise Exception(f"Failed to manage employees for global value set: {str(e)}") from e

    def assign_to_employees(self, global_value_set_uid: UUID, employee_uids: List[str]) -> requests.Response:
        """
        Assign a global value set to specified employees.

        Args:
            global_value_set_uid (UUID): The global value set UID to assign
            employee_uids (List[str]): List of employee UIDs to assign the global value set to

        Returns:
            requests.Response: The API response (204 No Content on success)
        """
        try:
            # API expects a simple Array[string] as body
            endpoint = f"{self.endpoint}/{global_value_set_uid}/assign"
            req_body = employee_uids

            response = self.zenegy.post(endpoint=endpoint, json=employee_uids)
            self.zenegy.raise_for_status_with_details(response)
            return response

        except Exception as e:
            raise Exception(f"Failed to assign global value set to employees: {str(e)}") from e

    def unassign_from_employees(self, global_value_set_uid: UUID, employee_uids: List[str]) -> requests.Response:
        """
        Unassign employees from a global value set.

        Args:
            global_value_set_uid (UUID): The global value set UID to unassign employees from
            employee_uids (List[str]): List of employee UIDs to unassign

        Returns:
            requests.Response: The API response
        """
        try:
            # API expects a simple Array[string] as body
            endpoint = f"{self.endpoint}/{global_value_set_uid}/employees/delete"
            req_body = employee_uids

            response = self.zenegy.post(endpoint=endpoint, json=employee_uids)
            self.zenegy.raise_for_status_with_details(response)
            return response

        except Exception as e:
            raise Exception(f"Failed to unassign employees from global value set: {str(e)}") from e
