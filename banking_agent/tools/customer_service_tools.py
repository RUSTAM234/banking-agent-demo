from langchain_core.tools import tool
import logging

LOGGER = logging.getLogger(__name__)


@tool
def customer_service() -> str:
    """Return dummy customer-care information for this learning project."""
    LOGGER.info("TOOL customer_service")
    return "Customer Care: 1800-000-0000\nThis is a demo number for this learning project."
