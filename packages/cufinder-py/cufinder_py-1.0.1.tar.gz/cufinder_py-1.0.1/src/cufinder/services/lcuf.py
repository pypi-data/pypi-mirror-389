"""LCUF - LinkedIn Company URL Finder service."""

from ..models.responses import LcufResponse
from .base import BaseService


class Lcuf(BaseService):
    """
    LCUF - LinkedIn Company URL Finder API (V2).
    
    Finds LinkedIn company URLs from company names.
    """

    def get_linkedin_url(self, company_name: str) -> LcufResponse:
        """
        Get LinkedIn URL from company name.
        
        Args:
            company_name: The name of the company to find LinkedIn URL for
            
        Returns:
            LcufResponse: LinkedIn URL information
            
        Example:
            ```python
            result = client.lcuf("cufinder")
            print(result.linkedin_url)  # 'https://linkedin.com/company/cufinder'
            ```
        """

        try:
            response = self.client.post("/lcuf", {
                "company_name": company_name.strip(),
            })

            return LcufResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "LCUF Service")
