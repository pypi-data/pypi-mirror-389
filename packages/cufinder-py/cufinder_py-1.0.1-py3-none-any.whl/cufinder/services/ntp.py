"""NTP - Company Phone Finder service."""

from ..models.responses import NtpResponse
from .base import BaseService


class Ntp(BaseService):
    """
    NTP - Company Phone Finder API (V2).
    
    Returns up to two verified phone numbers for a company.
    """

    def get_phones(self, company_name: str) -> NtpResponse:
        """
        Get company phones from company name.
        
        Args:
            company_name: The name of the company to find phones for
            
        Returns:
            NtpResponse: Company phone information
            
        Example:
            ```python
            result = client.ntp("Apple")
            print(result.phones)  # ['+1-408-996-1010']
            ```
        """

        try:
            response = self.client.post("/ntp", {
                "company_name": company_name.strip(),
            })

            return NtpResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "NTP Service")
