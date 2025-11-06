from email_manager.providers.base import BaseEmailProvider


class EmailNotificationService:
    """
    Servicio de envío de correos usando un proveedor específico.
    """

    def __init__(self, provider: BaseEmailProvider):
        self.provider = provider
        self.from_email = None
        self.from_name = None

    def send_email(self, to: str, subject: str, body: str, **kwargs) -> bool:
        """
        Envía un correo a un destinatario usando el proveedor configurado.
        """
        return self.provider.send_email(to, subject, body, **kwargs)

    def send_bulk_email(self, recipients: list, subject: str, body: str) -> dict:
        """
        Envía correos a múltiples destinatarios.
        """
        return self.provider.send_bulk_email(recipients, subject, body)

    def validate_email(self, email: str) -> bool:
        """
        Validación básica de formato de correo.
        """
        return "@" in email and "." in email