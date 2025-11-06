import logging
from azure.search.documents.aio import SearchClient  # async client
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import HttpResponseError, ServiceRequestError
from azure.core.pipeline.policies import RetryPolicy, AsyncHTTPPolicy
from semantic_kernel.functions import kernel_function
 
# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
 
# -------------------------------
# Custom Timeout Policy
# -------------------------------
class TimeoutPolicy(AsyncHTTPPolicy):
    """Custom asynchronous timeout policy for Azure SDK HTTP requests.
 
    This policy ensures that each outgoing request respects a defined timeout
    duration. It can be applied to async clients like `SearchClient` to prevent
    indefinite waiting in case of network slowness or service delay.
 
    Attributes:
        timeout (int): The timeout duration (in seconds) for each request.
    """
 
    def __init__(self, timeout: int = 10):
        """
        Initialize the timeout policy.
 
        Args:
            timeout (int, optional): The maximum time allowed for each request
                before timing out. Defaults to 10 seconds.
        """
        super().__init__()
        self.timeout = timeout
 
    async def send(self, request):
        """
        Apply the timeout setting to each HTTP request.
 
        Args:
            request: The HTTP request object from the Azure SDK pipeline.
 
        Returns:
            The HTTP response after applying the timeout.
 
        """
        request.http_request.timeout = self.timeout
        return await self.next.send(request)
 
 
# -------------------------------
# AzureSearchPlugin Implementation
# -------------------------------
 
class AzureSearchPlugin:
    """Asynchronous Azure Cognitive Search plugin for Semantic Kernel or standalone use.
 
    This plugin performs semantic or keyword-based searches over a configured Azure
    Cognitive Search index. It uses an asynchronous client with retry and timeout
    policies for reliability and returns the top matching document based on confidence score.
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
            max_retries (int, optional): Number of retry attempts for transient errors.
                Defaults to 3.
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
            policies=[timeout_policy],
        )
 
        self.semantic_config = semantic_config
        self.max_retries = max_retries
        self.timeout = timeout
 
    @kernel_function(
        description="Performs a semantic or keyword search asynchronously and returns the top matching document."
    )
    async def search_top(self, query: str, top_k: int):
        """Perform an asynchronous Azure Cognitive Search query and return the top result.
 
        This method performs a semantic or keyword search using Azure Cognitive Search.
        It retrieves the top `top_k` documents, calculates their confidence scores,
        and returns the document with the highest score.
 
        Args:
            query (str): Search text input from the user.
            top_k (int): Number of top results to retrieve. Must be a positive integer.
 
        Returns:
            dict | None: The best matching document with all index fields and a `_confidence`
            score, or None if no results are found or an error occurs.
 
        Raises:
            ValueError: If the `top_k` parameter is not a positive integer.
            HttpResponseError: If the Azure Search service returns an HTTP error.
            ServiceRequestError: If a network or request-level error occurs.
            TimeoutError: If the request exceeds the configured timeout duration.
 
        Example:
            ```python
            plugin = AzureSearchPlugin(
                endpoint="https://my-search.search.windows.net",
                api_key="YOUR_API_KEY",
                index_name="my-index",
                semantic_config="my-semantic-config"
            )
 
            result = await plugin.search_top("Azure AI Search overview", top_k=3)
            print(result)
            ```
        """
        try:
            # Validate top_k parameter
            if not isinstance(top_k, int) or top_k <= 0:
                raise ValueError(
                    f"Invalid 'top_k' value: {top_k}. It must be a positive integer."
                )
 
            # Await the async search operation
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
 
            # Iterate asynchronously over search results
            async for doc in results:
                item = dict(doc)
                try:
                    score_value = doc.get("@search.score")
                    item["_confidence"] = float(score_value)
                except (TypeError, ValueError, AttributeError):
                    item["_confidence"] = (
                        score_value if isinstance(score_value, (int, float)) else None
                    )
                results_list.append(item)
 
            if results_list:
                top_doc = max(results_list, key=lambda x: x["_confidence"])
                logger.info(
                    f"Top document retrieved successfully (Confidence: {top_doc['_confidence']})"
                )
                return top_doc
 
        except ValueError as ve:
            logger.error(f"Validation error: {ve}", exc_info=True)
        except HttpResponseError as http_err:
            logger.error(
                f"HTTP error occurred while querying Azure Search: {http_err}",
                exc_info=True,
            )
        except ServiceRequestError as service_err:
            logger.error(
                f"Service request error occurred while connecting to Azure Search: {service_err}",
                exc_info=True,
            )
        except TimeoutError:
            logger.error(
                "Azure Search request timed out. Consider increasing the timeout value.",
                exc_info=True,
            )
        except Exception as e:
            logger.error(
                f"Unexpected error in AzureSearchPlugin: {e}",
                exc_info=True,
            )
        finally:
            if self.client:
                await self.client.close()
 
        return None