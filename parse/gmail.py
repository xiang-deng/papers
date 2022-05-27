from __future__ import print_function

import os.path
import pdb

import hashlib

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Importing required libraries
from httplib2 import Http
import base64
from bs4 import BeautifulSoup
import re
import time
import dateutil.parser as parser
from datetime import datetime
import datetime
import csv

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify'] # we are using modify and not readonly, as we will be marking the messages Read

user_id = 'me'

def clean_text(text):
    return re.sub(r"[\'\"\s]", ' ', text).strip()

def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('/home/deng.595/workspace/papers/parse/token.json'):
        creds = Credentials.from_authorized_user_file('/home/deng.595/workspace/papers/parse/token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                '/home/deng.595/workspace/papers/parse/credentials.json', SCOPES)
            creds = flow.run_local_server(port=8899)
        # Save the credentials for the next run
        with open('/home/deng.595/workspace/papers/parse/token.json', 'w') as token:
            token.write(creds.to_json())
    try:
        # Call the Gmail API
        GMAIL = build('gmail', 'v1', credentials=creds)
        # results = GMAIL.users().labels().list(userId='me').execute()
        # labels = results.get('labels', [])
        # print(labels)
        # Getting all the unread messages from Inbox
        # labelIds can be changed accordingly
        unread_msgs = GMAIL.users().messages().list(userId='me',labelIds=['Label_6846142515572560952']).execute()

        # We get a dictonary. Now reading values for the key 'messages'
        mssg_list = unread_msgs['messages']

        print ("Total unread messages in inbox: ", str(len(mssg_list)))

        final_list = {}
        for mssg in mssg_list:
            temp_dict = { }
            m_id = mssg['id'] # get id of individual message
            message = GMAIL.users().messages().get(userId=user_id, id=m_id).execute() # fetch the message using API
            payld = message['payload'] # get payload of the message 
            headers = payld['headers'] # get header of the payload
            header_mapping = {
                'Subject': lambda x: x,
                'From': lambda x: x,
                'Date': lambda x: parser.parse(x)
            }
            for header in headers:
                if header['name'] in header_mapping:
                    temp_dict[header['name'].lower()] = header_mapping[header['name']](header['value'])
            # if 'new articles' not in temp_dict['subject']:
            #     continue

            temp_dict['Snippet'] = message['snippet'] # fetching message snippet
                
            # Fetching message body
            if 'parts' in payld:
                payld = payld.get('parts')[-1]
            data = payld['body']['data'] # fetching the message data
            data = data.replace("-","+").replace("_","/") # decoding from Base64 to UTF-8
            data = base64.b64decode(data)
            soup = BeautifulSoup(data , "lxml" )
            titles = soup.find_all("a", {"class":"gse_alrt_title"})
            is_new = 'new articles' in temp_dict['subject']
            for title in titles:
                # print(title.text)
                authors = title.findNext('div')
                # print(authors.text)
                abstract = authors.findNext('div')
                # print(abstract.text)
                if not is_new:
                    cite = abstract.findNext('span')
                    # print(cite.text)
                else:
                    cite = None
                k = title.text.lower()+' | '+authors.text.lower()
                final_list[k] = {
                    'title': clean_text(title.text),
                    'authors': clean_text(authors.text),
                    'abs': clean_text(abstract.text+' '+(cite.text if cite is not None else '')),
                    'date': temp_dict['date']
                }
                # print('-'*10)

            # pdb.set_trace()

            
            # This will mark the messagea as read
            # GMAIL.users().messages().modify(userId=user_id, id=m_id,body={ 'removeLabelIds': ['UNREAD']}).execute() 
            
        for k, paper in final_list.items():
            with open(f"/home/deng.595/workspace/papers/docs/_posts/{paper['date'].strftime('%Y-%m-%d')}-{hashlib.md5(k.encode()).hexdigest()}.markdown", "w") as f:
                f.write(f'---\nlayout: post\ntitle:  "{paper["title"]}"\ndate:   {paper["date"].strftime("%Y-%m-%d %X")} -0400\ncategories: jekyll update\nauthor: "{paper["authors"]}"\n---\n{paper["abs"]}')


        print ("Total papers retrived: ", str(len(final_list)))

        

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f'An error occurred: {error}')

if __name__ == '__main__':
    main()