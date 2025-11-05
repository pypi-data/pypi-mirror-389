"""API client utilities for leap-bundle."""

from typing import Any, Dict, List, Literal, Optional, Union, cast

import requests

from leap_bundle import __version__
from leap_bundle.types.create import (
    BundleRequestExistsResponse,
    CreateBundleRequestBody,
    CreateBundleResponse,
    ResumeBundleResponse,
)
from leap_bundle.types.list import (
    BundleRequestDetailsResponse,
    BundleRequestResponse,
    GetBundleRequestDetailsResponse,
    GetBundleRequestsResponse,
)
from leap_bundle.utils.config import get_api_token, get_headers, get_server_url


class APIClient:
    """Client for LEAP API interactions."""

    def __init__(self) -> None:
        self.server_url = get_server_url()
        self.api_token = get_api_token()

    def _get_headers(self, include_api_token: bool = True) -> Dict[str, str]:
        """Get headers with authentication and stored custom headers."""
        headers = {
            "Content-Type": "application/json",
        }

        if include_api_token:
            if not self.api_token:
                raise ValueError(
                    "No API token found. Please run 'leap-bundle login' first."
                )
            headers.update({"Authorization": f"Bearer {self.api_token}"})

        custom_headers = get_headers()
        headers.update(custom_headers)

        return headers

    def create_bundle_request(
        self,
        input_path: str,
        input_hash: str,
        quantization: Optional[str] = None,
        model_type: Optional[str] = None,
        force_recreate: bool = False,
    ) -> Union[BundleRequestExistsResponse, CreateBundleResponse]:
        """Create a new bundle request."""
        url = f"{self.server_url.rstrip('/')}/api/cli/bundle-requests"
        request_body = CreateBundleRequestBody(
            input_path=input_path,
            input_hash=input_hash,
            force_recreate=force_recreate,
            quantization=quantization,
            model_type=model_type,
            cli_version=__version__,
        )

        response = requests.post(
            url, json=request_body.model_dump(), headers=self._get_headers(), timeout=30
        )

        if response.status_code == 409:
            return BundleRequestExistsResponse(message=response.json().get("error", ""))
        elif response.status_code == 200:
            return CreateBundleResponse.model_validate(response.json())
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get(
                    "error", f"HTTP {response.status_code} error"
                )
            except ValueError:
                error_msg = f"HTTP {response.status_code} error"
            raise requests.HTTPError(error_msg, response=response)

    def resume_bundle_request(self, request_id: int) -> ResumeBundleResponse:
        url = f"{self.server_url.rstrip('/')}/api/cli/bundle-requests/{request_id}"
        response = requests.post(url, headers=self._get_headers(), timeout=30)
        if response.status_code == 200:
            return ResumeBundleResponse.model_validate(response.json())
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get(
                    "error", f"HTTP {response.status_code} error"
                )
            except ValueError:
                error_msg = f"HTTP {response.status_code} error"
            raise requests.HTTPError(error_msg, response=response)

    def update_bundle_request_status(
        self,
        request_id: int,
        status: Literal["uploading_started", "uploading_completed", "uploading_failed"],
        user_message: Optional[str] = None,
    ) -> None:
        """Update bundle request status via PATCH endpoint.

        :param user_message: this is usually an error message in case of failure.
        """
        url = f"{self.server_url.rstrip('/')}/api/cli/bundle-requests/{request_id}"
        payload: Dict[str, Any] = {"status": status}
        if user_message:
            payload["user_message"] = user_message

        response = requests.patch(
            url, json=payload, headers=self._get_headers(), timeout=30
        )
        response.raise_for_status()

    def list_bundle_requests(self) -> List[BundleRequestResponse]:
        """List bundle requests for the authenticated user."""
        url = f"{self.server_url.rstrip('/')}/api/cli/bundle-requests"

        response = requests.get(url, headers=self._get_headers(), timeout=30)

        if response.status_code != 200:
            try:
                error_data = response.json()
                error_msg = error_data.get(
                    "error", f"HTTP {response.status_code} error"
                )
            except ValueError:
                error_msg = f"HTTP {response.status_code} error"
            raise requests.HTTPError(error_msg, response=response)

        return GetBundleRequestsResponse.model_validate(response.json()).requests

    def get_bundle_request(
        self, request_id: Union[str, int]
    ) -> BundleRequestDetailsResponse:
        """Get details for a specific bundle request."""
        url = f"{self.server_url.rstrip('/')}/api/cli/bundle-requests/{request_id}"

        response = requests.get(url, headers=self._get_headers(), timeout=30)

        if response.status_code != 200:
            try:
                error_data = response.json()
                error_msg = error_data.get(
                    "error", f"HTTP {response.status_code} error"
                )
            except ValueError:
                error_msg = f"HTTP {response.status_code} error"
            raise requests.HTTPError(error_msg, response=response)

        return GetBundleRequestDetailsResponse.model_validate(response.json()).request

    def download_bundle_request(self, request_id: str) -> Dict[str, Any]:
        """Get download URL for a completed bundle request."""
        url = f"{self.server_url.rstrip('/')}/api/cli/bundle-requests/{request_id}/download"

        response = requests.post(url, headers=self._get_headers(), timeout=30)

        if response.status_code != 200:
            try:
                error_data = response.json()
                error_msg = error_data.get(
                    "error", f"HTTP {response.status_code} error"
                )
            except ValueError:
                error_msg = f"HTTP {response.status_code} error"
            raise requests.HTTPError(error_msg, response=response)

        return cast(Dict[str, Any], response.json())

    def cancel_bundle_request(self, request_id: str) -> Dict[str, Any]:
        """Cancel a bundle request."""
        url = f"{self.server_url.rstrip('/')}/api/cli/bundle-requests/{request_id}"

        response = requests.delete(url, headers=self._get_headers(), timeout=30)

        if response.status_code not in [200, 404]:
            try:
                error_data = response.json()
                error_msg = error_data.get(
                    "error", f"HTTP {response.status_code} error"
                )
            except ValueError:
                error_msg = f"HTTP {response.status_code} error"
            raise requests.HTTPError(error_msg, response=response)

        result: Dict[str, Any] = response.json()
        return result

    def whoami(self) -> Dict[str, Any]:
        """Get current user information."""
        url = f"{self.server_url.rstrip('/')}/api/cli/whoami"

        response = requests.get(url, headers=self._get_headers(), timeout=10)

        if response.status_code != 200:
            try:
                error_data = response.json()
                error_msg = error_data.get(
                    "error", f"HTTP {response.status_code} error"
                )
            except ValueError:
                error_msg = f"HTTP {response.status_code} error"
            raise requests.HTTPError(error_msg, response=response)

        return cast(Dict[str, Any], response.json())

    def validate_token(self, token: str) -> bool:
        """Validate API token with the LEAP platform."""
        try:
            url = f"{self.server_url.rstrip('/')}/api/cli/login"
            response = requests.post(
                url,
                json={"api_token": token},
                headers=self._get_headers(False),
                timeout=10,
            )
            return response.status_code == 200
        except requests.RequestException:
            return False
