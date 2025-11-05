"""DTE - Company Email Finder service."""

from ..models.responses import DteResponse
from .base import BaseService


class Dte(BaseService):
    """
    DTE - Company Email Finder API (V2).
    
    Returns up to five general or role-based business email addresses for a company.
    """

    def get_emails(self, company_website: str) -> DteResponse:
        """
        Get company emails from domain.
        
        Args:
            company_website: The website URL to find emails for
            
        Returns:
            DteResponse: Company email information
            
        Example:
            ```python
            result = client.dte("stripe.com")
            print(result.emails)  # ['contact@stripe.com', 'info@stripe.com']
            ```
        """
        try:
            response = self.client.post("/dte", {
                "company_website": company_website.strip(),
            })

            return DteResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "DTE Service")


__all__ = ["Dte"]
