from abc import ABC, abstractmethod


class LLMProvider(ABC):

    @abstractmethod
    def generate_reply(
        self,
        skill_text: str,
        customer_email: str,
    ) -> str:
        """
        Generate a foreign-trade reply analysis using the supplied
        skill rules and customer email content.

        This method returns text only.

        It must not send email or perform external communication.
        """
        raise NotImplementedError