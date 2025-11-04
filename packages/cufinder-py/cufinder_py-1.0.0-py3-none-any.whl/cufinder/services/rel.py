"""REL - Reverse Email Lookup service."""


from ..models.responses import RelResponse
from .base import BaseService


class Rel(BaseService):
    """
    REL - Reverse Email Lookup API (V2).
    
    Enriches an email address with detailed person and company information.
    """

    def reverse_email_lookup(self, email: str) -> RelResponse:
        """
        Reverse email lookup.
        
        Args:
            email: The email address to lookup
            
        Returns:
            RelResponse: Person and company information
            
        Example:
            ```python
            result = client.rel("john.doe@example.com")
            print(result.person.full_name)  # 'John Doe'
            print(result.person.company_name)  # 'Example Corp'
            ```
        """


        try:
            response = self.client.post("/rel", {
                "email": email.strip(),
            })

            return RelResponse.from_dict(self.parse_response_data(response))
        except Exception as error:
            raise self.handle_error(error, "REL Service")
