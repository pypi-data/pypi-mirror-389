"""CAR - Company Revenue Finder service."""

from ..models.responses import CarResponse
from .base import BaseService


class Car(BaseService):
    """
    CAR - Company Revenue Finder API (V2).
    
    Estimates a company's annual revenue based on name.
    """

    def get_revenue(self, query: str) -> CarResponse:
        """
        Get company revenue.
        
        Args:
            query: Company name to get revenue data for
            
        Returns:
            CarResponse: Revenue information
            
        Example:
            ```python
            result = client.car("Apple")
            print(result.annual_revenue)  # '$100M - $500M'
            ```
        """

        try:
            response = self.client.post("/car", {
                "query": query.strip(),
            })

            return CarResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "CAR Service")
