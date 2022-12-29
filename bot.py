import base64, os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import docker

SERVER_DOCKER_URL = "tcp://192.168.1.100:2375"
DOCKER_NAME = "your-minecraft-server-container"
TOKEN_PATH = 'C:\\token.json'
SECRET_PATH = 'C:\\secret.json'

def reboot_server():
    client = docker.DockerClient(base_url=SERVER_DOCKER_URL)
    container = client.containers.get(DOCKER_NAME)
    container.restart()

def runner():
    creds = None
    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(SECRET_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().messages().list(userId='me', q='is:unread AND from:assistenza@paypal.it AND minecraft').execute()
        messages = results.get('messages', [])

        if not messages:
            print('Non go trovà i messagi.')
            return

        print('Messagi:')
        for message in messages:
            service.users().messages().modify(userId='me', id=message["id"], body={
                'removeLabelIds': ['UNREAD'],
                'addLabelIds': ['INBOX']
            }).execute()
            reboot_server()

    except HttpError as error:
        print(f'An error occurred: {error}')

def get_message_body(service, message_id):
  # Retrieve the message using the Gmail API
  message = service.users().messages().get(userId='me', id=message_id).execute()

  # Get the message payload
  payload = message['payload']

  # Get the list of headers
  headers = payload['headers']

  # Find the "Content-Type" header
  content_type_header = next(header for header in headers if header['name'].lower() == 'content-type')

  # Get the value of the "Content-Type" header
  content_type = content_type_header['value']

  # Check if the message body is in plain text or HTML
  if 'text/plain' in content_type:
    # The message body is in plain text
    body = payload['body']['data']
  elif 'text/html' in content_type:
    # The message body is in HTML
    body = payload['body']['data']
  else:
    # The message body is in some other format (e.g., an attachment)
    body = None

  # Decode the message body from base64
  if body:
    body = base64.urlsafe_b64decode(body).decode()

  return body
if __name__ == "__main__":
    runner()