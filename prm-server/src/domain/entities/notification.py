from dataclasses import dataclass
from datetime import datetime


@dataclass
class NotificationLog:
    id: int | None
    notification_type: str
    recipient_user_id: int
    subject_id: int
    reference_key: str
    provider: str
    sent_at: datetime


@dataclass
class TimesheetReminderTracking:
    id: int | None
    resource_profile_id: int
    week_start_date: str
    reminder_count: int
    last_reminder_sent_at: datetime | None
