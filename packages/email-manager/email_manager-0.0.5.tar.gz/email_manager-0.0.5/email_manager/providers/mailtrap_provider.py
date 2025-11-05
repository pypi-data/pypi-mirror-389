from email import encoders
from email.mime.base import MIMEBase
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email_manager.providers.base import BaseEmailProvider


class MailtrapProvider(BaseEmailProvider):
    def __init__(self, mailtrap_params: dict, config):
        self.host = mailtrap_params["host"]
        self.port = mailtrap_params["port"]
        self.password = mailtrap_params["psw"]
        self.from_email = mailtrap_params["from_email"]
        self.timeout = config.timeout

    def send_email(self, to: str, subject: str, body: str, bcc: str, attachments: list, **kwargs) -> bool:
        try:
            if isinstance(to, str):
                to = [i.strip() for i in to.split(',') if i.strip()]

            msg = MIMEMultipart()
            msg["From"] = self.from_email
            msg["To"] = ", ".join(to)
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "html"))

            context = ssl.create_default_context()
            with smtplib.SMTP(self.host, self.port, timeout=self.timeout) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(self.from_email, self.password)
                to += bcc
                if attachments:
                    for attachment in attachments:
                        part = MIMEBase('application', 'octet-stream')
                        with open(attachment, 'rb') as f:
                            part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', 'attachment',
                                        filename=attachment.split('/')[-1])
                        msg.attach(part)
                server.sendmail(self.from_email, to, msg.as_string())

            return True
        except Exception as e:
            self._handle_error(e)
            return False

    def send_bulk_email(self, recipients: list, subject: str, body: str) -> dict:
        return {recipient: self.send_email(recipient, subject, body) for recipient in recipients}

    def _handle_error(self, error: Exception):
        print(f"[Mailtrap Error] {error}")

    def get_provider_name(self) -> str:
        return "MailtrapProvider"