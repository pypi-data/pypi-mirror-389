"""This module provides a wrapper for the API."""

import logging
import os
from typing import Any, Dict

from httpx import AsyncClient, Auth, Client, Response
from pydantic import BaseModel

from axmp_openapi_helper.openapi.multi_openapi_spec import AuthenticationType

logger = logging.getLogger(__name__)

_TIMEOUT = os.getenv("HTTPX_DEFAULT_TIMEOUT", 10)


class AxmpAPIWrapper:
    """AxmpAPIWrapper is a wrapper for the API."""

    def __init__(
        self,
        server: str,
        /,
        *,
        cookies: dict | None = None,
        auth_type: AuthenticationType | None = AuthenticationType.NONE,
        tls_verify: bool | None = False,
        timeout: int | None = _TIMEOUT,
    ):
        """Initialize the AxmpAPIWrapper.

        Args:
            server (str): The server URL
            cookies (dict, optional): The cookies for the API request. Defaults to None.
            auth_type (AuthenticationType, optional): The authentication type. Defaults to AuthenticationType.NONE.
            tls_verify (bool, optional): Whether to verify the TLS certificate. Defaults to False.
            timeout (int, optional): The timeout for the API request. Defaults to _TIMEOUT.
        """
        if not server:
            raise ValueError("Server URL is required")

        self._server = server
        self._cookies = cookies or {}
        self._auth_type = auth_type
        self._tls_verify = tls_verify
        self._timeout = timeout

        # self._auth = None
        self._client = None
        self._async_client = None

        # if auth_type == AuthenticationType.BASIC:
        #     if not username or not password:
        #         raise ValueError(
        #             "Username and password are required for Basic authentication"
        #         )
        #     self._auth = BasicAuth(username=username, password=password)

    @property
    def async_client(self) -> AsyncClient:
        """Get the async client."""
        if self._async_client is None:
            self._async_client = AsyncClient(
                base_url=self._server,
                cookies=self._cookies,
                verify=self._tls_verify,
                timeout=self._timeout,
            )
        return self._async_client

    @property
    def client(self) -> Client:
        """Get the client."""
        if self._client is None:
            self._client = Client(
                base_url=self._server,
                cookies=self._cookies,
                verify=self._tls_verify,
                timeout=self._timeout,
            )
        return self._client

    async def close(self) -> None:
        """Close the async and sync clients."""
        if self._async_client is not None:
            await self._async_client.aclose()
            self._async_client = None
        if self._client is not None:
            self._client.close()
            self._client = None

    async def _get_response(self, response: Response) -> Dict[str, Any]:
        """Get response from API.

        Args:
            response (Response): Response from API

        Returns:
            Dict[str, Any]: Response data
        """
        if response.status_code == 200:
            logger.debug(f"Response: {response.json()}")

            return response.json()
        else:
            logger.warning(
                f"Failed to get response: {response.status_code} {response.text}"
            )
            return {
                "result": "failed",
                "code": response.status_code,
                "message": response.text,
            }

    async def run(
        self,
        method: str,
        path: str,
        /,
        *,
        headers: dict | None = None,
        auth: Auth | None = None,
        path_params: BaseModel | None = None,
        query_params: BaseModel | None = None,
        request_body: BaseModel | None = None,
    ) -> str:
        """Run the API request asynchronously.

        Args:
            method (str): The HTTP method to use
            path (str): The path to the resource
            headers (dict, optional): The headers for the API request. Defaults to None.
            auth (Auth, optional): The authentication for the API request. Defaults to None.
            path_params (Any, optional): Path parameters for the tool. Defaults to None.
            query_params (Any, optional): Query parameters for the tool. Defaults to None.
            request_body (Any, optional): Request body for the tool. Defaults to None.

        Returns:
            str: Response from the API
        """
        headers = headers or {}
        # NOTE: set the content type to application/json by default
        headers.update({"Content-Type": "application/json"})

        logger.debug(f"Method: {method}, Path: {path}")
        logger.debug("-" * 100)
        logger.debug(f"Headers: {headers}")
        logger.debug(f"Auth: {auth}")
        logger.debug(f"Path params: {path_params}")
        logger.debug(f"Query params: {query_params}")
        logger.debug(f"Request body: {request_body}")

        if path_params is not None:
            # for path parameters
            # NOTE: exclude_none=True, mode="json" is used to exclude None values and convert to json (e.g. Enum values)
            path = path.format(**path_params.model_dump(exclude_none=True, mode="json"))

            logger.debug(f"Formatted path: {path}")

        logger.debug(
            f"Query params: {query_params.model_dump_json(exclude_none=True) if query_params else None}"
        )
        logger.debug(
            f"Request body: {request_body.model_dump_json(exclude_none=True) if request_body else None}"
        )

        # NOTE: If the request body is an array, we need to get the value for the array
        request_body_array_value = None
        if request_body:
            request_body_array_value = await self._get_request_body_value_for_array(
                request_body
            )

        response = await self.async_client.request(
            method,
            path,
            headers=headers,
            auth=auth,
            params=query_params.model_dump(exclude_none=True, mode="json")
            if query_params
            else None,
            json=request_body_array_value
            if request_body_array_value
            else request_body.model_dump(exclude_none=True, mode="json")
            if request_body
            else None,
        )

        response.raise_for_status()

        return await self._get_response(response)

    async def _get_request_body_value_for_array(
        self, request_body: BaseModel
    ) -> list[Any] | None:
        """Get request body value for array.

        Args:
            request_body (BaseModel): Request body

        Returns:
            Any: Request body value
        """
        request_body_value = None
        for i, (field_name, field_info) in enumerate(
            type(request_body).model_fields.items()
        ):
            field_value = getattr(request_body, field_name)
            if i == 0 and field_value is not None:
                if isinstance(field_value, list):
                    request_body_value = [
                        item.model_dump(exclude_none=True, mode="json")
                        if isinstance(item, BaseModel)
                        else item
                        for item in field_value
                    ]
                    break
            else:
                logger.warning(f"Request body value is not array: {field_name}")
                return None

        logger.debug(f"Request body value: {request_body_value}")

        return request_body_value

    def __repr__(self) -> str:
        """Return the string representation of the AxmpAPIWrapper."""
        str = (
            f"AxmpAPIWrapper(server={self._server}, "
            f"cookies={self._cookies}, "
            f"auth_type={self._auth_type}, "
            f"tls_verify={self._tls_verify}, "
            f"timeout={self._timeout}"
        )
        return str
