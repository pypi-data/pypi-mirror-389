
"""
Terminal-based Gmail Client
Requires: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
"""

import os
import pickle
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

class TerminalGmail:
    def __init__(self):
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with Gmail API"""
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists('credentials.json'):
                    print("\n❌ Error: credentials.json not found!")
                    print("Please download OAuth credentials from Google Cloud Console")
                    print("Visit: https://console.cloud.google.com/apis/credentials")
                    exit(1)
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('gmail', 'v1', credentials=creds)
        print("✓ Authenticated successfully\n")
    
    def list_messages(self, max_results=10, query=''):
        """List messages from inbox"""
        try:
            results = self.service.users().messages().list(
                userId='me', 
                maxResults=max_results,
                q=query
            ).execute()
            
            messages = results.get('messages', [])
            
            if not messages:
                print("No messages found.")
                return
            
            print(f"\n{'='*80}")
            print(f"📬 INBOX ({len(messages)} messages)")
            print(f"{'='*80}\n")
            
            for idx, msg in enumerate(messages, 1):
                message = self.service.users().messages().get(
                    userId='me', 
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()
                
                headers = message['payload']['headers']
                from_addr = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
                
                is_unread = 'UNREAD' in message.get('labelIds', [])
                unread_marker = '🔵' if is_unread else '  '
                
                print(f"{unread_marker} [{idx}] From: {from_addr[:50]}")
                print(f"    Subject: {subject[:60]}")
                print(f"    Date: {date}")
                print(f"    ID: {msg['id']}")
                print(f"{'-'*80}\n")
                
        except Exception as e:
            print(f"❌ Error listing messages: {e}")
    
    def read_message(self, msg_id):
        """Read a specific message"""
        try:
            message = self.service.users().messages().get(
                userId='me', 
                id=msg_id,
                format='full'
            ).execute()
            
            headers = message['payload']['headers']
            from_addr = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')
            
            print(f"\n{'='*80}")
            print(f"From: {from_addr}")
            print(f"Subject: {subject}")
            print(f"Date: {date}")
            print(f"{'='*80}\n")
            
            # Get message body
            text_body, html_body = self.get_message_body(message['payload'])
            
            if html_body:
                print("📧 This email contains HTML content.")
                choice = input("View as: [1] Text  [2] HTML in browser  [3] Both: ").strip()
                
                if choice == '2' or choice == '3':
                    # Save HTML to temp file and open in browser
                    import tempfile
                    import webbrowser
                    
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                        f.write(html_body)
                        html_file = f.name
                    
                    print(f"✓ Opening HTML in browser...")
                    webbrowser.open('file://' + html_file)
                    
                    if choice == '3' and text_body:
                        print("\n--- TEXT VERSION ---\n")
                        print(text_body)
                
                elif choice == '1' or not choice:
                    if text_body:
                        print(text_body)
                    else:
                        print("⚠️  No plain text version available.")
                        open_html = input("Open HTML in browser? (y/n): ").strip().lower()
                        if open_html == 'y':
                            import tempfile
                            import webbrowser
                            
                            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                                f.write(html_body)
                                html_file = f.name
                            
                            webbrowser.open('file://' + html_file)
            else:
                print(text_body if text_body else "No body content")
            
            print(f"\n{'='*80}\n")
            
            # Mark as read
            self.service.users().messages().modify(
                userId='me',
                id=msg_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            
        except Exception as e:
            print(f"❌ Error reading message: {e}")
    
    def get_message_body(self, payload):
        """Extract message body from payload"""
        text_body = ""
        html_body = ""
        
        def extract_parts(part):
            nonlocal text_body, html_body
            
            if 'parts' in part:
                for subpart in part['parts']:
                    extract_parts(subpart)
            else:
                mime_type = part.get('mimeType', '')
                data = part['body'].get('data', '')
                
                if data:
                    decoded = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    
                    if mime_type == 'text/plain':
                        text_body = decoded
                    elif mime_type == 'text/html':
                        html_body = decoded
        
        extract_parts(payload)
        
        # Return both text and html
        return text_body, html_body
    
    def send_message(self, to, subject, body):
        """Send an email"""
        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            self.service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()
            
            print(f"✓ Message sent to {to}")
            
        except Exception as e:
            print(f"❌ Error sending message: {e}")
    
    def search_messages(self, query):
        """Search messages"""
        print(f"\nSearching for: {query}")
        self.list_messages(max_results=10, query=query)
    
    def delete_message(self, msg_id):
        """Delete a message"""
        try:
            self.service.users().messages().trash(
                userId='me',
                id=msg_id
            ).execute()
            print(f"✓ Message moved to trash")
        except Exception as e:
            print(f"❌ Error deleting message: {e}")


def main():
    gmail = TerminalGmail()
    
    while True:
        print("\n" + "="*80)
        print("📧 TERMINAL GMAIL CLIENT")
        print("="*80)
        print("1. List Inbox")
        print("2. Read Message")
        print("3. Send Message")
        print("4. Search Messages")
        print("5. Delete Message")
        print("6. Exit")
        print("="*80)
        
        choice = input("\nSelect option: ").strip()
        
        if choice == '1':
            max_results = input("Number of messages to show (default 10): ").strip()
            max_results = int(max_results) if max_results else 10
            gmail.list_messages(max_results=max_results)
            
        elif choice == '2':
            msg_id = input("Enter message ID: ").strip()
            gmail.read_message(msg_id)
            
        elif choice == '3':
            to = input("To: ").strip()
            subject = input("Subject: ").strip()
            print("Body (type your message, press Cmd+Enter or Ctrl+S to send):")
            print("-" * 40)
            
            import sys
            import tty
            import termios
            
            lines = []
            current_line = ""
            
            # Save terminal settings
            old_settings = termios.tcgetattr(sys.stdin)
            
            try:
                tty.setraw(sys.stdin.fileno())
                
                while True:
                    char = sys.stdin.read(1)
                    
                    # Ctrl+S to send (works on all platforms)
                    if char == '\x13':
                        lines.append(current_line)
                        break
                    
                    # Check for Escape sequences (includes Cmd+Enter on Mac)
                    if char == '\x1b':  # ESC
                        next_chars = sys.stdin.read(2)
                        # Cmd+Enter sends ESC + [13~ on Mac Terminal
                        if next_chars == '[1' or next_chars == '[2':
                            remaining = sys.stdin.read(2)
                            if '~' in remaining:
                                # This is Cmd+Enter, send the message
                                lines.append(current_line)
                                break
                        continue
                    
                    # Regular Enter (newline)
                    elif char == '\r' or char == '\n':
                        sys.stdout.write('\r\n')
                        sys.stdout.flush()
                        lines.append(current_line)
                        current_line = ""
                    
                    # Backspace (Mac uses \x7f)
                    elif char == '\x7f' or char == '\x08':
                        if current_line:
                            current_line = current_line[:-1]
                            sys.stdout.write('\b \b')
                            sys.stdout.flush()
                    
                    # Ctrl+D (EOF) - alternative way to send
                    elif char == '\x04':
                        lines.append(current_line)
                        break
                    
                    # Regular character
                    elif ord(char) >= 32:
                        current_line += char
                        sys.stdout.write(char)
                        sys.stdout.flush()
                        
            finally:
                # Restore terminal settings
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                print("\n" + "-" * 40)
            
            body = '\n'.join(lines)
            if body.strip():
                gmail.send_message(to, subject, body)
            else:
                print("❌ Email body is empty. Message not sent.")
            
        elif choice == '4':
            query = input("Search query: ").strip()
            gmail.search_messages(query)
            
        elif choice == '5':
            msg_id = input("Enter message ID to delete: ").strip()
            confirm = input(f"Delete message {msg_id}? (yes/no): ").strip().lower()
            if confirm == 'yes':
                gmail.delete_message(msg_id)
            
        elif choice == '6':
            print("\nGoodbye! 👋")
            break
            
        else:
            print("Invalid option. Please try again.")


if __name__ == '__main__':
    main()