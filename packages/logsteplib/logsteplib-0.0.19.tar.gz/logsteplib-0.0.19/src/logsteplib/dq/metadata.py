"""
Define data quality metadata structures for logging and future database
persistence.

This module provides a dataclass for encapsulating metadata related to data
quality tracking, including file attributes, user information, processing
status, and rejection reasons.
Use this structure to support logging, auditing, and persistence of data
quality events.

Classes
-------
DQMetadata
    Represent metadata for data quality tracking, including file and user
    details.

Examples
--------
Create a DQMetadata instance and convert it to JSON:

    metadata = DQMetadata(
        target="my_table",
        key="123",
        input_file_name="input.csv",
        file_name="output.csv",
        user_name="jdoe",
        user_email="jdoe@example.com",
        modify_date="2025-10-30",
        file_size="1024",
        file_row_count="100",
        status="SUCCESS"
    )
    json_str = metadata.to_json()
"""

from dataclasses import dataclass, asdict
from typing import Optional
import json


@dataclass
class DQMetadata:
    """
    Serialize the metadata instance to a JSON-formatted string.

    Convert all metadata fields into a human-readable JSON string for logging,
    transmission, or storage.

    Returns
    -------
    str
        JSON representation of the metadata.
    """

    target: str
    key: str
    input_file_name: str
    file_name: str
    user_name: str
    user_email: str
    modify_date: str  # Consider using datetime for stricter typing
    file_size: str  # Consider using int for stricter typing
    file_row_count: str  # Consider using int for stricter typing
    status: str
    rejection_reason: Optional[str] = None
    file_web_url: Optional[str] = None

    def to_json(self) -> str:
        """
        Convert the metadata instance to a JSON-formatted string.

        Serialize all metadata fields into a human-readable JSON string for
        logging, transmission, or storage.

        Returns
        -------
        str
            JSON representation of the metadata.
        """
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


# eof
