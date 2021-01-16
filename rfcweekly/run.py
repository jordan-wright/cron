import os

from datetime import date
from sources import PROVIDERS, DRAFT_PROVIDERS
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Asm

CACHE_DIR = './.cache'


def fetch_rfcs():
    rfcs = []
    for provider_cls in PROVIDERS:
        provider = provider_cls(CACHE_DIR)
        rfcs.extend(provider.fetch())
    return rfcs


def fetch_drafts():
    drafts = []
    for provider_cls in DRAFT_PROVIDERS:
        provider = provider_cls(CACHE_DIR)
        drafts.extend(provider.fetch())
    return drafts


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
    response = client.marketing.contacts.get()
    return [contact['email'] for contact in response.to_dict['result']]


def send_emails(mailer, rfcs, drafts):
    week = date.today().strftime('%B %d')
    contacts = fetch_contacts(mailer.client)
    for contact in contacts:
        mail = Mail(
            from_email=os.environ.get('RFCWEEKLY_SENDGRID_FROM_ADDRESS'),
            to_emails=contact)
        mail.dynamic_template_data = {
            'week': week,
            'rfcs': rfcs,
            'drafts': drafts
        }
        mail.template_id = os.environ.get('RFCWEEKLY_SENDGRID_TEMPLATE_ID')
        mail.asm = Asm(
            group_id=int(os.environ.get('RFCWEEKLY_SENDGRID_GROUP')))
        try:
            mailer.send(mail)
            print('{} new RFCs sent for the week of {}'.format(
                len(rfcs), week))
        except Exception as e:
            print(e.to_dict)


def main():
    mailer = SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    week = date.today().strftime('%B %d')
    rfcs = fetch_rfcs()
    drafts = fetch_drafts()
    if not rfcs and not drafts:
        print('No RFCS for the week of {}'.format(week))
        return
    if os.environ.get('DISABLE_MAIL_SENDING'):
        print(
            'Disabling mail sending due to DISABLE_MAIL_SENDING variable being set.'
        )
        return
    send_emails(mailer, rfcs, drafts)


if __name__ == '__main__':
    main()
