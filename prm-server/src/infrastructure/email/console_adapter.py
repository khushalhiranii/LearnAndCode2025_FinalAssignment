import structlog

from src.domain.ports.email_provider import EmailMessage, IEmailProvider

log = structlog.get_logger()


class ConsoleEmailProvider(IEmailProvider):

    @property
    def provider_name(self) -> str:
        return "console"

    async def send(self, message: EmailMessage) -> None:
        log.info(
            "email_console",
            to=message.to,
            subject=message.subject,
            html_body=message.html_body,
            text_body=message.text_body,
        )
