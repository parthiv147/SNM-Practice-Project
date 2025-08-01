import smtplib
from email.message import EmailMessage
def send_mail(to, subject, body):
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login('parthiv147d@gmail.com','zxdt koau jzgt trtv')
    msg = EmailMessage()
    msg['From'] = 'parthiv147d@gmail.com'
    msg['To'] = to
    msg['Subject'] = subject
    msg.set_content(body)
    server.send_message(msg)
    server.close()
    