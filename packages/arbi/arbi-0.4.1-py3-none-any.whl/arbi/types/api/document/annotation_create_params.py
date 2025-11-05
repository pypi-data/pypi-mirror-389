# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Annotated, TypedDict

from ...._utils import PropertyInfo

__all__ = ["AnnotationCreateParams"]


class AnnotationCreateParams(TypedDict, total=False):
    note: Optional[str]

    page_ref: Optional[int]

    tag_name: Optional[str]

    workspace_key: Annotated[str, PropertyInfo(alias="workspace-key")]
