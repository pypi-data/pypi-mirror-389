from .schemas.absences import (CreateAbsenceRequest,
                               UpdateAbsenceRequest,
                               AbsenceGet)
import requests
from uuid import UUID
from brynq_sdk_functions import Functions
from typing import Dict, Any, List, Tuple
import pandas as pd

class Absences:
    """
    Handles all absence-related operations in Zenegy API
    """

    def __init__(self, zenegy):
        """
        Initialize the Absences class.

        Args:
            zenegy: The Zenegy instance to use for API calls
        """
        self.zenegy = zenegy
        self.endpoint = f"api/companies/{self.zenegy.company_uid}/absence"

    def get(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        GetAbsenceDaysPerCompany
        Returns:
            DataFrame with absence information
        """
        endpoint = f"api/companies/{self.zenegy.company_uid}/absence"
        try:
            # Make the API request and get raw response
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
                valid_data, invalid_data = Functions.validate_data(df, AbsenceGet)
                return valid_data, invalid_data
            return pd.DataFrame(), pd.DataFrame()
        except Exception as e:
            raise Exception(f"Failed to retrieve absences: {str(e)}") from e

    def create(self, data: Dict[str, Any]) -> requests.Response:
        """
        Create
        Args:
            data (Dict[str, Any]): The data
        Returns:
            requests.Response: The API response
        """
        # Validate the data using Pydantic
        try:
            valid_data = CreateAbsenceRequest(**data)
            req_body = valid_data.model_dump(by_alias=True, mode='json',exclude_none=True)
            response = self.zenegy.post(endpoint=self.endpoint, json=req_body)
            self.zenegy.raise_for_status_with_details(response)
            return response
        except Exception as e:
            raise Exception(f"Failed to create absence: {str(e)}")

    def delete(self, absence_uid: UUID) -> requests.Response:
        endpoint = f"{self.endpoint}/{absence_uid}"
        try:
            response = self.zenegy.delete(endpoint=endpoint)
            self.zenegy.raise_for_status_with_details(response)
            return response
        except Exception as e:
            raise Exception(f"Failed to delete absence: {str(e)}")

    def update(self, absence_uid: UUID, data: Dict[str, Any]) -> requests.Response:
        """
        Update an existing absence record.

        Args:
            absence_uid (UUID): The absence uid to update
            data (Dict[str, Any]): The updated absence data

        Returns:
            requests.Response: The response from the API
        """
        # Validate the data using Pydantic
        try:
            valida_data = UpdateAbsenceRequest(**data)
            req_body = valida_data.model_dump(by_alias=True, mode='json', exclude_none=True)
            endpoint = f"{self.endpoint}/{absence_uid}"
            response = self.zenegy.put(endpoint=endpoint, json=req_body)
            self.zenegy.raise_for_status_with_details(response)
            return response
        except Exception as e:
            raise Exception(f"Failed to update absences: {str(e)}")
