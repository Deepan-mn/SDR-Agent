
import os, re
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from email.mime.text import MIMEText
import base64
from datetime import datetime, timedelta

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']


class OutReachTool:
    def __init__(self):
        self.service = self._get_gmail_service()

    def draft_welcome_mail(self,lead_info, sender, welcome_email, user_id='me'):
        try:
            self._get_complete_lead_info(lead_info)
            message = self._create_welcome_message(sender, welcome_email)
            draft = self.service.users().drafts().create(userId=user_id, body={
                'message': {
                    'raw': self._encode_message(message)
                }
            }).execute()
            print(f"Draft created for email from {sender} with subject 'Welcome'")
            return draft
        except Exception as error:
            print(f"An error occurred while creating draft: {error}")
            return None

    def send_welcome_mail(self, lead_info, sender, welcome_email, user_id='me'):
        try:
            self._get_complete_lead_info(lead_info)
            message = self._create_welcome_message(sender, welcome_email)
            sent_message = self.service.users().messages().send(userId=user_id, body={
                'raw': self._encode_message(message)
            }).execute()
            print(f"Reply sent to {sender} with subject 'Welcome'")
            return sent_message
        except Exception as error:
            print(f"An error occurred while sending reply: {error}")
            return None

    def _get_complete_lead_info(self, lead_info):
        try:
            return lead_info
        except Exception as error:
            print(f"An error occurred while writing  welcome email: {error}")
            return None

    def _create_welcome_message(self, sender, reply_text):
        message = MIMEText(reply_text)
        message['to'] = sender
        message['subject'] = f"Welcome to Davinci.ai- An Agentic Automation Agency"
        return message

    def _get_gmail_service(self):
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())

        return build('gmail', 'v1', credentials=creds)

    def _encode_message(self, message):
        return base64.urlsafe_b64encode(message.as_bytes()).decode()
