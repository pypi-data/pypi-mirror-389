"""
Azure AI Search Plugin Package.

This package provides integration utilities for:
- Azure Cognitive Search plugin (`AzureSearchPlugin`)
- Cosmos DB data retrieval (`CosmosDBRetriever`)
- Custom Cosmos DB exception handling

Exports:
    AzureSearchPlugin (class): Interface for Azure AI Search operations.
    CosmosDBRetriever (class): Cosmos DB connection and query management.
    CosmosConnectionError (Exception): Raised when Cosmos DB connection fails.
    CosmosQueryError (Exception): Raised for query or retrieval failures.
    CosmosQuerySyntaxError (Exception): Raised for unsafe or invalid queries.
"""

from .main import AzureSearchPlugin
from .cosmos_data_retriever import CosmosDBRetriever
from .exceptions import CosmosConnectionError, CosmosQueryError, CosmosQuerySyntaxError

__all__ = ["AzureSearchPlugin",
           "CosmosDBRetriever",
            "CosmosConnectionError",
            "CosmosQueryError",
            "CosmosQuerySyntaxError"]
