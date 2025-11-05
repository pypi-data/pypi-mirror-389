import os
import socket
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests

from leap_bundle.types.create import SignedUrlData


def upload_directory_with_signed_url(
    signed_url_data: SignedUrlData, directory_path: str
) -> None:
    """Legacy upload directory to S3 using signed URL (fallback)."""
    path = Path(directory_path)
    hostname: Optional[str] = None
    try:
        parsed_url = urlparse(signed_url_data.url)
        if parsed_url.hostname:
            hostname = parsed_url.hostname
            socket.getaddrinfo(hostname, None)
    except (socket.gaierror, OSError) as e:
        raise ConnectionError(
            f"Cannot access AWS services. Please ensure you can reach {hostname or 'AWS host'}. "
            f"Check your internet connection and DNS settings. Error: {e}"
        ) from e

    for root, dirnames, filenames in os.walk(path):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for filename in filenames:
            if filename.startswith("."):
                continue
            file_path = Path(root) / filename
            relative_path = file_path.relative_to(path)

            form_data = signed_url_data.fields.copy()
            form_data["key"] = form_data["key"].replace(
                "${filename}", str(relative_path)
            )

            with open(file_path, "rb") as f:
                files = {"file": f}
                response = requests.post(
                    signed_url_data.url, data=form_data, files=files, timeout=600
                )
                response.raise_for_status()
