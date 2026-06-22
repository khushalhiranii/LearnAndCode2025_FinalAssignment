import asyncio
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.domain.exceptions import EmailDeliveryError
from src.domain.ports.email_provider import EmailMessage, IEmailProvider


class SmtpEmailProvider(IEmailProvider):

    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        password: str,
        from_address: str,
        use_tls: bool = True,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._from = from_address
        self._use_tls = use_tls

    @property
    def provider_name(self) -> str:
        return "smtp"

    async def send(self, message: EmailMessage) -> None:
        await asyncio.to_thread(self._send_sync, message)

    def _send_sync(self, message: EmailMessage) -> None:
        mime = MIMEMultipart("alternative")
        mime["Subject"] = message.subject
        mime["From"] = self._from
        mime["To"] = message.to
        if message.text_body:
            mime.attach(MIMEText(message.text_body, "plain"))
        mime.attach(MIMEText(message.html_body, "html"))
        try:
            with smtplib.SMTP(self._host, self._port, timeout=30) as server:
                if self._use_tls:
                    server.starttls()
                if self._username:
                    server.login(self._username, self._password)
                server.sendmail(self._from, [message.to], mime.as_string())
        except Exception as exc:
            raise EmailDeliveryError(f"SMTP send failed: {exc}") from exc
