import smtplib
from email.message import EmailMessage

from app.core.config import settings


def send_invitation_email(to_email: str, owner_nome: str, invite_link: str) -> None:
    if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
        raise RuntimeError("Serviço de e-mail não configurado.")

    message = EmailMessage()
    message["Subject"] = "Convite para acesso compartilhado - Finanças"
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = to_email
    message.set_content(
        (
            f"{owner_nome} convidou você para acessar os dados financeiros compartilhados.\n\n"
            f"Confirme o convite neste link:\n{invite_link}\n\n"
            "Se você ainda não possui conta, o link também permitirá concluir seu cadastro."
        )
    )

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
        if settings.SMTP_USE_TLS:
            smtp.starttls()
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.send_message(message)
