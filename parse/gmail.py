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
import sys

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify'] # we are using modify and not readonly, as we will be marking the messages Read

illegal_unichrs = [(0x00, 0x08), (0x0B, 0x0C), (0x0E, 0x1F),
                   (0x7F, 0x84), (0x86, 0x9F),
                   (0xFDD0, 0xFDDF), (0xFFFE, 0xFFFF)]
if sys.maxunicode >= 0x10000:  # not narrow build
    illegal_unichrs.extend([(0x1FFFE, 0x1FFFF), (0x2FFFE, 0x2FFFF),
                            (0x3FFFE, 0x3FFFF), (0x4FFFE, 0x4FFFF),
                            (0x5FFFE, 0x5FFFF), (0x6FFFE, 0x6FFFF),
                            (0x7FFFE, 0x7FFFF), (0x8FFFE, 0x8FFFF),
                            (0x9FFFE, 0x9FFFF), (0xAFFFE, 0xAFFFF),
                            (0xBFFFE, 0xBFFFF), (0xCFFFE, 0xCFFFF),
                            (0xDFFFE, 0xDFFFF), (0xEFFFE, 0xEFFFF),
                            (0xFFFFE, 0xFFFFF), (0x10FFFE, 0x10FFFF)])

illegal_ranges = [fr'{chr(low)}-{chr(high)}' for (low, high) in illegal_unichrs]
xml_illegal_character_regex = '[' + ''.join(illegal_ranges) + ']'
illegal_xml_chars_re = re.compile(xml_illegal_character_regex)

from clean import TOPIC_IGNORE, PUB_INGORE

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
        unread_msgs = GMAIL.users().messages().list(userId='me',labelIds=['Label_6846142515572560952', 'UNREAD'], maxResults=500).execute()

        # We get a dictonary. Now reading values for the key 'messages'
        
        mssg_list = unread_msgs.get('messages', [])

        print ("Total unread messages in inbox: ", str(len(mssg_list)))

        final_list = {}
        ignored = set()
        new_emails = set()
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
            success = True
            for title in titles:
                try:
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
                    if TOPIC_IGNORE.search(title.text) or TOPIC_IGNORE.search(abstract.text) or PUB_INGORE.search(authors.text):
                        ignored.add(title.text)
                    else:
                        final_list[k] = {
                            'title': clean_text(title.text),
                            'authors': clean_text(authors.text),
                            'abs': clean_text(abstract.text)+'\n'+(clean_text(cite.text) if cite is not None else ''),
                            'date': temp_dict['date']
                        }
                    # print('-'*10)
                except:
                    success = False
                    print(temp_dict['subject'])
            if success:
                new_emails.add(m_id)

            # pdb.set_trace()
            
        for k, paper in final_list.items():
            with open(f"/home/deng.595/workspace/papers/docs/_posts/{paper['date'].strftime('%Y-%m-%d')}-{hashlib.md5(k.encode()).hexdigest()}.markdown", "w") as f:
                f.write(f'---\nlayout: post\ntitle:  "{paper["title"]}"\ndate:   {paper["date"].strftime("%Y-%m-%d %X")} -0400\ncategories: jekyll update\nauthor: "{paper["authors"]}"\n---\n{paper["abs"]}')


        print ("Total papers retrived: ", str(len(final_list)))
        print ("Total papers ignored: ", str(len(ignored)))

        # This will mark the messagea as read
        for m_id in new_emails:
            GMAIL.users().messages().modify(userId=user_id, id=m_id,body={ 'removeLabelIds': ['UNREAD']}).execute() 

        

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f'An error occurred: {error}')

if __name__ == '__main__':
    main()