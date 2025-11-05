"""FCC - Company Subsidiaries Finder service."""

from ..models.responses import FccResponse
from .base import BaseService


class Fcc(BaseService):
    """
    FCC - Company Subsidiaries Finder API (V2).
    
    Identifies known subsidiaries of a parent company.
    """

    def get_subsidiaries(self, query: str) -> FccResponse:
        """
        Get company subsidiaries.
        
        Args:
            query: Company name to find subsidiaries for
            
        Returns:
            FccResponse: Subsidiaries information
            
        Example:
            ```python
            result = client.fcc("Amazon")
            for subsidiary in result.subsidiaries:
                print(subsidiary)
            ```
        """

        try:
            response = self.client.post("/fcc", {
                "query": query.strip(),
            })

            return FccResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "FCC Service")
