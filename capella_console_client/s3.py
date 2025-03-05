"""Wrapper for cloudpathlib S3Path."""

from __future__ import annotations
from typing import TYPE_CHECKING
from typing_extensions import TypeAlias

if TYPE_CHECKING:
    from cloudpathlib import S3Path as _S3Path

    S3Path: TypeAlias = _S3Path
else:
    try:
        from cloudpathlib import S3Path
    except ImportError:

        class S3Path:
            def __init__(self, *args, **kwargs):
                raise ImportError(
                    "S3Path requires the 'cloudpathlib' package. "
                    "Install it with 'pip install capella-console-client[s3]'."
                )
