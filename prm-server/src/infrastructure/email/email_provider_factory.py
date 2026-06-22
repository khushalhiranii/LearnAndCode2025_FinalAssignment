from src.config import settings
from src.domain.exceptions import EmailDeliveryError
from src.domain.ports.email_provider import IEmailProvider
from src.infrastructure.email.console_adapter import ConsoleEmailProvider
from src.infrastructure.email.gmail_adapter import GmailEmailProvider
from src.infrastructure.email.smtp_adapter import SmtpEmailProvider


class EmailProviderFactory:

    @staticmethod
    def create() -> IEmailProvider:
        provider = settings.email_provider.lower()
        if provider == "console":
            return ConsoleEmailProvider()
        if provider == "gmail":
            if not settings.gmail_sender or not settings.gmail_service_account_file:
                raise EmailDeliveryError(
                    "Gmail provider requires GMAIL_SENDER and GMAIL_SERVICE_ACCOUNT_FILE in .env."
                )
            return GmailEmailProvider(
                sender=settings.gmail_sender,
                service_account_file=settings.gmail_service_account_file,
            )
        if provider == "smtp":
            if not settings.smtp_host:
                raise EmailDeliveryError("SMTP provider requires SMTP_HOST in .env.")
            return SmtpEmailProvider(
                host=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_user,
                password=settings.smtp_password,
                from_address=settings.smtp_from or settings.smtp_user,
                use_tls=settings.smtp_use_tls,
            )
        return ConsoleEmailProvider()
