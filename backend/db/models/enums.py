import enum


class NotificationChannel(str, enum.Enum):
    email = "email"
    push = "push"


class DeliveryStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"