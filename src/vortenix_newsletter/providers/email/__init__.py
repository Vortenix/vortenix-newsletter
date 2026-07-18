from .console_provider import ConsoleEmailProvider
from .factory import configured_recipients, create_email_provider, newsletter_recipients

__all__=[
    "ConsoleEmailProvider",
    "configured_recipients",
    "create_email_provider",
    "newsletter_recipients",
]
