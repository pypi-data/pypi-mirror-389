# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional
from typing_extensions import Required, TypedDict

__all__ = ["ModalLearnParams"]


class ModalLearnParams(TypedDict, total=False):
    message: Required[Dict[str, object]]
    """Single message to learn from with 'role' and 'content' fields"""

    user_id: Required[str]
    """Unique identifier for the user"""

    datetime_input: Optional[str]
    """ISO format datetime string for the message timestamp"""

    session_id: Optional[str]
    """Optional session identifier for conversation context"""
