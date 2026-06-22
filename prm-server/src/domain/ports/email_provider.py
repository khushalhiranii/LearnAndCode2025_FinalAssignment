from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class EmailMessage:
    to: str
    subject: str
    html_body: str
    text_body: str | None = None


class IEmailProvider(ABC):

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    async def send(self, message: EmailMessage) -> None: ...
