"""CUF - Company URL Finder service."""

from ..models.responses import CufResponse
from .base import BaseService


class Cuf(BaseService):
    """
    CUF - Company Name to Domain API.
    
    Returns the official website URL of a company based on its name.
    """

    def get_domain(
        self,
        company_name: str,
        country_code: str,
    ) -> CufResponse:
        """
        Get company domain from company name.
        
        Args:
            company_name: The name of the company to find the domain for
            country_code: The 2-letter ISO country code (e.g., 'US', 'GB')
            
        Returns:
            CufResponse: Company domain information
            
        Raises:
            ValidationError: If parameters are invalid
            AuthenticationError: If API key is invalid
            CreditLimitError: If not enough credits
            NotFoundError: If company not found
            NetworkError: If network issues occur
            
        Example:
            ```python
            result = client.cuf("Apple Inc", "US")
            print(result.domain)  # 'apple.com'
            print(result.query)   # Original query
            print(result.credit_count)  # Credits used
            ```
        """

        try:
            response = self.client.post("/cuf", {
                "company_name": company_name.strip(),
                "country_code": country_code.strip().upper(),
            })

            return CufResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "CUF Service")
