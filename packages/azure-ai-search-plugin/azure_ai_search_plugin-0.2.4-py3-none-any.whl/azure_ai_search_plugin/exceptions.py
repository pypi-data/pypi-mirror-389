class CosmosConnectionError(Exception):
    """Exception raised when the connection to Cosmos DB fails.

    This error is thrown when there is a problem establishing or maintaining
    a connection to the Azure Cosmos DB instance, such as invalid credentials,
    missing endpoint, or network unavailability.
    """
    pass


class CosmosQueryError(Exception):
    """Exception raised when a Cosmos DB query or item retrieval fails.

    This error occurs during query execution or data retrieval, typically
    due to runtime issues such as invalid parameters, timeouts, or API errors.
    """
    pass


class CosmosQuerySyntaxError(Exception):
    """Exception raised when a query contains invalid syntax or unsafe operations.

    This error is used to flag potentially destructive or malformed queries,
    such as attempts to execute non-SELECT operations (e.g., DELETE, DROP, UPDATE, INSERT, ALTER, TRUNCATE).
    """
    pass
