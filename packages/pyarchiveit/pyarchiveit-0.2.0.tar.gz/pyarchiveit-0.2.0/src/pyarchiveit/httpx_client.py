"""HTTPX Client for interacting with Archive-it API."""

from types import TracebackType

import httpx


class HTTPXClient:
    """A simple HTTP client using httpx library with context manager support."""

    def __init__(
        self,
        account_name: str,
        account_password: str,
        base_url: str = "https://partner.archive-it.org/api/",
        default_timeout: float | None = None,
    ) -> None:
        """Initialize the HTTPXClient with authentication and base URL.

        Args:
            account_name (str): The account name for authentication.
            account_password (str): The account password for authentication.
            base_url (str): The base URL for the API endpoints. Defaults to Archive-it API base URL.
            default_timeout (float | None): Default timeout in seconds. Use None for no timeout.

        """
        self.account_name = account_name
        self.account_password = account_password
        self.base_url = base_url
        self.default_timeout = default_timeout
        self.client = httpx.Client(
            auth=(self.account_name, self.account_password),
            follow_redirects=True,
            timeout=default_timeout,
        )

    def __enter__(self) -> "HTTPXClient":
        """Enter context manager."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        """Exit context manager and close the client."""
        self.close()
        return False

    def close(self) -> None:
        """Close the HTTP client and release resources."""
        if hasattr(self, "client") and self.client is not None:
            self.client.close()

    def get(
        self, endpoint: str, params: dict | None = None, timeout: float | None = None
    ) -> httpx.Response:
        """Send a GET request to the specified endpoint.

        Args:
            endpoint (str): The API endpoint path.
            params (dict | None): Query parameters to include in the request.
            timeout (float | None): Timeout in seconds for this request. Uses client default if not specified.

        Returns:
            httpx.Response: The HTTP response object.

        Raises:
            httpx.HTTPStatusError: If the response status code indicates an error.

        """
        url = self.base_url + endpoint
        kwargs = {"params": params}
        if timeout is not None:
            kwargs["timeout"] = timeout
        response = self.client.get(url, **kwargs)
        response.raise_for_status()
        return response

    def post(
        self,
        endpoint: str,
        data: dict | None = None,
        timeout: float | None = None,
        headers: dict | None = None,
    ) -> httpx.Response:
        """Send a POST request to the specified endpoint.

        Args:
            endpoint (str): The API endpoint path.
            data (dict | None): JSON data to send in the request body.
            timeout (float | None): Timeout in seconds for this request. Uses client default if not specified.

        Returns:
            httpx.Response: The HTTP response object.

        Raises:
            httpx.HTTPStatusError: If the response status code indicates an error.

        """
        url = self.base_url + endpoint
        kwargs = {"json": data}
        if timeout is not None:
            kwargs["timeout"] = timeout
        response = self.client.post(url, **kwargs)
        response.raise_for_status()
        return response

    def put(
        self, endpoint: str, data: dict | None = None, timeout: float | None = None
    ) -> httpx.Response:
        """Send a PUT request to the specified endpoint.

        Args:
            endpoint (str): The API endpoint path.
            data (dict | None): JSON data to send in the request body.
            timeout (float | None): Timeout in seconds for this request. Uses client default if not specified.

        Returns:
            httpx.Response: The HTTP response object.

        Raises:
            httpx.HTTPStatusError: If the response status code indicates an error.

        """
        url = self.base_url + endpoint
        kwargs = {"json": data}
        if timeout is not None:
            kwargs["timeout"] = timeout
        response = self.client.put(url, **kwargs)
        response.raise_for_status()
        return response

    def patch(
        self, endpoint: str, data: dict | None = None, timeout: float | None = None
    ) -> httpx.Response:
        """Send a PATCH request to the specified endpoint.

        Args:
            endpoint (str): The API endpoint path.
            data (dict | None): JSON data to send in the request body.
            timeout (float | None): Timeout in seconds for this request. Uses client default if not specified.

        Returns:
            httpx.Response: The HTTP response object.

        Raises:
            httpx.HTTPStatusError: If the response status code indicates an error.

        """
        url = self.base_url + endpoint
        kwargs = {"json": data}
        if timeout is not None:
            kwargs["timeout"] = timeout
        response = self.client.patch(url, **kwargs)
        response.raise_for_status()
        return response

    def delete(self, endpoint: str, timeout: float | None = None) -> httpx.Response:
        """Send a DELETE request to the specified endpoint.

        Args:
            endpoint (str): The API endpoint path.
            timeout (float | None): Timeout in seconds for this request. Uses client default if not specified.

        Returns:
            httpx.Response: The HTTP response object.

        Raises:
            httpx.HTTPStatusError: If the response status code indicates an error.

        """
        url = self.base_url + endpoint
        kwargs = {}
        if timeout is not None:
            kwargs["timeout"] = timeout
        response = self.client.delete(url, **kwargs)
        response.raise_for_status()
        return response
