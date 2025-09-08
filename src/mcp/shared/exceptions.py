from mcp.types import ErrorData, ELICITATION_REQUIRED, ElicitRequestParams
from typing import Any


class McpError(Exception):
    """
    Exception type raised when an error arrives over an MCP connection.
    """

    error: ErrorData

    def __init__(self, error: ErrorData):
        """Initialize McpError."""
        super().__init__(error.message)
        self.error = error


class ElicitationRequiredError(McpError):
    """
    Exception raised when a request cannot be processed until an elicitation is completed.
    """

    def __init__(self, elicitations: list[ElicitRequestParams], message: str | None = None):
        """Initialize ElicitationRequiredError."""
        elicitation_data = [elicit.dict() for elicit in elicitations]
        error = ErrorData(
            code=ELICITATION_REQUIRED,
            message=message or f"Elicitation{'s' if len(elicitations) > 1 else ''} required",
            data={"elicitations": elicitation_data}
        )
        super().__init__(error)
        self.elicitations = elicitations
