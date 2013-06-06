import sys
import email
from processmail import process_message

class StubHandler:
    def seen_before(self, addr):
        pass
    def mark_read(self):
        pass
    def mark_unread(self):
        pass
    def forward(self, addresses, subject, payload):
        pass
    def send(self, destination, maillist, subject, reply):
        pass
    def is_interesting(self, payload):
        return not not payload

fp = open(sys.argv[1], 'r')
contents = fp.read()
fp.close()
msg = email.message_from_string(contents)
process_message(msg, StubHandler())
