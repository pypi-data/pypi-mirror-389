# email_system/factory/provider_factory.py

from email_manager.providers.mailgun_provider import MailgunProvider
from email_manager.providers.smtp_provider import SMTPProvider
from email_manager.providers.mailtrap_provider import MailtrapProvider


class ProviderFactory:
    _provider_map = {
        "mailgun": lambda config: MailgunProvider(mailgun_params=config.mailgun_params, config=config),
        "smtp": lambda config: SMTPProvider(smtp_params=config.smtp_params, config=config),
        "mailtrap": lambda config: MailtrapProvider(mailtrap_params=config.mailtrap_params, config=config)
    }

    def create_provider(config, override=None):
        provider_key = (override or config.provider_type).lower()
        try:
            return ProviderFactory._provider_map[provider_key](config)
        except KeyError:
            raise ValueError(f"Unsupported provider type: {provider_key}")
        except Exception as e:
            raise RuntimeError(f"Error creating provider '{provider_key}': {e}")
