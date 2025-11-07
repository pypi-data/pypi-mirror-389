"""Schema definitions for Zenegy package"""

from .absences import AbsenceGet, CreateAbsenceRequest, UpdateAbsenceRequest
from .companies import CompaniesGet
from .company_cost_centers import CostCentersGet, CostCenterCreate
from .company_departments import DepartmentsGet
from .employees import EmployeesGet, EmployeesGetById, EmployeeCreate, EmployeeUpsert, EmployeeUpdate
from .employee_pensions import PensionGet, EmployeePensionCreate
from .global_values import GlobalValuesGet, CompanyGlobalValueCreate, CompanyGlobalValueResponse, CompanyGlobalValueUpdate, GlobalValueAssign, AssignedGlobalValuesGet
from .global_value_sets import GlobalValueSetsGet, GlobalValueSetCreate, GlobalValueSetUpdate, GlobalValueSetEmployeeAssignment, GlobalValueSetEmployeeAssignmentResponse
from .employee_pay_checks import PayChecksGet, PaycheckCreate, PaycheckUpdate
from .payrolls import PayrollsGet
from .payslips import PayslipsGet
from .supplements_and_deductions_rates import SupplementRatesGet, SupplementRegistrationsGet

__all__ = [
    'AbsenceGet', 'CreateAbsenceRequest', 'UpdateAbsenceRequest',
    'CompaniesGet',
    'CostCentersGet', 'CostCenterCreate',
    'DepartmentsGet',
    'EmployeesGet', 'EmployeesGetById', 'EmployeeCreate', 'EmployeeUpsert', 'EmployeeUpdate',
    'PensionGet', 'EmployeePensionCreate',
    'SupplementRegistrationsGet',
    'GlobalValuesGet', 'CompanyGlobalValueCreate', 'CompanyGlobalValueResponse', 'CompanyGlobalValueUpdate', 'GlobalValueAssign', 'AssignedGlobalValuesGet',
    'GlobalValueSetsGet', 'GlobalValueSetCreate', 'GlobalValueSetUpdate', 'GlobalValueSetEmployeeAssignment', 'GlobalValueSetEmployeeAssignmentResponse',
    'PayChecksGet', 'PaycheckCreate', 'PaycheckUpdate',
    'PayrollsGet',
    'PayslipsGet',
    'SupplementRatesGet'
]
