import ConfigParser
import email
import imaplib
import smtplib
import sys
from processmail import process_message

config = ConfigParser.ConfigParser()
config.read('config')
secret_key = config.get('mailassist', 'password');

mail = imaplib.IMAP4_SSL(config.get('mailassist', 'imap'), int(config.get('mailassist', 'imap_port')))
try:
    (retcode, capabilities) = mail.login(config.get('mailassist', 'username'), secret_key)
except:
    print sys.exc_info()[1]
    sys.exit(1)

mail.select(config.get('mailassist', 'mailbox'))
(retcode, messages) = mail.search(None, '(UNSEEN)')
if retcode != "OK":
    print sys.exc_info()[1]
    sys.exit(1)


class NetHandler:
    def __init__(self, mail, config, server):
        self.mail = mail
        self.server = server
        self.sender = config.get('mailassist', 'sender')
        self.seen = {}
        self.language = 'Language: ' + config.get('mailassist', 'language')

    def is_interesting(self, payload):
        return self.language in payload

    def make_current(self, num):
        self.num = num

    def seen_before(self, addr):
        return addr in self.seen

    def mark_seen(self, addr):
        self.seen[addr] = True

    def mark_read(self):
        ret, data = self.mail.store(self.num,'+FLAGS','\\Seen')
        if ret != 'OK':
            print 'Error marking message as read:', ret, data

    def mark_unread(self):
        ret, data = self.mail.store(num,'-FLAGS','\\Seen')
        if ret != 'OK':
            print 'Error marking message as unread:', ret, data        

    def forward(self, addresses, subject, payload):
        msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n%s" % (self.sender,
                                                               ','.join(addresses),
                                                               subject,
                                                               payload)
        self.server.sendmail(self.sender, addresses, msg)

    def send(self, destination, maillist, subject, reply):
        msg = "From: %s\r\nTo: %s\r\nCC: %s\r\nSubject: %s\r\n\r\n%s" % (self.sender,
                                                                         destination,
                                                                         maillist,
                                                                         "Re: " + subject,
                                                                         reply)
        self.server.sendmail(self.sender, [destination, maillist], msg)


server = smtplib.SMTP(config.get('mailassist', 'smtp'), config.get('mailassist', 'smtp_port'))
server.starttls()
server.login(config.get('mailassist', 'username'), secret_key)

handler = NetHandler(mail, config, server)
for num in messages[0].split(' '):
    typ, data = mail.fetch(num,'(RFC822)')
    msg = email.message_from_string(data[0][1])
    handler.make_current(num)
    if not process_message(msg, handler):
        break

server.quit()
mail.close()



