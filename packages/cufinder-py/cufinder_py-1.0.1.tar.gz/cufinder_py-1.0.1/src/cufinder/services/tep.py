"""TEP - Person Enrichment service."""

from ..models.responses import TepResponse
from .base import BaseService


class Tep(BaseService):
    """
    TEP - Person Enrichment API (V2).
    
    Enriches person information from various data sources.
    """

    def enrich_person(self, full_name: str, company: str) -> TepResponse:
        """
        Enrich person information.
        
        Args:
            full_name: Full name of the person to enrich
            company: Company name where the person works
            
        Returns:
            TepResponse: Enriched person information
            
        Example:
            ```python
            result = client.tep("John Doe", "Stripe")
            print(result.person.full_name)  # 'John Doe'
            print(result.person.email)  # Work email
            ```
        """

        try:
            response = self.client.post("/tep", {
                "full_name": full_name.strip(),
                "company": company.strip(),
            })

            return TepResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "TEP Service")
