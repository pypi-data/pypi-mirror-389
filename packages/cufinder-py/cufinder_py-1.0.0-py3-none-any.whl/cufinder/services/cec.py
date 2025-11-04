"""CEC - Company Employee Countries service."""

from ..models.responses import CecResponse
from .base import BaseService


class Cec(BaseService):
    """
    CEC - Company Employee Countries API (V2).
    
    Returns countries where a company has employees.
    """

    def get_employee_countries(self, query: str) -> CecResponse:
        """
        Get company employee countries.
        
        Args:
            query: Company name to get employee countries for
            
        Returns:
            CecResponse: Employee countries information
            
        Example:
            ```python
            result = client.cec("cufinder")
            print(result.countries)  # Country distribution data
            ```
        """

        try:
            response = self.client.post("/cec", {
                "query": query.strip(),
            })

            return CecResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "CEC Service")
