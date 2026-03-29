import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def send_price_alert(
    to_email: str,
    product_name: str,
    product_url: str,
    current_price: float,
    alert_price: float,
    change_pct: float | None = None,
):
    """Send email alert when a product drops below the target price."""
    if not settings.smtp_user or not settings.smtp_password:
        logger.warning("[alerts] SMTP not configured, skipping email alert")
        logger.info(
            f"[ALERT] {product_name} → ${current_price} "
            f"(target was ${alert_price})"
        )
        return

    subject = f"🔔 Price Alert: {product_name} bajó a ${current_price:,.0f}"
    change_text = f" ({change_pct:+.1f}%)" if change_pct is not None else ""

    html_body = f"""
    <html><body style="font-family:Arial,sans-serif;background:#f4f4f4;padding:20px;">
      <div style="max-width:560px;margin:0 auto;background:#fff;border-radius:8px;overflow:hidden;">
        <div style="background:#00e5a0;padding:20px;text-align:center;">
          <h1 style="margin:0;color:#080d14;font-size:20px;">💰 ¡Bajó de precio!</h1>
        </div>
        <div style="padding:24px;">
          <h2 style="color:#111;">{product_name}</h2>
          <p style="font-size:32px;font-weight:bold;color:#00c87a;margin:8px 0;">
            ${current_price:,.0f}{change_text}
          </p>
          <p style="color:#666;">Tu precio objetivo: <strong>${alert_price:,.0f}</strong></p>
          <a href="{product_url}"
             style="display:inline-block;margin-top:16px;padding:12px 24px;
                    background:#00e5a0;color:#080d14;text-decoration:none;
                    border-radius:6px;font-weight:bold;">
            Ver producto →
          </a>
        </div>
        <div style="padding:16px;text-align:center;color:#aaa;font-size:12px;">
          Price Tracker PRO
        </div>
      </div>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = settings.alert_from_email
    msg["To"]      = to_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.alert_from_email, to_email, msg.as_string())
        logger.info(f"[alerts] Email sent to {to_email} for '{product_name}'")
    except Exception as e:
        logger.error(f"[alerts] Failed to send email: {e}")
