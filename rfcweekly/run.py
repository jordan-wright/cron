import json
import os

from datetime import date
from sources import PROVIDERS
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Asm

CACHE_DIR = './.cache'


def fetch_rfcs():
    rfcs = []
    for provider_cls in PROVIDERS:
        provider = provider_cls(CACHE_DIR)
        rfcs.extend(provider.fetch())
    return rfcs

def fetch_contacts(client):
    # For now, we're just using the /marketing/contacts endpoint which has
    # the downside that it only returns the latest 50 contacts.
    #
    # Unfortunately, there isn't a clearcut way to get all the contacts for
    # a particular list using something like a paginated endpoint.
    #
    # Instead, we would need to export the contacts, poll for completion,
    # download the response, and gunzip it. Doable, but gross.
    #
    # ...50 contacts is fine for my purposes.
    # response = client.marketing.contacts.get()
    # contacts = [contact['email'] for contact in response['result']]
    return [os.environ.get('RFCWEEKLY_SENDGRID_TO_ADDRESS')]

def main():
    mailer = SendGridAPIClient(
        api_key=os.environ.get('RFCWEEKLY_SENDGRID_API_KEY'))
    week = date.today().strftime('%B %d')
    rfcs = fetch_rfcs()
    if not rfcs:
        print('No RFCS for the week of {}'.format(week))
        return
    contacts = fetch_contacts(mailer.client)
    # print('Sending emails to {} contacts')
    # for recipient in contacts:
    #     print('Sending email to {}'.format(recipient))
    mail = Mail(from_email=os.environ.get('RFCWEEKLY_SENDGRID_FROM_ADDRESS'),
                to_emails=contacts)
    mail.dynamic_template_data = {'week': week, 'rfcs': rfcs}
    mail.template_id = os.environ.get('RFCWEEKLY_SENDGRID_TEMPLATE_ID')
    mail.asm = Asm(group_id=os.environ.get('RFCWEEKLY_SENDGRID_GROUP'))
    try:
        mailer.send(mail)
        print('{} new RFCs sent for the week of {}'.format(len(rfcs), week))
    except Exception as e:
        print(e.to_dict)


if __name__ == '__main__':
    main()
