"""CLO - Company Locations service."""

from ..models.responses import CloResponse
from .base import BaseService


class Clo(BaseService):
    """
    CLO - Company Locations API (V2).
    
    Returns office locations for a company.
    """

    def get_locations(self, query: str) -> CloResponse:
        """
        Get company locations.
        
        Args:
            query: Company name to get locations for
            
        Returns:
            CloResponse: Company locations information
            
        Example:
            ```python
            result = client.clo("Apple")
            for location in result.locations:
                print(f"{location.city}, {location.state}, {location.country}")
            ```
        """

        try:
            response = self.client.post("/clo", {
                "query": query.strip(),
            })

            return CloResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "CLO Service")
