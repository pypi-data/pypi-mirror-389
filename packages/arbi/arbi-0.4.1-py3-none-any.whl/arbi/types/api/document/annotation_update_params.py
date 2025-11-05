# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Optional
from typing_extensions import Required, Annotated, TypedDict

from ...._utils import PropertyInfo

__all__ = ["AnnotationUpdateParams"]


class AnnotationUpdateParams(TypedDict, total=False):
    doc_ext_id: Required[str]

    note: Optional[str]

    page_ref: Optional[int]

    workspace_key: Annotated[str, PropertyInfo(alias="workspace-key")]
