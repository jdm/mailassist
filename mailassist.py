import ConfigParser
import email
import imaplib
import os
import re
import smtplib
import sys
import tempfile
from subprocess import call

config = ConfigParser.ConfigParser()
config.read('config')
secret_key = config.get('mailassist', 'password');

EDITOR = os.environ.get('EDITOR','nano')

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

comment_body = re.compile(r'Comment: (.*)', re.MULTILINE)
language = 'Language: ' + config.get('mailassist', 'language')

baseHeader = """Hi,
I'm Josh, one of many Firefox developers. Glad to hear from you! Feel free to have a look at http://whatcanidoformozilla.org if you're interested in joining a particular project or team. Meanwhile, I'll tell you about some general opportunities for writing code for Firefox.

To get started with the codebase, have a look at http://developer.mozilla.org/En/Introduction. """
baseFooter = """

If you need any help, you can obtain it on IRC. I recommend visiting #introduction, which is specifically for newcomers. See http://irc.mozilla.org for how to access it.

Feel free to contact me anytime if you're having any problems! I'm jdm on IRC, or just josh@joshmatthews.net.

Happy hacking,
Josh"""

responses = {
    'java': baseHeader + "If you'd like to use Java, you can get involved with the Mobile Firefox project, which uses it to create the UI on Android devices. See https://wiki.mozilla.org/Mobile/Get_Involved for more information." + baseFooter,

    '.net': baseHeader + "Unfortunately, we don't do any .NET work, but if you're willing to use any of C++, JavaScript, Java, or Python, there's lots to do!" + baseFooter,

    'learn': """Hi,
I'm Josh, one of many Firefox developers. Glad to hear from you! You may be interested in our web development resources: https://developer.mozilla.org/en-US/learn

Happy hacking,
Josh""",

    'thunderbird': baseHeader + "For Thunderbird in particular, you'll want to start with https://developer.mozilla.org/En/Simple_Thunderbird_build and #maildev on IRC." + baseFooter,

    'b2g': baseHeader + 'If you want to learn more about contributing to Firefox OS, have a look at https://developer.mozilla.org/en-US/docs/Mozilla/Firefox_OS.' + baseFooter,

    'webapps': """Hi,
I'm Josh, one of many Firefox developers. Glad to hear from you! To learn about Firefox OS app development, have a look at https://developer.mozilla.org/en-US/docs/Mozilla/Firefox_OS/Writing_a_web_app_for_B2G .""" + baseFooter,

    'base': baseHeader + baseFooter,

    'intern': """Hi,
I'm Josh, one of many Firefox developers. Glad to hear from you! To learn more about internship possibilities, see the positions available on http://careers.mozilla.org/en-US/ .

Cheers,
Josh""",
}

def forwardMessage(actions, destination):
    if not destination in actions['forward']:
        actions['forward'] += [destination]

handlers = {
    'webdev': 'lcrouch@mozilla.com',
    'docs': 'jswisher@mozilla.com',
    'addons': 'atsay@mozilla.com',
    'l10n': 'jbeatty@mozilla.com',
    'sumo': 'rardila@mozilla.com',
    'marketing': 'cnovak@mozilla.com',
    'design': 'matej@mozilla.com',
    'qa': 'marcia@mozilla.com',
    'france': 'contact@mozfr.org',
    'hispano': 'participa@mozilla-hispano.org'
}

def makeForwarder(contact):
    return lambda actions: forwardMessage(actions, handlers[contact])

def appendToMessage(actions, addition):
    if not addition in actions['reply']:
        actions['reply'] += [addition]

def makeAutoreply(msg):
    return lambda actions: appendToMessage(actions, msg)

filters = {
    'java': makeAutoreply('java'),
    'android': makeAutoreply('java'),
    'mobile': makeAutoreply('java'),
    'mobile': makeAutoreply('java'),

    'thunderbird': makeAutoreply('thunderbird'),

    'c++': makeAutoreply('base'),
    'js': makeAutoreply('base'),
    'javascript': makeAutoreply('base'),
    'python': makeAutoreply('base'),

    'c#': makeAutoreply('.net'),
    '.net': makeAutoreply('.net'),

    'learn': makeAutoreply('learn'),

    'intern': makeAutoreply('intern'),

    'firefox os': makeAutoreply('b2g'),

    'webapp': makeAutoreply('webapp'),
    'app': makeAutoreply('webapp'),

    'php': makeForwarder('webdev'),
    'webdev': makeForwarder('webdev'),
    'django': makeForwarder('webdev'),
    'web develop': makeForwarder('webdev'),

    'qa': makeForwarder('qa'),
    'testing': makeForwarder('qa'),

    'helping users': makeForwarder('sumo'),

    'design': makeForwarder('design'),

    'marketing': makeForwarder('marketing'),

    'spanish': makeForwarder('hispano'),

    'translating': makeForwarder('l10n'),
    'translatte': makeForwarder('l10n'),
    'localize': makeForwarder('l10n'),
    'localizing': makeForwarder('l10n'),

    'addon': makeForwarder('addons'),
    'add-on': makeForwarder('addons'),
    'extension': makeForwarder('addons'),
}

server = smtplib.SMTP(config.get('mailassist', 'smtp'), config.get('mailassist', 'smtp_port'))
server.starttls()
server.login(config.get('mailassist', 'username'), secret_key)

seen = {}

quit = False
for num in messages[0].split(' '):
    skip = False
    keep = False

    typ, data = mail.fetch(num,'(RFC822)')
    msg = email.message_from_string(data[0][1])
    maillist = msg['To']
    destination = msg['Reply-To']
    if destination:
        replacements = {'.cmo': 'com', 'gmial.': 'gmail.', 'gamil.': 'gmail.'}
        for needle in replacements:
            destination = destination.replace(needle, replacements[needle])
    else:
        print 'Skipping non-mailing list message'
        ret, data = mail.store(num,'+FLAGS','\\Seen')
        if ret != 'OK':
            print 'Error marking message as read:', ret, data
        continue

    subject = msg['Subject']
    if destination in seen:
        print 'Skipping duplicate message'
        ret, data = mail.store(num,'+FLAGS','\\Seen')
        if ret != 'OK':
            print 'Error marking message as read:', ret, data
        continue

    payload = msg.get_payload(decode=True)
    if not language in payload:
        print 'Skipping non-English message'
        ret, data = mail.store(num,'+FLAGS','\\Seen')
        if ret != 'OK':
            print 'Error marking non-English message as read:', ret, data
        continue
    else:
        print 'Marking as unread...'
        ret, data = mail.store(num,'-FLAGS','\\Seen')
        if ret != 'OK':
            print 'Error marking message as unread:', ret, data

        comment = payload[payload.find('Comment: ') + len('Comment: '):]
        print '-----'
        print destination
        print comment

        actions = { 'reply': ['base'], 'forward': [] }

        lower_comment = comment.lower()
        for filter_test in filters:
            if filter_test in lower_comment:
                filters[filter_test](actions)

        if actions['reply']:
            print 'Matches:'
            for i in xrange(0, len(actions['reply'])):
                print str(i + 1) + ") " + actions['reply'][i]
        if actions['forward']:
            print 'Forwarding to:', actions['forward']
    
    reply = None
    while True:
        x = raw_input('> ').split()
        if x[0] == '.quit':
            quit = True
            break
        elif x[0] == '.skip':
            skip = True
            break
        elif x[0] == '.keep':
            keep = True
            break
        elif x[0] == '.noforward':
            actions['forward'] = []
            print 'Removing forwards...'
            continue
        elif x[0] == '.forward':
            actions['forward'] += [x[1]]
            print 'Adding forward:', x[1]
            continue
        elif x[0] == '.edit':
            default = ['base'] if len(x) == 1 else x[[1]:]
            print 'Entering editor...'
            with tempfile.NamedTemporaryFile(suffix=".tmp") as tempfile:
                tempfile.write(comment + '\n' + '-' * 10 + '\n' + '\n'.join(map(lambda x: responses[x], default)))
                tempfile.flush()
                call([EDITOR, tempfile.name])
                tempfile.flush()
                tempfile.seek(0)
                contents = tempfile.readlines()
                print contents
                reply = ''.join(contents[contents.index('-'*10+'\r\n') + 1 :])
        elif x[0] in responses:
            reply = responses[x[0]]
            break
        else:
            try:
                choice = int(x[0]) - 1
            except:
                continue
            if choice >= 0 and choice < len(actions['reply']):
                reply = responses[actions['reply'][choice]]
                break

    if quit:
        break
    if keep:
        continue

    sender = config.get('mailassist', 'sender')
    if reply:
        print ''
        print 'Sending reply:'
        print reply
        msg = "From: %s\r\nTo: %s\r\nCC: %s\r\nSubject: %s\r\n\r\n%s" % (sender, destination, maillist, "Re: " + subject, reply)
        server.sendmail(sender, [destination, maillist], msg)

    if actions['forward']:
        print ''
        print 'Forwarding...'
        msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n%s" % (sender, ','.join(actions['forward']), subject, payload)
        server.sendmail(sender, actions['forward'], msg)

    if reply or actions['forward'] or skip:
        print 'Marking as read...'
        seen[destination] = True
        ret, data = mail.store(num,'+FLAGS','\\Seen')
        if ret != 'OK':
            print 'Error marking message as read:', ret, data

server.quit()
mail.close()
