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
    smtp_host: str = "",
    smtp_port: int = 587,
    smtp_user: str = "",
    smtp_password: str = "",
    fra: str = "hey@nops.no",
    fra_navn: str = "nops.no",
) -> bool:
    """Sender e-post via Resend REST API (primær) eller SMTP (fallback)."""
    # Prøv Resend REST API først (fungerer fra cloud-servere der SMTP er blokkert)
    if smtp_password and smtp_password.startswith("re_"):
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {smtp_password}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": f"{fra_navn} <{fra}>",
                        "to": [til],
                        "subject": emne,
                        "html": html_innhold,
                    },
                )
                if resp.status_code in (200, 201):
                    logger.info("E-post sendt via Resend API til %s: %s", til, emne)
                    return True
                else:
                    logger.warning("Resend API feilet: %s %s", resp.status_code, resp.text[:200])
        except Exception as exc:
            logger.warning("Resend API feilet: %s – prøver SMTP", exc)

    # Fallback: SMTP
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
        logger.info("E-post sendt via SMTP til %s: %s", til, emne)
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


# ── Innsynsbegjæring til kommune ─────────────────────────────────────────────

# Kjente kommune-e-postadresser for byggesak/postmottak
KOMMUNE_EPOST: dict[str, str] = {
    "3212": "post@nesodden.kommune.no",
    "3205": "postmottak@lillestrom.kommune.no",
    "0301": "postmottak@oslo.kommune.no",
    "3201": "post@baerum.kommune.no",
    "3203": "postmottak@asker.kommune.no",
    "3207": "postmottak@nordrefollo.kommune.no",
    "3218": "postmottak@as.kommune.no",
    "3214": "post@frogn.kommune.no",
    "3216": "post@vestby.kommune.no",
    "3220": "postmottak@drammen.kommune.no",
    "3301": "postmottak@sandefjord.kommune.no",
    "3303": "postmottak@larvik.kommune.no",
    "4601": "postmottak@bergen.kommune.no",
    "5001": "postmottak@trondheim.kommune.no",
    "5401": "postmottak@tromso.kommune.no",
    "1103": "postmottak@stavanger.kommune.no",
    "1106": "postmottak@sandnes.kommune.no",
    "4204": "postmottak@kristiansand.kommune.no",
    "1505": "postmottak@kristiansund.kommune.no",
    "3024": "postmottak@fredrikstad.kommune.no",
    "3025": "postmottak@halden.kommune.no",
    "3030": "postmottak@sarpsborg.kommune.no",
    "3005": "postmottak@drammen.kommune.no",
}


def hent_kommune_epost(kommunenummer: str, kommunenavn: str = "") -> str:
    """Henter kjent e-postadresse for kommunen, eller genererer en basert på mønster."""
    if kommunenummer in KOMMUNE_EPOST:
        return KOMMUNE_EPOST[kommunenummer]
    # De fleste norske kommuner følger mønsteret post@kommune.kommune.no
    # eller postmottak@kommune.kommune.no
    if kommunenavn:
        slugified = kommunenavn.lower().replace("ø", "o").replace("æ", "ae").replace("å", "a").replace(" ", "")
        return f"postmottak@{slugified}.kommune.no"
    return ""


INNSYN_TEGNINGER_HTML = _BASE_HTML.replace("{{ content }}", """
<div class="header"><h1>nops.no</h1><p>Innsynsbegjæring – Godkjente byggetegninger</p></div>
<div class="body">
  <p>Til {{ kommunenavn }} kommune,</p>
  <p>I forbindelse med potensielt søknadspliktige tiltak for eiendommen <strong>{{ adresse }}</strong>,
  på <strong>{{ gnr }}/{{ bnr }}</strong> i {{ kommunenavn }} kommune (kommunenr. {{ knr }}),
  ber vi om innsyn (jf. Grunnloven § 100 og offentleglova § 3) i følgende dokumenter:</p>
  <ul style="color:#334155;line-height:1.8;padding-left:20px;">
    <li>Sist godkjente situasjonskart</li>
    <li>Sist godkjente plantegninger</li>
    <li>Sist godkjente fasadetegninger</li>
    <li>Sist godkjente snitt-tegninger</li>
    <li>Tilhørende byggesaksdokumenter</li>
  </ul>
  <p>Vi ber om at dokumentene sendes digitalt til <strong>{{ svar_epost }}</strong>.</p>
  <p>Med vennlig hilsen,<br>
  <strong>{{ bruker_navn }}</strong><br>
  på vegne av eier/tiltakshaver<br><br>
  <em>Sendt via nops.no – Norges ledende plattform for digitale eiendomstjenester</em></p>
</div>
<div class="footer">
  <p>nops.no · Konsepthus AS · hey@nops.no</p>
</div>
""")


async def send_innsynsbegjæring_tegninger(
    kommune_epost: str,
    kommunenavn: str,
    knr: str,
    gnr: int,
    bnr: int,
    adresse: str,
    bruker_navn: str,
    svar_epost: str,
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
) -> bool:
    """Sender innsynsbegjæring for godkjente tegninger til kommunen."""
    html = Template(INNSYN_TEGNINGER_HTML).render(
        kommunenavn=kommunenavn,
        knr=knr,
        gnr=gnr,
        bnr=bnr,
        adresse=adresse,
        bruker_navn=bruker_navn,
        svar_epost=svar_epost,
    )
    emne = f"Innsynsbegjæring – Godkjente tegninger for {adresse} ({gnr}/{bnr})"
    return await send_epost(
        til=kommune_epost,
        emne=emne,
        html_innhold=html,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_user=smtp_user,
        smtp_password=smtp_password,
    )
