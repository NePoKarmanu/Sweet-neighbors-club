from __future__ import annotations

from email.message import EmailMessage
import smtplib
import ssl

from backend.core.config import settings


class EmailSender:
    def send(self, *, recipient: str, title: str, url: str, price: float | None) -> None:
        if not settings.SMTP_HOST or not settings.SMTP_FROM:
            raise RuntimeError("SMTP is not configured")

        message = EmailMessage()
        message["Subject"] = f"New listing: {title}"
        message["From"] = settings.SMTP_FROM
        message["To"] = recipient
        message.set_content(f"{title}\n{url}\nPrice: {price}")

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
            smtp.ehlo()
            if settings.SMTP_USE_TLS:
                smtp.starttls(context=ssl.create_default_context())
                smtp.ehlo()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            smtp.send_message(message)
