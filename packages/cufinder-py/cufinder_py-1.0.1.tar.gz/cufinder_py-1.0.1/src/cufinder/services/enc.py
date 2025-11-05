"""ENC - Company Enrichment service."""

from ..models.responses import EncResponse
from .base import BaseService


class Enc(BaseService):
    """
    ENC - Company Enrichment API (V2).
    
    Enriches company information from various data sources.
    """

    def enrich_company(self, query: str) -> EncResponse:
        """
        Enrich company information.
        
        Args:
            query: Company name or domain to enrich
            
        Returns:
            EncResponse: Enriched company information
            
        Example:
            ```python
            result = client.enc("cufinder")
            print(result.company.name)  # 'CUFinder'
            print(result.company.industry)  # 'Technology'
            ```
        """

        try:
            response = self.client.post("/enc", {
                "query": query.strip(),
            })

            return EncResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "ENC Service")
