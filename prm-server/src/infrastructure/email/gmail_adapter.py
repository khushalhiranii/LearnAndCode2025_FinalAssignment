import asyncio
import base64
from email.mime.text import MIMEText

from src.domain.exceptions import EmailDeliveryError
from src.domain.ports.email_provider import EmailMessage, IEmailProvider


class GmailEmailProvider(IEmailProvider):
    """Gmail API via GCP service account with domain-wide delegation."""

    def __init__(self, sender: str, service_account_file: str) -> None:
        self._sender = sender
        self._service_account_file = service_account_file

    @property
    def provider_name(self) -> str:
        return "gmail"

    async def send(self, message: EmailMessage) -> None:
        await asyncio.to_thread(self._send_sync, message)

    def _send_sync(self, message: EmailMessage) -> None:
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
        except ImportError as exc:
            raise EmailDeliveryError(
                "Gmail provider requires google-auth and google-api-python-client."
            ) from exc

        scopes = ["https://www.googleapis.com/auth/gmail.send"]
        try:
            credentials = service_account.Credentials.from_service_account_file(
                self._service_account_file,
                scopes=scopes,
            )
            delegated = credentials.with_subject(self._sender)
            service = build("gmail", "v1", credentials=delegated, cache_discovery=False)

            mime = MIMEText(message.html_body, "html")
            mime["to"] = message.to
            mime["from"] = self._sender
            mime["subject"] = message.subject
            raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()
            service.users().messages().send(userId="me", body={"raw": raw}).execute()
        except Exception as exc:
            raise EmailDeliveryError(f"Gmail API send failed: {exc}") from exc
