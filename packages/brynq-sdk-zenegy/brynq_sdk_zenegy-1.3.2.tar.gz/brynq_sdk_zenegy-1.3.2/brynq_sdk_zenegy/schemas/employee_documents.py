# Generated schemas for tag: EmployeeDocuments

from typing import Optional

# BrynQ Pandera DataFrame Model for Employee Documents
from pandera.typing import Series
import pandera as pa
import pandas as pd
from brynq_sdk_functions import BrynQPanderaDataFrameModel


class EmployeeDocumentsGet(BrynQPanderaDataFrameModel):
    """Flattened schema for Zenegy Employee Documents output data"""
    employee_uid: Optional[Series[pd.StringDtype]] = pa.Field(nullable=True, description="Employee UID", alias="employeeUid",)
    created_on: Optional[Series[pd.StringDtype]] = pa.Field(nullable=True, description="Document creation timestamp", alias="createdOn",)
    file_name: Optional[Series[pd.StringDtype]] = pa.Field(nullable=True, description="Original file name", alias="fileName")
    file_size: Optional[Series[pd.Int64Dtype]] = pa.Field(nullable=True, description="Document size in bytes", alias="fileSize")
    description: Optional[Series[pd.StringDtype]] = pa.Field(nullable=True, description="Document description", alias="description")
    is_protected: Optional[Series[pd.BooleanDtype]] = pa.Field(nullable=True, description="Indicates if the document is protected", alias="isProtected")
    extension: Optional[Series[pd.Int64Dtype]] = pa.Field(nullable=True, description="File extension enum", alias="extension", isin=[0, 1, 2, 3, 4, 5])
    is_document_owner: Optional[Series[pd.BooleanDtype]] = pa.Field(nullable=True, description="Whether the employee owns the document", alias="isDocumentOwner")
    id: Optional[Series[pd.Int64Dtype]] = pa.Field(nullable=True, description="Numeric document ID", alias="id")
    uid: Optional[Series[pd.StringDtype]] = pa.Field(nullable=True,description="Document UID", alias="uid")

    class Config:
        coerce = True

    class _Annotation:
        primary_key = "uid"
        foreign_keys = {}
