"""
Excel Processor - A lightweight wrapper for Spire.XLS

This package re-exports Spire.XLS components for easier dependency management.
It allows you to use Spire.XLS functionality without directly depending on Spire.Xls.Free.

Example:
    >>> from excel_processor import Workbook, FileFormat
    >>> workbook = Workbook()
    >>> workbook.LoadFromFile("data.xlsx")
    >>> workbook.SaveToFile("output.xlsx", FileFormat.Version2016)
"""

from spire.xls import Workbook, FileFormat

__version__ = "0.1.0"
__all__ = [
    "Workbook",
    "FileFormat",
]
