import smtplib
from email.message import EmailMessage

from app.core.config import settings


def _smtp_send(message: EmailMessage) -> None:
    """Envia uma mensagem via SMTP usando as configurações globais."""
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:  # type: ignore[arg-type]
        if settings.SMTP_USE_TLS:
            smtp.starttls()
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.send_message(message)


def _check_smtp_configured() -> None:
    if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
        raise RuntimeError("Serviço de e-mail não configurado.")


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
    _smtp_send(message)


def send_password_reset_email(to_email: str, reset_url: str) -> None:
    _check_smtp_configured()

    message = EmailMessage()
    message["Subject"] = "Redefinição de senha - Finanças"
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = to_email
    message.set_content(
        (
            "Você solicitou a redefinição de sua senha.\n\n"
            f"Clique no link abaixo para criar uma nova senha (válido por 1 hora):\n{reset_url}\n\n"
            "Se você não solicitou isso, ignore este e-mail — sua senha permanece inalterada."
        )
    )
    _smtp_send(message)
