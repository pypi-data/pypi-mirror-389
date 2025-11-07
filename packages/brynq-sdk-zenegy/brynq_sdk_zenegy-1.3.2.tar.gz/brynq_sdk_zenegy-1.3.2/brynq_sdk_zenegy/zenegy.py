import requests
import pandas as pd
from typing import Dict, Any, Optional, Type, List
from uuid import UUID
from pydantic import BaseModel
from datetime import datetime

from .absence import Absences
from brynq_sdk_brynq import BrynQ
from brynq_sdk_functions import Functions
from .companies import Companies
from .employees import Employees
from .cost_center import CostCenter
from .payroll import Payrolls
from .payslips import Payslips
from .global_values import GlobalValues
from .global_value_sets import GlobalValueSets
from .supplements_and_deductions_rates import SupplementsAndDeductionsRates
from .departments import CompanyDepartments
from .employee_documents import EmployeeDocuments

class Zenegy(BrynQ):
    """
    Base class for interacting with the Zenegy API.
    """

    # Default timeout in seconds for all requests
    TIMEOUT = 30

    def __init__(self, system_type: str,
                 debug: bool = False, test_environment: bool = False, test_environment_id: str = None):
        """
        Initialize the Zenegy API client.

        Args:
            system_type (str): System type
            test_environment (bool): Test environment flag
            debug (bool): Debug flag
        """
        super().__init__()

        if not test_environment and test_environment_id is None:
            self.base_url = "https://api.zenegy.com"
            system = "zenegy"
        elif test_environment_id:
            self.base_url = "https://api-gateway.beta.zalary.com"
            system = "zenegy-development"
            self.data_interface_id = test_environment_id
            self.interfaces._brynq.data_interface_id = test_environment_id
            self.interfaces.credentials._brynq.data_interface_id = test_environment_id
        else:
            raise ValueError("Test environment ID is required, please set up interface for test enviromnent of Zenegy")

        # Get credentials
        credentials = self.interfaces.credentials.get(
            system=system,
            system_type=system_type,
            test_environment=test_environment,
        )

        # Get bearer token
        self.token = credentials["data"]["access_token"]
        self.company_uid = credentials["data"]["company_id"]

        # Initialize session with timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        self.session.timeout = self.TIMEOUT

        # Set debug mode
        self.debug = debug

        # Initialize entity classes
        self.absences = Absences(self)
        self.companies = Companies(self)
        self.cost_centers = CostCenter(self)
        self.employees = Employees(self)
        self.payrolls = Payrolls(self)
        self.payslips = Payslips(self)
        self.employee_documents = EmployeeDocuments(self)
        self.global_values = GlobalValues(self)
        self.global_value_sets = GlobalValueSets(self)
        self.supplements_and_deduction_rates = SupplementsAndDeductionsRates(self)
        self.departments = CompanyDepartments(self)

    def get(self, endpoint: str, params: Dict[str, Any] = None):
        """
        Make a GET request to the API.

        Args:
            endpoint: API endpoint to call
            params: Query parameters

        Returns:
            Raw API response data
        """
        try:
            # Make the API request
            response = self.session.get(
                url=f"{self.base_url}/{endpoint}",
                params=params,
                timeout=self.TIMEOUT,
            )
            self.raise_for_status_with_details(response)
            content = response.json()

            return content

        except Exception as e:
            raise Exception(f"Failed to retrieve data: {str(e)}") from e

    def post(self, endpoint: str, json: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        Make a POST request using the shared session with timeout.

        Args:
            endpoint: API endpoint to call
            json: JSON body to send in the request

        Returns:
            requests.Response: Raw response object
        """
        try:
            response = self.session.post(
                url=f"{self.base_url}/{endpoint}",
                json=json,
                timeout=self.TIMEOUT,
            )
            self.raise_for_status_with_details(response)
            return response
        except Exception as e:
            raise Exception(f"Failed to POST {endpoint}: {str(e)}") from e

    def patch(self, endpoint: str, json: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        Make a PATCH request using the shared session with timeout.

        Args:
            endpoint: API endpoint to call
            json: JSON body to send in the request

        Returns:
            requests.Response: Raw response object
        """
        try:
            response = self.session.patch(
                url=f"{self.base_url}/{endpoint}",
                json=json,
                timeout=self.TIMEOUT,
            )
            self.raise_for_status_with_details(response)
            return response
        except Exception as e:
            raise Exception(f"Failed to PATCH {endpoint}: {str(e)}") from e

    def put(self, endpoint: str, json: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        Make a PUT request using the shared session with timeout.

        Args:
            endpoint: API endpoint to call
            json: JSON body to send in the request

        Returns:
            requests.Response: Raw response object
        """
        try:
            response = self.session.put(
                url=f"{self.base_url}/{endpoint}",
                json=json,
                timeout=self.TIMEOUT,
            )
            self.raise_for_status_with_details(response)
            return response
        except Exception as e:
            raise Exception(f"Failed to PUT {endpoint}: {str(e)}") from e

    def delete(self, endpoint: str) -> requests.Response:
        """
        Make a DELETE request using the shared session with timeout.

        Args:
            endpoint: API endpoint to call

        Returns:
            requests.Response: Raw response object
        """
        try:
            response = self.session.delete(
                url=f"{self.base_url}/{endpoint}",
                timeout=self.TIMEOUT,
            )
            self.raise_for_status_with_details(response)
            return response
        except Exception as e:
            raise Exception(f"Failed to DELETE {endpoint}: {str(e)}") from e

    def raise_for_status_with_details(self, response: requests.Response) -> None:
        """
        Raises HTTPError if the response contains an HTTP error status.
        Additionally includes response content (JSON or plain text) in the exception message
        to provide more detailed context.
        """
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            # Attempt to extract error details from the response
            try:
                error_details = response.json()
            except ValueError:
                # If the response is not JSON, fall back to plain text
                error_details = response.text

            # Raise a new exception with the detailed message
            raise requests.exceptions.HTTPError(
                f"{str(e)}\nResponse details:\n{error_details}"
            ) from e
