import logging
from azure.search.documents.aio import SearchClient  # async client
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError, ServiceRequestError
from azure.core.pipeline.policies import RetryPolicy, HTTPPolicy
from semantic_kernel.functions import kernel_function


# -------------------------------
# Logging Configuration
# -------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# -------------------------------
# Custom Timeout Policy
# -------------------------------
class TimeoutPolicy(HTTPPolicy):
    """Custom timeout policy for requests."""

    def __init__(self, timeout: int = 10):
        super().__init__()
        self.timeout = timeout

    def send(self, request):
        # Apply timeout to each HTTP request
        request.http_request.timeout = self.timeout
        return self.next.send(request)


# -------------------------------
# AzureSearchPlugin Implementation
# -------------------------------
class AzureSearchPlugin:
    """Asynchronous Azure Cognitive Search plugin for Semantic Kernel or standalone use.

    Provides semantic or keyword-based searches over an Azure Cognitive Search index
    using an async client with retry and timeout policies.
    """

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        index_name: str,
        semantic_config: str = None,
        max_retries: int = 3,
        timeout: int = 10,
    ):
        """Initialize the async Azure Cognitive Search client with retry and timeout logic.

        Args:
            endpoint (str): The endpoint URL of the Azure Cognitive Search service.
            api_key (str): The API key used for authentication.
            index_name (str): The name of the Azure Cognitive Search index to query.
            semantic_config (str, optional): The name of the semantic configuration
                for semantic search. Defaults to None.
            max_retries (int, optional): Number of retry attempts for transient errors. Defaults to 3.
            timeout (int, optional): Timeout in seconds for each request. Defaults to 10.

        Raises:
            ValueError: If any required configuration values are missing.
        """
        if not all([endpoint, api_key, index_name]):
            raise ValueError("Missing required Azure Search configuration values.")

        retry_policy = RetryPolicy(total_retries=max_retries)
        timeout_policy = TimeoutPolicy(timeout=timeout)

        # Async SearchClient with retry/timeout policies
        self.client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=AzureKeyCredential(api_key),
            retry_policy=retry_policy,
            transport=None,  # Let the SDK handle HTTP transport
        )

        self.semantic_config = semantic_config
        self.max_retries = max_retries
        self.timeout_policy = timeout_policy
        self.timeout = timeout

    # -------------------------------
    # Semantic Search Function
    # -------------------------------
    @kernel_function(
        description="Performs a semantic or keyword search asynchronously and returns the top matching document."
    )
    async def search_top(self, query: str, top_k: int):
        """Perform an asynchronous Azure Cognitive Search query and return the top result.

        Args:
            query (str): Search text input from the user.
            top_k (int): Number of top results to retrieve. Must be a positive integer.

        Returns:
            dict | None: The best matching document with a `_confidence` score,
            or None if no results are found or an error occurs.
        """
        try:
            if not isinstance(top_k, int) or top_k <= 0:
                raise ValueError(f"Invalid 'top_k' value: {top_k}. Must be a positive integer.")

            # Perform semantic or keyword search
            if self.semantic_config:
                results = await self.client.search(
                    search_text=query,
                    query_type="semantic",
                    semantic_configuration_name=self.semantic_config,
                    top=top_k,
                )
            else:
                results = await self.client.search(search_text=query, top=top_k)

            results_list = []

            async for doc in results:
                item = dict(doc)
                score_value = doc.get("@search.score")
                try:
                    item["_confidence"] = float(score_value)
                except (TypeError, ValueError):
                    item["_confidence"] = None
                results_list.append(item)

            if results_list:
                top_doc = max(results_list, key=lambda x: x["_confidence"] or 0)
                logger.info(
                    f"Top document retrieved successfully (Confidence: {top_doc['_confidence']})"
                )
                return top_doc

        except (ValueError, HttpResponseError, ServiceRequestError, TimeoutError) as e:
            logger.error(f"Search error: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Unexpected error in AzureSearchPlugin: {e}", exc_info=True)

        return None
