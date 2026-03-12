from email.mime.text import MIMEText
import base64


def create_draft(service, to, cc, subject, message_text):

    message = MIMEText(message_text)

    message['to'] = to
    if cc and str(cc) != "nan":
        message['cc'] = cc
    message['subject'] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    body = {'message': {'raw': raw}}

    draft = service.users().drafts().create(
        userId="me",
        body=body
    ).execute()

    return draft