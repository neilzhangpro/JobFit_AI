"""Command objects for the Resume bounded context.

Commands represent user intentions for resume operations.
"""

from pydantic import BaseModel


class UploadResumeCommand(BaseModel):
    """Command to upload and parse a new resume."""

    user_id: str
    tenant_id: str
    filename: str
    file_bytes: bytes

    model_config = {"arbitrary_types_allowed": True}
