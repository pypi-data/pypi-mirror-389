"""DTC - Domain to Company Name service."""

from ..models.responses import DtcResponse
from .base import BaseService


class Dtc(BaseService):
    """
    DTC - Domain to Company Name API (V2).
    
    Retrieves the registered company name associated with a given website domain.
    """

    def get_company_name(self, company_website: str) -> DtcResponse:
        """
        Get company name from domain.
        
        Args:
            company_website: The website URL to lookup
            
        Returns:
            DtcResponse: Company name information
            
        Example:
            ```python
            result = client.dtc("stripe.com")
            print(result.company_name)  # 'Stripe'
            ```
        """
        try:
            response = self.client.post("/dtc", {
                "company_website": company_website.strip(),
            })

            return DtcResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "DTC Service")
