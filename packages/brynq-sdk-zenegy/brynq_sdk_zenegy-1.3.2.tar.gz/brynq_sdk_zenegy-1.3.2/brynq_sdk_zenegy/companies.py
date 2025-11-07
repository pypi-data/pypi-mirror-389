from .schemas.companies import  CompaniesGet
from typing import Tuple
import pandas as pd
from brynq_sdk_functions import Functions

class Companies:
    """
    Handles all company-related operations in Zenegy API
    """

    def __init__(self, zenegy):
        """
        Initialize the Companies class.

        Args:
            zenegy: The Zenegy instance to use for API calls
        """
        self.zenegy = zenegy
        self.endpoint = "api/companies"

    def get(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        GetCurrentUserCompanies

        Returns:
            Tuple of (valid_data, invalid_data) DataFrames with company information
        """
        try:
            # Make the API request and get raw response
            content = self.zenegy.get(endpoint=self.endpoint)

            # Normalize the data (content is already an array)
            df = pd.DataFrame(content)

            if df.empty:
                return pd.DataFrame(), pd.DataFrame()

            # Validate data using schema
            valid_data, invalid_data = Functions.validate_data(df, CompaniesGet)
            return valid_data, invalid_data

        except Exception as e:
            raise Exception(f"Failed to retrieve companies: {str(e)}") from e
