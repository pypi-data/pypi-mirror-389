import aiosmtplib
from email.message import EmailMessage
from pydantic import BaseModel, Field, EmailStr
from asfeslib.core.logger import Logger

logger = Logger(name=__name__)


class MailConfig(BaseModel):
    host: str = Field(default="mail.asfes.ru", description="SMTP-сервер")
    port: int = Field(default=587, description="SMTP-порт (обычно 587 для STARTTLS)")
    username: str = Field(..., description="Имя пользователя (email-адрес)")
    password: str = Field(..., description="Пароль от почтового ящика")
    use_tls: bool = Field(default=True, description="Использовать STARTTLS")
    from_name: str = Field(default="ASFES Mailer", description="Отображаемое имя отправителя")


class MailMessage(BaseModel):
    to: list[EmailStr]
    subject: str
    body: str
    html: bool = False


async def send_mail(cfg: MailConfig, msg: MailMessage) -> bool:
    """
    Асинхронная отправка письма через SMTP (aiosmtplib).
    Возвращает True при успехе.
    """
    email = EmailMessage()
    email["From"] = f"{cfg.from_name} <{cfg.username}>"
    email["To"] = ", ".join(msg.to)
    email["Subject"] = msg.subject
    email.set_content(msg.body, subtype="html" if msg.html else "plain")

    try:
        smtp = aiosmtplib.SMTP(hostname=cfg.host, port=cfg.port, timeout=10)
        await smtp.connect()

        if cfg.use_tls:
            await smtp.starttls()

        await smtp.login(cfg.username, cfg.password)
        await smtp.send_message(email)
        await smtp.quit()

        logger.info(f"Письмо отправлено на {msg.to}")
        return True

    except Exception as e:
        logger.error(f"Ошибка при отправке письма: {e}")
        return False
