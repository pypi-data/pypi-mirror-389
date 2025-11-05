"""FCL - Company Lookalikes Finder service."""

from ..models.responses import FclResponse
from .base import BaseService


class Fcl(BaseService):
    """
    FCL - Company Lookalikes Finder API (V2).
    
    Provides a list of similar companies based on an input company's profile.
    """

    def get_lookalikes(self, query: str) -> FclResponse:
        """
        Get company lookalikes.
        
        Args:
            query: Company name or description to find similar companies for
            
        Returns:
            FclResponse: List of similar companies
            
        Example:
            ```python
            result = client.fcl("Apple")
            for company in result.companies:
                print(f"{company.name} - {company.industry}")
            ```
        """

        try:
            response = self.client.post("/fcl", {
                "query": query.strip(),
            })

            return FclResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "FCL Service")
