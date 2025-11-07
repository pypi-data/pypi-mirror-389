import requests
from uuid import UUID
from .schemas.company_cost_centers import (CostCenterCreate,
                                           CostCentersGet)
from brynq_sdk_functions import Functions
from typing import Dict, Any, List, Tuple
import pandas as pd


class CostCenter:
    """
    Handles all company cost center related operations in Zenegy API
    """

    def __init__(self, zenegy):
        """
        Initialize the Companycostcenters class.

        Args:
            zenegy: The Zenegy instance to use for API calls
        """
        self.zenegy = zenegy
        self.endpoint = f"api/companies/{self.zenegy.company_uid}/cost-center"

    def get(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        GetCompanyCostCentersAsync
        Returns:
            Tuple of (valid_data, invalid_data) DataFrames with cost center information
        """
        try:
            # Make the API request and get raw response
            content = self.zenegy.get(endpoint=self.endpoint)

            # Normalize the data (content is already an array)
            df = pd.DataFrame(content)

            if df.empty:
                return pd.DataFrame(), pd.DataFrame()

            # Validate data using schema
            valid_data, invalid_data = Functions.validate_data(df, CostCentersGet)
            return valid_data, invalid_data

        except Exception as e:
            raise Exception(f"Failed to retrieve cost centers: {str(e)}") from e

    def create(self, data: Dict[str, Any]) -> requests.Response:
        """
        CreateCostCenterAsync
        Args:
            data (Dict[str, Any]): The data
        Returns:
            requests.Response: The API response
        """
        # Validate the data using Pydantic
        try:
            req_data = CostCenterCreate(**data)
            req_body = req_data.model_dump(by_alias=True, mode='json',exclude_none=True)
            response = self.zenegy.post(endpoint=self.endpoint, json=req_body)
            self.zenegy.raise_for_status_with_details(response)
            return response
        except Exception as e:
            raise Exception(f"Failed to create cost center: {str(e)}")

    def delete(self, cost_center_uid: UUID) -> requests.Response:
        """
        DeleteCostCenterAsync
        Args:
            cost_center_uid (UUID): The cost center uid
        Returns:
            requests.Response: The API response
        """
        endpoint = f"{self.endpoint}/{cost_center_uid}"
        try:
            response = self.zenegy.delete(endpoint=endpoint)
            self.zenegy.raise_for_status_with_details(response)
            return response
        except Exception as e:
            raise Exception(f"Failed to delete cost center: {str(e)}")
