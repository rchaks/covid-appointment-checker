import logging
import os
from collections import namedtuple
from datetime import datetime
from enum import Enum

import requests
import typer as typer
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from tqdm import tqdm
from twilio.rest import Client

Message = namedtuple('Message', ['text', 'should_exist'])
SITES = {
    "https://www.hackensackmeridianhealth.org/covid19":
        Message(text="All appointments currently are full.", should_exist=False),

    "http://www.newbridgehealth.pub/BergenCovidVaccine":
        Message(text="The registration is currently closed.", should_exist=False),

    "https://www.evh.org/covid-19-schedule-an-appointment-page/":
        Message(text="All Appointments are currently full", should_exist=False),

    "https://mountainsidehosp.com/covid19vaccine":
        Message(text="APPOINTMENTS REQUESTS AT THE HOSPITAL ARE CURRENTLY FULL.", should_exist=False),

    "https://www.signupgenius.com/go/10c0d44a4ad2ba3fbcf8-sign2":
        Message(
            text=["This sign up has no slots that are currently available.", "NO SLOTS AVAILABLE. SIGN UP IS FULL."],
            should_exist=False),

    "https://vanguardmedgroup.com/news/covid-19-coronavirus-update/":
        Message(
            text="OUR ONLINE VACCINE APPOINTMENT SCHEDULING IS TEMPORARILY CLOSED",
            should_exist=False),

    "https://www.waynetownship.com/33-emergency-messages/537-covid-19-vaccine-appointments.html?highlight=WyJjb3ZpZCIsInZhY2NpbmVzIiwiY292aWQgdmFjY2luZXMiXQ==":
        Message(text="Unfortunately due to the limited supply of COVID Vaccines, all appointments have been scheduled",
                should_exist=False),

    "https://hipaa.jotform.com/210066987888171":
        Message(text="Unfortunately, all appointments are filled at this time due to high demand.",
                should_exist=False),

    "https://vaccines.shoprite.com":
        Message(text="Vaccine appointment schedule is FULL", should_exist=False),

    "https://www.valleyhealth.com/covid-19-vaccine-eligibility":
        Message(text="NO APPOINTMENTS ARE AVAILABLE AT THIS TIME", should_exist=False)
}

RETRY_CONFIGURATION = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])


class WebsiteChecker:
    def __init__(self):
        self.session = requests.Session()
        retries = RETRY_CONFIGURATION
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        self.session.headers = {
            # Some websites seem to check for a user agent and block requests if it's missing, so we add one
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:85.0) Gecko/20100101 Firefox/85.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'

        }

    def check_contents(self, url: str, message: Message) -> bool:
        response = self.session.get(url, allow_redirects=True)

        response.raise_for_status()
        if message.should_exist:
            if isinstance(message.text, list):
                return any(text in response.text for text in message.text)
            else:
                return message.text in response.text
        else:
            if isinstance(message.text, list):
                return all(text in response.text for text in message.text)
            else:
                return message.text not in response.text


class NotificationType(Enum):
    NONE = 'none'
    SMS = 'sms'


def send_sms(msg: str, to_phone: str):
    # Find these values at https://twilio.com/user/account
    # To set up environmental variables, see http://twil.io/secure
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    twilio_number = os.environ['TWILIO_NUMBER']

    client = Client(account_sid, auth_token)
    if not to_phone.startswith('+1'):
        logging.warning(f'Adding country code (+1) to {to_phone}')
        to_phone = f"+1{to_phone}"
    client.api.account.messages.create(to=to_phone, from_=twilio_number, body=msg)


def main(notification_type: NotificationType = typer.Option(default=NotificationType.NONE.value),
         recipient: str = typer.Option(..., help='recipient\'s phone number'),
         loglevel: str = typer.Option('INFO', help='log level')):
    logging.basicConfig(level=loglevel)

    logging.info('Starting Script')
    website_checker = WebsiteChecker()
    num_matched = 0
    num_checked = 0
    for url, message in tqdm(SITES.items()):
        num_checked += 1
        logging.debug(f'Checking {url}')
        if website_checker.check_contents(url=url, message=message):
            num_matched += 1
            logging.info(f'Hallelujah!! Rule <{message}> matched for site {url}!!')

            current_date = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            message = f"Subject: Covid Vaccine Appointment Availability {current_date}"
            message += f"\nAvailability at {url}"
            if notification_type == NotificationType.SMS:
                send_sms(msg=message, to_phone=recipient)
            elif notification_type == NotificationType.NONE:
                logging.info(f"Skipping notification. Would've sent the following message:\n{message}")
            else:
                raise NotImplementedError(f'Unsupported notification type: {notification_type}')
        else:
            logging.debug(f'No dice')

    logging.info(f'Finished checking {num_checked} sites. {num_matched} of them look promising.')


if __name__ == '__main__':
    typer.run(main)
