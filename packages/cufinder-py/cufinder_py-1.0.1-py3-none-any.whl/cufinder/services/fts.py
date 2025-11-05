"""FTS - Company Tech Stack Finder service."""

from ..models.responses import FtsResponse
from .base import BaseService


class Fts(BaseService):
    """
    FTS - Company Tech Stack Finder API (V2).
    
    Returns technology stack information for a company.
    """

    def get_tech_stack(self, query: str) -> FtsResponse:
        """
        Get company tech stack.
        
        Args:
            query: Company name or website to get tech stack for
            
        Returns:
            FtsResponse: Technology stack information
            
        Example:
            ```python
            result = client.fts("stripe.com")
            for tech in result.technologies:
                print(tech)
            ```
        """

        try:
            response = self.client.post("/fts", {
                "query": query.strip(),
            })

            return FtsResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "FTS Service")
