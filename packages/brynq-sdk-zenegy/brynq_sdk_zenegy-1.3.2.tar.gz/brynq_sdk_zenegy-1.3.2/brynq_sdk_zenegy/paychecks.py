import requests
from uuid import UUID
from brynq_sdk_functions import Functions
from .schemas.employee_pay_checks import (PaycheckUpdate,
                                          PaycheckCreate,
                                          PayChecksGet)
from typing import Dict, Any, Tuple
import pandas as pd
from pydantic import ValidationError


class PayChecks:
    """
    Handles all Employee Pay Check related operations in Zenegy API
    """
    def __init__(self, zenegy):
        """
        Initialize the Employeepaychecks class.

        Args:
            zenegy: The Zenegy instance to use for API calls
        """
        self.zenegy = zenegy
        self.endpoint = f"api/companies/{self.zenegy.company_uid}/paychecks/bulk"

    def get(self, employee_uid: UUID) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        GetPayCheckBasesAsync
        Args:
            employee_uid (UUID): The employee uid
        Returns:
            Tuple of (valid_data, invalid_data) DataFrames
        """
        try:
            endpoint = f"api/companies/{self.zenegy.company_uid}/employees/{employee_uid}/paychecks"
            content = self.zenegy.get(endpoint=endpoint)

            # Normalize the response (direct list of dicts with nested objects)
            df = pd.json_normalize(content, sep='__')
            if df.empty:
                return pd.DataFrame(), pd.DataFrame()
            # Validate against schema
            valid_data, invalid_data = Functions.validate_data(df, PayChecksGet)

            return valid_data, invalid_data
        except Exception as e:
            raise Exception(f"Failed to retrieve pay checks: {str(e)}") from e

    def create(self, employee_uid: UUID, data: Dict[str, Any]) -> requests.Response:
        """
        PostPayChecksAsync
        Args:
            employee_uid (UUID): The employee uid
            data (Dict[str, Any]): The data to create the pay check
        Returns:
            requests.Response: The response from the API
        Raises:
            ValidationError: If the data is invalid
            Exception: If there is an error in the API call
        """
        url = f"{self.zenegy.base_url}/api/companies/{self.zenegy.company_uid}/employees/{employee_uid}/paychecks"

        try:
            # Validate data using Pydantic schema
            validated_data = PaycheckCreate(**data)
            req_body = validated_data.model_dump(by_alias=True,mode='json')

            endpoint = f"api/companies/{self.zenegy.company_uid}/employees/{employee_uid}/paychecks"
            response = self.zenegy.post(endpoint=endpoint, json=req_body)
            self.zenegy.raise_for_status_with_details(response)
            return response
        except ValidationError as e:
            raise ValidationError(f"Invalid data: {e.errors()}")
        except Exception as e:
            raise Exception(f"Error creating pay check: {str(e)}")

    def update(self, employee_uid: UUID, paycheck_uid: UUID, data: Dict[str, Any]) -> requests.Response:
        """
        UpdatePayCheckPerEmployeeAsync
        Args:
            employee_uid (UUID): The employee uid
            paycheck_uid (UUID): The pay check uid
            data (Dict[str, Any]): The data to update the pay check
        Returns:
            requests.Response: The response from the API
        Raises:
            ValidationError: If the data is invalid
            Exception: If there is an error in the API call
        """
        try:
            # Validate data using Pydantic schema
            validated_data = PaycheckUpdate(**data)
            req_body = validated_data.model_dump(by_alias=True,mode="json")
            endpoint = f"api/companies/{self.zenegy.company_uid}/employees/{employee_uid}/paychecks"
            response = self.zenegy.post(endpoint=endpoint, json=req_body)
            self.zenegy.raise_for_status_with_details(response)
            return response
        except ValidationError as e:
            raise ValidationError(f"Invalid data: {e.errors()}")
        except Exception as e:
            raise Exception(f"Error updating pay check: {str(e)}")

    def delete(self, employee_uid: UUID, pay_check_uid: UUID) -> requests.Response:
        """
        DeletePayCheckPerEmployee
        Args:
            employee_uid (UUID): The employee uid
        Args:
            pay_check_uid (UUID): The pay check uid
        Returns:
            requests.Response: The API response
        """
        endpoint = f"api/companies/{self.zenegy.company_uid}/employees/{employee_uid}/paychecks/{pay_check_uid}"
        try:
            response = self.zenegy.delete(endpoint=endpoint)
            self.zenegy.raise_for_status_with_details(response)
            return response
        except Exception as e:
            raise Exception(f"Failed to delete pay check: {str(e)}")
