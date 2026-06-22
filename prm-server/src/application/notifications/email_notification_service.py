from datetime import datetime, timezone

from src.domain.entities.notification import NotificationLog
from src.domain.enums import NotificationType
from src.domain.ports.email_provider import EmailMessage, IEmailProvider
from src.domain.ports.repositories import INotificationRepository


class EmailNotificationService:

    def __init__(
        self,
        email: IEmailProvider,
        notifications: INotificationRepository,
    ) -> None:
        self._email = email
        self._notifications = notifications

    async def send_if_new(
        self,
        notification_type: NotificationType,
        recipient_user_id: int,
        recipient_email: str,
        subject_id: int,
        reference_key: str,
        subject: str,
        html_body: str,
        text_body: str | None = None,
    ) -> bool:
        if not recipient_email:
            return False
        ntype = notification_type.value
        if await self._notifications.was_sent(
            ntype, recipient_user_id, subject_id, reference_key
        ):
            return False
        await self._email.send(
            EmailMessage(
                to=recipient_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
            )
        )
        await self._notifications.record_sent(
            NotificationLog(
                id=None,
                notification_type=ntype,
                recipient_user_id=recipient_user_id,
                subject_id=subject_id,
                reference_key=reference_key,
                provider=self._email.provider_name,
                sent_at=datetime.now(timezone.utc),
            )
        )
        return True
