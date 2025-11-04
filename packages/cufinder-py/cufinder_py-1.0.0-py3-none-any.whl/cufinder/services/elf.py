"""ELF - Company Fundraising service."""

from ..models.responses import ElfResponse
from .base import BaseService


class Elf(BaseService):
    """
    ELF - Company Fundraising API (V2).
    
    Returns detailed funding information about a company.
    """

    def get_fundraising(self, query: str) -> ElfResponse:
        """
        Get company fundraising information.
        
        Args:
            query: Company name to get fundraising data for
            
        Returns:
            ElfResponse: Fundraising information
            
        Example:
            ```python
            result = client.elf("cufinder")
            print(result.fundraising_info.funding_money_raised)
            print(result.fundraising_info.funding_last_round_type)
            ```
        """

        try:
            response = self.client.post("/elf", {
                "query": query.strip(),
            })

            return ElfResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "ELF Service")
