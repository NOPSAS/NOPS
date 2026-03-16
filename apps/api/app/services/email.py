"""
ByggSjekk / nops.no – E-posttjeneste.

Sender transaksjons-e-poster via SMTP (aiosmtplib).
Maler bruker Jinja2.
"""
from __future__ import annotations

import logging
import secrets
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import aiosmtplib
from jinja2 import Template

logger = logging.getLogger(__name__)


def generer_token(lengde: int = 64) -> str:
    return secrets.token_urlsafe(lengde)


# ── HTML-maler ──────────────────────────────────────────────────────────────

_BASE_HTML = """<!DOCTYPE html>
<html lang="nb">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f8fafc; margin: 0; padding: 20px; }
  .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
  .header { background: linear-gradient(135deg, #2563eb, #4338ca); padding: 32px 40px; }
  .header h1 { color: white; margin: 0; font-size: 24px; font-weight: 700; }
  .header p { color: #bfdbfe; margin: 4px 0 0; font-size: 14px; }
  .body { padding: 40px; }
  .body p { color: #334155; line-height: 1.6; margin: 0 0 16px; }
  .btn { display: inline-block; background: #2563eb; color: white !important; padding: 14px 28px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 15px; margin: 8px 0 24px; }
  .footer { background: #f8fafc; padding: 24px 40px; border-top: 1px solid #e2e8f0; }
  .footer p { color: #94a3b8; font-size: 12px; margin: 0; }
  .token-box { background: #f1f5f9; border-radius: 6px; padding: 12px 16px; font-family: monospace; font-size: 18px; letter-spacing: 4px; color: #1e293b; text-align: center; margin: 16px 0; }
</style>
</head>
<body><div class="container">{{ content }}</div></body>
</html>"""

VERIFISERING_HTML = _BASE_HTML.replace("{{ content }}", """
<div class="header"><h1>nops.no</h1><p>ByggSjekk – Eiendomsintelligens</p></div>
<div class="body">
  <p>Hei {{ navn }},</p>
  <p>Takk for at du registrerte deg på nops.no! Bekreft e-postadressen din for å aktivere kontoen:</p>
  <a href="{{ url }}" class="btn">Bekreft e-postadresse</a>
  <p>Eller kopier denne lenken inn i nettleseren:</p>
  <p style="font-size:12px;color:#94a3b8;word-break:break-all;">{{ url }}</p>
  <p>Lenken er gyldig i 24 timer. Hvis du ikke registrerte deg på nops.no kan du ignorere denne e-posten.</p>
</div>
<div class="footer"><p>© 2026 nops.no – ByggSjekk · Konsepthus AS</p></div>
""")

PASSORD_RESET_HTML = _BASE_HTML.replace("{{ content }}", """
<div class="header"><h1>nops.no</h1><p>ByggSjekk – Tilbakestill passord</p></div>
<div class="body">
  <p>Hei {{ navn }},</p>
  <p>Vi mottok en forespørsel om å tilbakestille passordet for kontoen din.</p>
  <a href="{{ url }}" class="btn">Tilbakestill passord</a>
  <p>Lenken er gyldig i 1 time. Hvis du ikke ba om dette kan du ignorere e-posten.</p>
</div>
<div class="footer"><p>© 2026 nops.no – ByggSjekk · Konsepthus AS</p></div>
""")

VELKOMST_HTML = _BASE_HTML.replace("{{ content }}", """
<div class="header"><h1>Velkommen til nops.no! 🎉</h1><p>ByggSjekk – Eiendomsintelligens</p></div>
<div class="body">
  <p>Hei {{ navn }},</p>
  <p>Kontoen din er nå aktivert. Her er hva du kan gjøre:</p>
  <ul style="color:#334155;line-height:1.8;padding-left:20px;">
    <li>🗺️ <strong>Eiendomsoppslag</strong> – søk opp enhver norsk eiendom</li>
    <li>📋 <strong>Byggesaker</strong> – hent historikk fra kommunalt arkiv</li>
    <li>🤖 <strong>AI-analyse</strong> – risikovurdering med lovhenvisninger</li>
    <li>💰 <strong>Verdiestimator</strong> – estimert markedsverdi</li>
  </ul>
  <a href="{{ dashboard_url }}" class="btn">Gå til dashboard</a>
</div>
<div class="footer"><p>Spørsmål? Svar på denne e-posten eller kontakt oss på support@nops.no</p></div>
""")


async def send_epost(
    til: str,
    emne: str,
    html_innhold: str,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    fra: str = "hey@nops.no",
    fra_navn: str = "nops.no",
) -> bool:
    """Sender en e-post via SMTP. Returnerer True ved suksess."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = emne
    msg["From"] = f"{fra_navn} <{fra}>"
    msg["To"] = til
    msg.attach(MIMEText(html_innhold, "html", "utf-8"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=smtp_host,
            port=smtp_port,
            username=smtp_user,
            password=smtp_password,
            start_tls=True,
        )
        logger.info("E-post sendt til %s: %s", til, emne)
        return True
    except Exception as exc:
        logger.error("E-postsending feilet for %s: %s", til, exc)
        return False


async def send_verifisering(
    til: str,
    navn: str,
    token: str,
    base_url: str,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
) -> bool:
    url = f"{base_url}/verify-email?token={token}"
    html = Template(VERIFISERING_HTML).render(navn=navn.split()[0] if navn else "der", url=url)
    return await send_epost(til, "Bekreft e-postadressen din – nops.no", html, smtp_host, smtp_port, smtp_user, smtp_password)


async def send_passord_reset(
    til: str,
    navn: str,
    token: str,
    base_url: str,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
) -> bool:
    url = f"{base_url}/reset-password?token={token}"
    html = Template(PASSORD_RESET_HTML).render(navn=navn.split()[0] if navn else "der", url=url)
    return await send_epost(til, "Tilbakestill passord – nops.no", html, smtp_host, smtp_port, smtp_user, smtp_password)


async def send_velkomst(
    til: str,
    navn: str,
    base_url: str,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
) -> bool:
    html = Template(VELKOMST_HTML).render(navn=navn.split()[0] if navn else "der", dashboard_url=f"{base_url}/")
    return await send_epost(til, "Velkommen til nops.no! 🎉", html, smtp_host, smtp_port, smtp_user, smtp_password)
