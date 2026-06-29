"""Envoi d'email via SMTP generique (compatible OVH ssl0.ovh.net)."""
from __future__ import annotations

import logging
import os
import smtplib
import ssl
from email.message import EmailMessage

log = logging.getLogger(__name__)


class MailConfigError(RuntimeError):
    pass


def _env(name: str, default: str = "") -> str:
    """Comme os.environ.get mais traite une valeur vide comme absente (secrets vides)."""
    val = os.environ.get(name)
    return val if val else default


def _cfg() -> dict[str, str]:
    host = _env("SMTP_HOST", "ssl0.ovh.net")
    port = _env("SMTP_PORT", "587")
    security = _env("SMTP_SECURITY", "starttls").lower()
    user = _env("SMTP_USER", "noreply@whitetelecom.fr")
    password = _env("SMTP_PASSWORD")
    mail_from = _env("MAIL_FROM", user)
    mail_to = _env("MAIL_TO", "Auger939@gmail.com")
    missing = [k for k, v in {"SMTP_USER": user, "SMTP_PASSWORD": password}.items() if not v]
    if missing:
        raise MailConfigError(
            "Configuration SMTP incomplete, variables manquantes : " + ", ".join(missing)
        )
    return {
        "host": host,
        "port": port,
        "security": security,
        "user": user,
        "password": password,
        "from": mail_from,
        "to": mail_to,
    }


def send_email(subject: str, body: str, html: str | None = None) -> None:
    """Envoie un email. Leve une exception en cas d'echec (loggee par l'appelant)."""
    c = _cfg()
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = c["from"]
    msg["To"] = c["to"]
    msg.set_content(body)
    if html:
        msg.add_alternative(html, subtype="html")

    port = int(c["port"])
    security = c["security"]
    context = ssl.create_default_context()

    log.info("Envoi mail -> %s via %s:%s (%s)", c["to"], c["host"], port, security)
    if security == "ssl":
        with smtplib.SMTP_SSL(c["host"], port, context=context, timeout=30) as server:
            server.login(c["user"], c["password"])
            server.send_message(msg)
    else:
        with smtplib.SMTP(c["host"], port, timeout=30) as server:
            server.ehlo()
            if security == "starttls":
                server.starttls(context=context)
                server.ehlo()
            server.login(c["user"], c["password"])
            server.send_message(msg)
    log.info("Mail envoye.")


def send_stock_alert(product_name: str, url: str, detail: str, stores: list[str]) -> None:
    """Construit et envoie l'alerte de disponibilite."""
    subject = f"[STOCK] {product_name} est DISPONIBLE !"
    lines = [
        "Bonne nouvelle, un produit suivi est disponible :",
        "",
        f"Produit : {product_name}",
        f"Detail  : {detail}",
    ]
    if stores:
        lines.append(f"Magasin(s) : {', '.join(stores)}")
    lines += ["", f"Lien : {url}", "", "-- Scraper Clim Portable"]
    body = "\n".join(lines)

    stores_html = (
        f"<p><b>Magasin(s) :</b> {', '.join(stores)}</p>" if stores else ""
    )
    html = (
        f"<h2>Produit disponible !</h2>"
        f"<p><b>{product_name}</b></p>"
        f"<p>{detail}</p>"
        f"{stores_html}"
        f'<p><a href="{url}">Voir le produit</a></p>'
        f"<hr><p style='color:#888'>Scraper Clim Portable</p>"
    )
    send_email(subject, body, html)
