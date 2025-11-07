from uuid import UUID
from typing import Tuple
import pandas as pd

from brynq_sdk_functions import Functions
from .schemas.employee_documents import EmployeeDocumentsGet


class EmployeeDocuments:
    """Handles all employee document related operations in the Zenegy API"""

    def __init__(self, zenegy):
        """Initialize the EmployeeDocuments class with a Zenegy client instance."""
        self.zenegy = zenegy

    def get(self, employee_uid: UUID) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Retrieve all documents for a given employee.

        Args:
            employee_uid: The employee UID.

        Returns:
            Tuple of (valid_data, invalid_data) Pandas DataFrames.
        """
        try:
            endpoint = (
                f"api/employees/{employee_uid}/companies/{self.zenegy.company_uid}/documents"
            )
            content = self.zenegy.get(endpoint=endpoint)

            records = content if isinstance(content, list) else content.get("data", [])
            df = pd.json_normalize(records, sep="__")
            if df.empty:
                return pd.DataFrame(), pd.DataFrame()

            valid_data, invalid_data = Functions.validate_data(df, EmployeeDocumentsGet)
            return valid_data, invalid_data
        except Exception as e:
            raise Exception(f"Failed to retrieve employee documents: {str(e)}") from e
