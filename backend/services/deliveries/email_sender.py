from __future__ import annotations

from email.message import EmailMessage
import logging
import smtplib
import ssl

from backend.core.config import settings
from backend.logging_utils import log_exception, log_info

logger = logging.getLogger(__name__)


class EmailSender:
    def send_many(
        self,
        *,
        recipient: str,
        listings: list[tuple[str, str, float | None]],
        user_id: int | None = None,
    ) -> None:
        log_info(
            logger, "Email send attempt started", event="notifications.email_send_attempt",
            channel="email", user_id=user_id, listings_count=len(listings)
        )
        try:
            if not settings.SMTP_HOST or not settings.SMTP_FROM:
                raise RuntimeError("SMTP is not configured")
            if not listings:
                raise RuntimeError("No listings to send")

            message = EmailMessage()
            message["Subject"] = "РќРѕРІС‹Рµ РѕР±СЉСЏРІР»РµРЅРёСЏ РґР»СЏ Р’Р°СЃ!"
            message["From"] = settings.SMTP_FROM
            message["To"] = recipient
            lines = ["РќРѕРІС‹Рµ РѕР±СЉРµРєС‚С‹ Р±С‹Р»Рё РЅР°Р№РґРµРЅС‹ РїРѕ РІР°С€РёРј С„РёР»СЊС‚СЂР°Рј:", ""]
            for index, (title, url, price) in enumerate(listings, start=1):
                lines.append(f"{index}. {title}")
                lines.append(f"   {url}")
                lines.append(f"   Р¦РµРЅР°: {price}")
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

            log_info(
                logger, "Email send attempt succeeded", event="notifications.email_send_success",
                channel="email", user_id=user_id, listings_count=len(listings)
            )
        except Exception:
            log_exception(
                logger, "Email send attempt failed", event="notifications.email_send_failed",
                channel="email", user_id=user_id
            )
            raise
