import threading
from typing import List, Dict, Any, Optional
from azure.cosmos import CosmosClient, exceptions
from .exceptions import CosmosConnectionError, CosmosQueryError, CosmosQuerySyntaxError
from .utils.logger import get_logger

logger = get_logger(__name__)

class CosmosDBRetriever:
    """
    Unified Cosmos DB connection and retrieval class.
    
    Provides:
    - Thread-safe CosmosClient initialization
    - Reusable container access
    - Common data retrieval utilities (get, query, etc.)
    """

    _client = None
    _lock = threading.Lock()

    def __init__(self, database_name: str, container_name: str,
                 endpoint: Optional[str] = None, key: Optional[str] = None):
        """
        Initialize the Cosmos DB retriever instance.

        Args:
            database_name (str): Name of the Cosmos DB database.
            container_name (str): Name of the container to connect to.
            endpoint (Optional[str]): Cosmos DB account endpoint.
            key (Optional[str]): Cosmos DB primary or read-only key.

        Raises:
            CosmosConnectionError: If credentials or connection initialization fails.
        """
        self.endpoint = endpoint 
        self.key = key 
        self.database_name = database_name
        self.container_name = container_name

        if not self.endpoint or not self.key:
            raise CosmosConnectionError("Missing Cosmos DB endpoint or key.")

        self.container = self._get_container()

    
    #  CONNECTION HANDLING
    
    def _get_client(self) -> CosmosClient:
        """
        Thread-safe singleton CosmosClient initialization.

        Returns:
            CosmosClient: Initialized Cosmos client.

        Raises:
            CosmosConnectionError: If client creation fails.
        """
        if CosmosDBRetriever._client is None:
            with CosmosDBRetriever._lock:
                if CosmosDBRetriever._client is None:
                    try:
                        logger.info("Initializing Cosmos DB client...")
                        CosmosDBRetriever._client = CosmosClient(
                            self.endpoint, credential=self.key
                        )
                    except Exception as e:
                        logger.error(f"Failed to initialize Cosmos DB client: {e}")
                        raise CosmosConnectionError(str(e))
        return CosmosDBRetriever._client

    def _get_container(self):
        """
        Retrieve Cosmos DB container client.

        Returns:
            ContainerProxy: The connected container client.

        Raises:
            CosmosConnectionError: If container access fails.
        """
        try:
            client = self._get_client()
            database = client.get_database_client(self.database_name)
            container = database.get_container_client(self.container_name)
            logger.info(f"Connected to container: {self.container_name}")
            return container
        except Exception as e:
            logger.error(f"Failed to get container: {e}")
            raise CosmosConnectionError(str(e))

    
    # RETRIEVAL METHODS
   
    def get_item_by_id(self, item_id: str, partition_key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single item by its ID and partition key.

        Args:
            item_id (str): Unique identifier of the item.
            partition_key (str): Partition key value for the item.

        Returns:
            Optional[Dict[str, Any]]: Retrieved item if found, else None.

        Raises:
            CosmosQueryError: If retrieval operation fails.
        """
        try:
            item = self.container.read_item(item=item_id, partition_key=partition_key)
            logger.info(f"Retrieved item with ID: {item_id}")
            return item
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Item not found: {item_id}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving item {item_id}: {e}")
            raise CosmosQueryError(str(e))

    def fetch_all_items(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
         Retrieve all documents from the container with an optional record limit.

        Args:
            limit (int, optional): Maximum number of records to retrieve. 
                Defaults to 100.

        Returns:
            List[Dict[str, Any]]: List of retrieved documents.

        Raises:
            CosmosQueryError: If the query execution fails.
        """
        try:
            # Build query with limit

            query = f"SELECT * FROM c OFFSET 0 LIMIT {limit}"

            items = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
                ))
            
            logger.info(f"Fetched {len(items)} items (limit={limit}) from container '{self.container_name}'")
            return items

        except Exception as e:
            logger.error(f"Error fetching items (limit={limit}): {e}")
            raise CosmosQueryError(str(e))

    def fetch_by_field(
            self, 
            filters: Dict[str, Any]
            ) -> List[Dict[str, Any]]:
        
        """
        Retrieve documents filtered by one or more fields with input validation.

        Args:
            filters (Dict[str, Any]): A dictionary of field-value pairs to filter on.
                Example: {"status": "active", "type": "premium"}

        Returns:
            List[Dict[str, Any]]: List of matching documents.

        Raises:
            ValueError: If filters are empty or contain invalid field names.
            CosmosQueryError: If query execution fails.
        
        """
        
        try:
            if not filters or not isinstance(filters, dict):
                raise ValueError("Filters must be a non-empty dictionary.")
            
            # Input validation: only allow safe field names (alphanumeric + underscore)
            for field in filters.keys():
                if not field.replace("_", "").isalnum():
                    raise CosmosQuerySyntaxError(f"Invalid field name: {field}")
                
            # Build WHERE clause dynamically but safely
            conditions = []
            parameters = []
            for idx, (field, value) in enumerate(filters.items()):
                param_name = f"@param{idx}"
                conditions.append(f"c.{field} = {param_name}")
                parameters.append({"name": param_name, "value": value})

            where_clause = " AND ".join(conditions)
            query = f"SELECT * FROM c WHERE {where_clause}"

            # Execute parameterized query (prevents injection)
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))

            logger.info(f"Fetched {len(items)} items using filters: {filters}")
            return items
        
        except CosmosQuerySyntaxError  as ve:
            logger.error(f"Input validation failed: {ve}")
            raise CosmosQueryError(str(ve))
        
        except Exception as e:
            logger.error(f"Error fetching by fields {filters}: {e}")
            raise CosmosQueryError(str(e))

    def query_knowledge_source(
        self,
        sql_query: str,
        parameters: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Execute a safe SQL query on Cosmos DB.

        Only `SELECT` queries are allowed to prevent destructive operations.

        Args:
            sql_query (str): SQL-like query string.
            parameters (Optional[List[Dict[str, Any]]]): Query parameters.

        Returns:
            Dict[str, Any]: Dictionary with 'count' and 'items' retrieved.

        Raises:
            CosmosQuerySyntaxError: If unsafe or invalid query is detected.
            CosmosQueryError: If query execution fails.
        """

        try:
            # Allow only SELECT queries
            upper_query = sql_query.strip().upper()

            if not upper_query.startswith("SELECT"):
                raise CosmosQuerySyntaxError("Only SELECT queries are allowed.")
            
            disallowed_words = ["DELETE", "DROP", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]
            if any(word in upper_query for word in disallowed_words):
                raise CosmosQuerySyntaxError("Destructive operations are not permitted.")   
            
            query_result = list(self.container.query_items(
                query=sql_query,
                parameters=parameters or [],
                enable_cross_partition_query=True
            ))

            logger.info(f"Query executed successfully. {len(query_result)} items retrieved.")
            return {"count": len(query_result), "items": query_result}
        
        except CosmosQuerySyntaxError as se:
            logger.error(f"Query syntax validation failed: {se}")
            raise

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise CosmosQueryError(str(e))
