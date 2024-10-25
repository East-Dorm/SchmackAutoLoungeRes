import os.path
import base64
from Parse import EventInfo, extract_event_info
from datetime import timedelta, datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# I'm about to be so for real, most of this code is Google's or ChatGPT's, it might look weird because of that



# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/calendar"]


def create_calendar(service, calendar_name):
    calendar = {
        'summary': calendar_name,
        'timeZone': 'PST'  # Set your desired time zone
    }
    created_calendar = service.calendars().insert(body=calendar).execute()
    print(f"Created calendar with ID: {created_calendar['id']}")
    return created_calendar['id']

def add_events_to_calendar(service, calendar_id, event_list):
    for event in event_list:
        if event.header != "meowzles":
            actual_event = {
                'summary': event.header,
                'start': {
                    'dateTime': event.time.isoformat(),
                    'timeZone': 'PST',
                },
                'end': {
                    'dateTime': (event.time + timedelta(hours=1, minutes=30)).isoformat(),  # Default to 1-hour event
                    'timeZone': 'PST',
                }, 
            }
            created_event = service.events().insert(calendarId=calendar_id, body=actual_event).execute()
            print(f"Event created: {created_event.get('htmlLink')}")


# Returns the messages
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

        # Print the message ID
        #print(f"\nMessage ID: {message['id']}")

        # Extract and print desired headers
        header_dict = {}
        for header in headers:
            header_name = header.get('name')
            header_value = header.get('value')
            header_dict[header_name] = header_value

        # What I actually want   
        for x in headers:
            if x['name'] == 'Subject':
                sub = x['value'] #subject
                #print(sub)
                my_headers.append(sub)
    return my_headers



def main():
  """Shows basic usage of the Gmail API.
  Lists the user's Gmail labels.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  #TOKEN_PATH = "/home/stumpy/Scripts/SchmackAutoLoungeRes/token.json"
  TOKEN_PATH = "token.json"
  if os.path.exists(TOKEN_PATH):
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    # Call the Gmail API
    service = build("gmail", "v1", credentials=creds)

    my_query = 'newer_than:1h'


    # my contribution to this mess
    unparsed_headers = gimme_some_the_meats(service, gimme_some_IDs(service, my_query))
    potential_events = []
    for header in unparsed_headers:
       event = extract_event_info(header)
       #Remove duplicates
       if event not in potential_events:
        potential_events.append(event)
    
    #google calendar call
    service2 = build("calendar", "v3", credentials=creds)
    calendar_id = "ee3f1428ddeb99ddcb56b6c7370895499601fc98635024b91c208f99101c74ec@group.calendar.google.com"

    already_added = []
    page_token = None
    while True:
        events = service2.events().list(calendarId=calendar_id, pageToken=page_token).execute()
        for event in events['items']:
            already_added_event = EventInfo(event['summary'])
            already_added_event.time = datetime.strptime(event["start"]["dateTime"],
                  '%Y-%m-%dT%H:%M:00-07:00')
            print(already_added_event)
            for e in potential_events:
                if e.header == already_added_event.header and abs((e.time-already_added_event.time).total_seconds()) <= 7200:
                    potential_events.remove(e)
                    print(event)
        page_token = events.get('nextPageToken')
        if not page_token:
            break  
        
    add_events_to_calendar(service2, calendar_id, potential_events)

  except HttpError as error:
    # TODO(developer) - Handle errors from gmail API.
    print(f"An error occurred: {error}")


if __name__ == "__main__":
  main()
