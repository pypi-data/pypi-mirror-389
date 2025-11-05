"""
Utility package initializer for Azure AI Search Plugin.

This package provides reusable utility modules such as:
- logger: for consistent logging configuration across the project
"""

from .logger import get_logger

__all__ = ["get_logger"]
