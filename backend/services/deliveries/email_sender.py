from __future__ import annotations

from email.message import EmailMessage
import smtplib
import ssl

from backend.core.config import settings


class EmailSender:
    def send_many(
        self,
        *,
        recipient: str,
        listings: list[tuple[str, str, float | None]],
    ) -> None:
        if not settings.SMTP_HOST or not settings.SMTP_FROM:
            raise RuntimeError("SMTP is not configured")
        if not listings:
            raise RuntimeError("No listings to send")

        message = EmailMessage()
        message["Subject"] = "New listings found"
        message["From"] = settings.SMTP_FROM
        message["To"] = recipient
        lines = ["New apartments were found for your filters:", ""]
        for index, (title, url, price) in enumerate(listings, start=1):
            lines.append(f"{index}. {title}")
            lines.append(f"   {url}")
            lines.append(f"   Price: {price}")
            lines.append("")
        message.set_content("\n".join(lines))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
            smtp.ehlo()
            if settings.SMTP_USE_TLS:
                smtp.starttls(context=ssl.create_default_context())
                smtp.ehlo()
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            smtp.send_message(message)
