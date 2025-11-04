# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from .._models import BaseModel

__all__ = [
    "FileTypeGetResponse",
    "Document",
    "DocumentFormat",
    "Image",
    "ImageFormat",
    "Presentation",
    "PresentationFormat",
    "Spreadsheet",
    "SpreadsheetFormat",
    "Text",
    "TextFormat",
]


class DocumentFormat(BaseModel):
    extension: str
    """The extension of the file type"""

    mime_type: str
    """The MIME type of the file type"""


class Document(BaseModel):
    formats: List[DocumentFormat]


class ImageFormat(BaseModel):
    extension: str
    """The extension of the file type"""

    mime_type: str
    """The MIME type of the file type"""


class Image(BaseModel):
    formats: List[ImageFormat]


class PresentationFormat(BaseModel):
    extension: str
    """The extension of the file type"""

    mime_type: str
    """The MIME type of the file type"""


class Presentation(BaseModel):
    formats: List[PresentationFormat]


class SpreadsheetFormat(BaseModel):
    extension: str
    """The extension of the file type"""

    mime_type: str
    """The MIME type of the file type"""


class Spreadsheet(BaseModel):
    formats: List[SpreadsheetFormat]


class TextFormat(BaseModel):
    extension: str
    """The extension of the file type"""

    mime_type: str
    """The MIME type of the file type"""


class Text(BaseModel):
    formats: List[TextFormat]


class FileTypeGetResponse(BaseModel):
    document: Document
    """Information about supported file formats in a category"""

    image: Image
    """Information about supported file formats in a category"""

    presentation: Presentation
    """Information about supported file formats in a category"""

    spreadsheet: Spreadsheet
    """Information about supported file formats in a category"""

    text: Text
    """Information about supported file formats in a category"""
