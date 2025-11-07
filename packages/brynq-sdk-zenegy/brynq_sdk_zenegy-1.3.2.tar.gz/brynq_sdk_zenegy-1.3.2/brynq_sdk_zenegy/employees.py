# Generated endpoint class for tag: Employees
import pandas as pd
import requests
from uuid import UUID
from brynq_sdk_functions import Functions

from .schemas.employees import (EmployeeCreate,
                                EmployeeUpdate,
                                EmployeesGet,
                                EmployeesGetById,
                                EmployeeEmploymentDataUpdate,
                                EmployeeEmploymentUpdate,
                                EmployeeAdditionalUpdate,
                                StartSaldo,
                                EmployeePatch)
from .paychecks import PayChecks
from .pensions import Pensions
from typing import Dict, Any, Tuple, List


class Employees:
    """
    Handles all employees-related operations in Zenegy API
    """

    def __init__(self, zenegy):
        """
        Initialize the Employees class.

        Args:
            zenegy: The Zenegy instance to use for API calls
        """
        self.zenegy = zenegy
        self.endpoint = f"api/companies/{self.zenegy.company_uid}/employees"

        # Initialize paychecks and pensions
        self.paychecks = PayChecks(zenegy)
        self.pensions = Pensions(zenegy)

    def get(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        GetEmployeeBasesAsync
        Returns:
            Tuple of (valid_data, invalid_data) DataFrames with employee information
        """
        try:
            # Make the API request and get raw response
            content = self.zenegy.get(endpoint=self.endpoint)

            # Get data from response
            data = content.get("data", [])

            # Normalize the data
            df = pd.json_normalize(
                data,
                sep='__'
            )

            if df.empty:
                return pd.DataFrame(), pd.DataFrame()

            # Validate data using schema
            valid_data, invalid_data = Functions.validate_data(df, EmployeesGet)
            return valid_data, invalid_data

        except Exception as e:
            raise Exception(f"Failed to retrieve employees: {str(e)}") from e

    def get_by_id(self, employee_uid: UUID) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        GetEmployeeAsync

        Args:
            employee_uid (UUID): The employee uid
        Returns:
            Tuple of (valid_data, invalid_data) DataFrames with employee information
        """
        endpoint = f"{self.endpoint}/{employee_uid}"
        try:
            # Make the API request and get raw response
            content = self.zenegy.get(endpoint=endpoint)

            # Normalize the data (content is already a dict)
            df = pd.json_normalize(
                [content],  # Wrap single object in list for normalization
                sep='__'
            )

            if df.empty:
                return pd.DataFrame(), pd.DataFrame()

            # Validate data using detailed by-id schema
            valid_data, invalid_data = Functions.validate_data(df, EmployeesGetById)
            return valid_data, invalid_data

        except Exception as e:
            raise Exception(f"Failed to retrieve employee by ID: {str(e)}") from e

    def create(self, data: Dict[str, Any]) -> requests.Response:
        """
        PostEmployeeAsync
        Args:
            data (Dict[str, Any]): The data
        Returns:
            requests.Response: The API response
        """
        try:
            req_data = EmployeeCreate(**data)
            req_body = req_data.model_dump(by_alias=True, mode='json', exclude_none=True)
            response = self.zenegy.post(endpoint=self.endpoint.lstrip('/'), json=req_body)
            patch_body = self.create_update_body(data)

            # if the patch body is bigger than the request body, that means that there are fields left for the patch:
            # Count actual fields at the lowest level for proper comparison
            patch_field_count = self._count_nested_fields(patch_body)
            if patch_field_count > len(req_body):
                response_data = response.json()
                if isinstance(response_data, str):
                    uid = response_data
                elif isinstance(response_data, dict):
                    uid = response_data['data']['uid']
                patch_endpoint = f"{self.endpoint}/{uid}"

                response = self.zenegy.put(
                    endpoint=patch_endpoint.lstrip('/'),
                    json=patch_body
                )
                self.zenegy.raise_for_status_with_details(response)
                return response

            self.zenegy.raise_for_status_with_details(response)
            return response
        except Exception as e:
            raise Exception(f"Failed to create employee: {str(e)}")

    def upsert(self, data: Dict[str, Any]) -> requests.Response:
        """
        UpsertEmployeeAsync

        Args:
            data (Dict[str, Any]): The data to update

        Returns:
            requests.Response: The API response
        """
        endpoint = f"api/companies/{self.zenegy.company_uid}/employees"
        try:
            req_body = self.create_update_body(data)
            uid = data.get('employee_uid')
            endpoint = f"{self.endpoint}/{uid}".lstrip('/')
            response = self.zenegy.put(endpoint=endpoint, json=req_body)
            self.zenegy.raise_for_status_with_details(response)
            return response
        except Exception as e:
            raise Exception(f"Failed to update employee: {str(e)}")

    def delete(self, employee_uid: UUID) -> requests.Response:
        """
        DeleteEmployee

        Args:
            employee_uid (UUID): The employee uid
        Returns:
            requests.Response: The API response
        """
        endpoint = f"{self.endpoint}/{employee_uid}"
        try:
            response = self.zenegy.delete(endpoint=endpoint)
            self.zenegy.raise_for_status_with_details(response)
            return response
        except Exception as e:
            raise Exception(f"Failed to delete employee: {str(e)}")

    def create_update_body(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create the update body for the employee.
        """
        # There is strange logic in Zenegy that you can create an employee with only a limited set of fields. Afterward, you have to patch the employee with the rest of the fields.
        update_data = EmployeeUpdate(**data)
        body = update_data.model_dump(by_alias=True, mode='json', exclude_none=True)


        #-- START TODO: This is a temporary solution to handle the additional fields for the contract related fields in mft.
        #additional fields for contract related fields
        schema_map = {
            "startSaldo": StartSaldo,
            "employmentData": EmployeeEmploymentDataUpdate,
            "employeeEmployment": EmployeeEmploymentUpdate,
            "employeeAditional": EmployeeAdditionalUpdate
        }

        result_body = {"updateEmployeeBase": body}

        # Initialize required top-level fields with empty objects (API requires these to always be present)
        result_body["startSaldo"] = {} # can be passed empty
        result_body["employeeEmployment"] = {}
        result_body["employeeAditional"] = {"monthlySalaryFixedBase": 0}

        # Check if any fields from data match schema fields, and serialize accordingly
        for schema_name, schema_class in schema_map.items():
            schema_fields = schema_class.model_fields.keys()
            # Find matching keys between data and schema fields
            matching_data = {k: v for k, v in data.items() if k in schema_fields}

            # Skip if employee_number is the only field present
            if matching_data:  # and not (len(matching_data) == 1 and 'employee_number' in matching_data):
                # Serialize the matching data using the schema
                schema_instance = schema_class(**matching_data)
                serialized_data = schema_instance.model_dump(by_alias=True, mode='json', exclude_none=True)

                # startSaldo appears both inside updateEmployeeBase and at top level
                if schema_name == "startSaldo":
                    result_body["updateEmployeeBase"][schema_name] = serialized_data
                    result_body[schema_name] = serialized_data
                # employmentData appears inside updateEmployeeBase
                elif schema_name == "employmentData":
                    result_body["updateEmployeeBase"][schema_name] = serialized_data
                # employeeEmployment and employeeAditional appear at top level
                else:
                    result_body[schema_name] = serialized_data
        #--END TODO
        return result_body

    def _count_nested_fields(self, data: Dict[str, Any]) -> int:
        """
        Count the actual fields at the lowest level of a nested dictionary.
        https://www.google.com/search?client=firefox-b-d&sca_esv=4acce884baa46368&sxsrf=AE3TifPbAKp8zW8Gczemzqd3WYBgKrcwlg:1761129017606&q=recursion&spell=1&sa=X&ved=2ahUKEwja3v3rzLeQAxUwwAIHHZJVKZUQBSgAegQIFhAB

        Args:
            data: Dictionary that may contain nested dictionaries

        Returns:
            int: Total count of fields at the lowest level
        """
        count = 0
        for value in data.values():
            if isinstance(value, dict):
                count += self._count_nested_fields(value)
            else:
                count += 1
        return count

    def patch(self, employee_uid: UUID, data: Dict[str, Any], op: str = "replace") -> requests.Response:
        """
        PatchEmployee

        Single entry point for patching employees using a flat data dictionary.
        Flat keys may include prefixes for nested fields using a single underscore '_',
        e.g., 'start_saldo_start_g_days', 'language_name'. All generated operations
        are sent in ONE PATCH request as a JSON array per endpoint capability.

        Args:
            employee_uid (UUID): The employee uid
            data (Dict[str, Any]): Flat dictionary with EmployeeUpdate fields (supports '_' prefix nesting in keys)
            op (str): Operation type; defaults to "replace"

        Returns:
            requests.Response: Single response from the batch PATCH request
        """
        try:
            if not op:
                raise ValueError("Patch operation 'op' must be provided")

            operations = self.build_patch_operations(data=data, op=op)
            endpoint = f"{self.endpoint}/{employee_uid}".lstrip('/')
            response = self.zenegy.patch(endpoint=endpoint, json=operations)
            self.zenegy.raise_for_status_with_details(response)
            return response
        except Exception as e:
            raise Exception(f"Failed to patch employee: {str(e)}")


    def build_patch_operations(self, data: Dict[str, Any], op: str = "replace") -> List[Dict[str, Any]]:
        """
        Build JSON Patch operations from a flat employee data dictionary using
        the EmployeePatch flat schema (aliases map directly to JSON Patch paths).

        Args:
            data (Dict[str, Any]): Flat data with pythonic keys (e.g., name, email, start_g_days)
            op (str): JSON Patch op. Defaults to "replace".

        Returns:
            List[Dict[str, Any]]: JSON Patch operations
        """
        if not isinstance(data, dict):
            raise ValueError("data must be a dictionary")
        if not op:
            raise ValueError("Patch operation 'op' must be provided")

        # Validate against flat schema and dump using alias names
        validated = EmployeePatch(**data)
        alias_dump: Dict[str, Any] = validated.model_dump(by_alias=True, mode='json', exclude_none=True, exclude_unset=True)

        operations: List[Dict[str, Any]] = []
        for alias_key, value in alias_dump.items():
            operations.append({
                "op": op,
                "path": f"/{alias_key}",
                "value": value,
            })
        return operations
