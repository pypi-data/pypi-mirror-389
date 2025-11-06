import resend
from mosayic.logger import get_logger
from mosayic.services.email.email_templates import welcome_email_template

logger = get_logger(__name__)


class ResendService:

    def __init__(self, resend_api_key):
        resend.api_key = resend_api_key
        self.params = resend.Emails.SendParams()

    # async def send_welcome_email(self, recipient, sender, verification_link: str | None) -> dict:
    #     logger.info("Sending welcome recipient_email to %s...",  recipient.email)
    #     self.params['to'] = recipient.email
    #     self.params['from'] = f"{sender_name } <{self.settings.from_email}>"
    #     self.params['subject'] = f'Welcome to {self.settings.app_title}'
    #     self.params['html'] = welcome_email_template(recipient, self.settings, verification_link)
    #     if self.params['to'] and self.params['from'] and self.params['subject'] and self.params['html']:
    #         response = resend.Emails.send(self.params)
    #         logger.info("The welcome email has been sent to: %s",  recipient.email)
    #         return response
    #     logger.error("Email not sent. Missing parameters: %s", self.params)
