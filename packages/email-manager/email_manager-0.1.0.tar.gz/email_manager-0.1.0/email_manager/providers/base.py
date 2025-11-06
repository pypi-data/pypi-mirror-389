from abc import ABC, abstractmethod

class BaseEmailProvider(ABC):
    """
    Clase base abstracta para proveedores de envío de correo.
    Todos los proveedores deben implementar estos métodos.
    """

    @abstractmethod
    def send_email(self, to: str, subject: str, body: str, **kwargs) -> bool:
        """
        Envía un correo electrónico a un destinatario.
        """
        pass

    @abstractmethod
    def send_bulk_email(self, recipients: list, subject: str, body: str) -> dict:
        """
        Envía correos electrónicos a múltiples destinatarios.
        Retorna un diccionario con el estado por destinatario.
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Retorna el nombre del proveedor (para logging o identificación).
        """
        pass