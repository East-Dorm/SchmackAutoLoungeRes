import os.path
import base64
from datetime import timedelta, datetime, timezone
from urllib.parse import urlencode, quote_plus

from Parse import EventInfo, extract_event_info

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# I'm about to be so for real, most of this code is Google's or ChatGPT's, it might look weird because of that



# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.modify", "https://www.googleapis.com/auth/calendar"]


def add_events_to_calendar(calendar_service, calendar_id, event_list, gmail_service):
    for event in event_list:
        if event.header != "meowzles":
            actual_event = {
                'summary': event.header,
                'start': {
                    'dateTime': event.time.isoformat(),
                    'timeZone': 'PST',
                },
                'end': {
                    'dateTime': (event.time + timedelta(hours=1, minutes=30)).isoformat(),
                    'timeZone': 'PST',
                },
            }
            created_event = calendar_service.events().insert(calendarId=calendar_id, body=actual_event).execute()
            print(f"Event created: {created_event.get('htmlLink')}")

            # Generate the event link
            event_link = generate_event_link(actual_event)

            # Send reply email
            send_reply_email(gmail_service, event.message_id, event_link)


def generate_event_link(actual_event):
    from dateutil import parser
    base_url = 'https://calendar.google.com/calendar/r/eventedit'

    # Parse and convert times to UTC in the required format
    start_time = parser.isoparse(actual_event['start']['dateTime'])
    start_time_utc = start_time.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    end_time = parser.isoparse(actual_event['end']['dateTime'])
    end_time_utc = end_time.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    dates = f"{start_time_utc}/{end_time_utc}"

    params = {
        'action': 'TEMPLATE',
        'dates': dates,
        'stz': 'Europe/Brussels',
        'etz': 'Europe/Brussels',
        'details': actual_event.get('description', ''),
        'location': actual_event.get('location', ''),
        'text': actual_event.get('summary', ''),
    }

    query_string = urlencode(params, quote_via=quote_plus)
    link = f"{base_url}?{query_string}"
    return link


def send_reply_email(service, message_id, event_link):
    # Fetch the original message
    original_message = service.users().messages().get(userId='me', id=message_id, format='full').execute()
    thread_id = original_message['threadId']

    headers = original_message['payload']['headers']
    subject = ''
    sender = ''
    message_id_header = ''
    for header in headers:
        if header['name'] == 'Subject':
            subject = header['value']
        if header['name'] == 'From':
            sender = header['value']
        if header['name'] == 'Message-ID':
            message_id_header = header['value']

    reply_subject = "Re: " + subject if not subject.startswith("Re:") else subject
    message_text = f"Here is the link to this event: {event_link}. Use this is you want to add it to your calender. Alternatively, you could just add the East Dorm Calender by pasting this url in google: https://calendar.google.com/calendar/u/0?cid=ZWUzZjE0MjhkZGViOTlkZGNiNTZiNmM3MzcwODk1NDk5NjAxZmM5ODYzNTAyNGI5MWMyMDhmOTkxMDFjNzRlY0Bncm91cC5jYWxlbmRhci5nb29nbGUuY29t"

    # Build the MIME message
    from email.mime.text import MIMEText
    mime_message = MIMEText(message_text)
    # just send to schmack
    mime_message['to'] = f"east-dorm-chat-l@g.hmc.edu, {sender}"
    mime_message['subject'] = reply_subject
    mime_message['In-Reply-To'] = message_id_header
    mime_message['References'] = message_id_header

    # Encode the message
    raw_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode('utf-8')
    body = {'raw': raw_message, 'threadId': thread_id}

    # Send the message
    sent_message = service.users().messages().send(userId='me', body=body).execute()
    print(f"Replied to message ID: {message_id} with message ID: {sent_message['id']}")



def decode_parts(parts_list):
    for part in parts_list:
        if part.get('parts'):
            decode_parts(part.get('parts'))
        elif part.get('mimeType') == 'text/plain':
            data = part.get('body', {}).get('data', '')
            decoded_data = base64.urlsafe_b64decode(data).decode('utf-8')
            print("Message Body:")
            print(decoded_data)


def gimme_some_IDs(service, query):
    messages = []
    page_token = None
    while True:
        response = service.users().messages().list(
            userId='me', maxResults=100, pageToken=page_token, q=query
        ).execute()
        messages.extend(response.get('messages', []))
        page_token = response.get('nextPageToken')
        print(f"Retrieved {len(messages)} messages so far.")
        if not page_token:
            break
    if not messages:
        print('No messages found.')
    else:
        print(f"Total messages retrieved: {len(messages)}")
    return messages


def gimme_some_the_meats(service, messages):
    my_headers = []
    for message in messages:
        # Fetch the message using the message ID
        msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()

        # Extract the payload from the message
        payload = msg.get('payload', {})
        headers = payload.get('headers', [])

        # Extract and store the Subject and Message ID
        subject = ''
        for header in headers:
            if header['name'] == 'Subject':
                subject = header['value']
                break
        my_headers.append((message['id'], subject))
    return my_headers


def main():
    creds = None
    TOKEN_PATH = "token.json"
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        # Build the Gmail and Calendar services
        gmail_service = build("gmail", "v1", credentials=creds)
        calendar_service = build("calendar", "v3", credentials=creds)

        my_query = 'newer_than:1h'

        # Get messages and extract events
        unparsed_headers = gimme_some_the_meats(gmail_service, gimme_some_IDs(gmail_service, my_query))
        potential_events = []
        for message_id, header in unparsed_headers:
            event = extract_event_info(header)
            event.message_id = message_id  # Attach the message ID to the event
            # Remove duplicates
            if event not in potential_events:
                potential_events.append(event)

        # Calendar ID (replace with your calendar ID)
        calendar_id = "ee3f1428ddeb99ddcb56b6c7370895499601fc98635024b91c208f99101c74ec@group.calendar.google.com"

        # Remove already added events
        already_added = []
        page_token = None
        while True:
            events = calendar_service.events().list(calendarId=calendar_id, pageToken=page_token).execute()
            for event in events['items']:
                already_added_event = EventInfo(event['summary'])
                already_added_event.time = datetime.strptime(event["start"]["dateTime"],
                                                             '%Y-%m-%dT%H:%M:00-07:00')
                print(already_added_event)
                for e in potential_events:
                    if e.header == already_added_event.header and abs(
                            (e.time - already_added_event.time).total_seconds()) <= 7200:
                        potential_events.remove(e)
            page_token = events.get('nextPageToken')
            if not page_token:
                break

        # Add events to calendar and reply to emails
        add_events_to_calendar(calendar_service, calendar_id, potential_events, gmail_service)

    except HttpError as error:
        print(f"An error occurred: {error}")


if __name__ == "__main__":
    main()
