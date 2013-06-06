import os
import re
import tempfile
from subprocess import call

EDITOR = os.environ.get('EDITOR','nano')

comment_body = re.compile(r'Comment: (.*)', re.MULTILINE)

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

    'webapp': """Hi,
I'm Josh, one of many Firefox developers. Glad to hear from you! To learn about Firefox OS app development, have a look at https://developer.mozilla.org/en-US/docs/Mozilla/Firefox_OS/Writing_a_web_app_for_B2G .""" + baseFooter,

    'base': baseHeader + baseFooter,

    'intern': """Hi,
I'm Josh, one of many Firefox developers. Glad to hear from you! To learn more about internship possibilities, see the positions available on http://careers.mozilla.org/en-US/ .

Cheers,
Josh""",

    'support': """I'm sorry to hear about some of the issues you are running into with Firefox. Perhaps we can help solve your problem with a simple fix.

I suggest asking about this on our Firefox support site at

http://support.mozilla.com/kb/ask

Please be specific and also post any error messages if available and/or a crash ID so that we can have a more complete understanding of the issue.

Thanks, we're here to help.""",

    'hispano': """Please visit http://www.mozilla.org/es-ES/contribute/ for more information.

Cheers,
Josh"""
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
    'france': 'contact@mozfr.org'
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
    'firefoxos': makeAutoreply('b2g'),

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

    'spanish': makeAutoreply('hispano'),

    'translation': makeForwarder('l10n'),
    'translating': makeForwarder('l10n'),
    'translate': makeForwarder('l10n'),
    'localize': makeForwarder('l10n'),
    'localise': makeForwarder('l10n'),
    'localizing': makeForwarder('l10n'),
    'localising': makeForwarder('l10n'),
    'localization': makeForwarder('l10n'),
    'localisation': makeForwarder('l10n'),

    'add on': makeForwarder('addons'),
    'addon': makeForwarder('addons'),
    'add-on': makeForwarder('addons'),
    'extension': makeForwarder('addons'),

    'writing': makeForwarder('docs'),
    'documentation': makeForwarder('docs'),
    'docs': makeForwarder('docs'),
}

def process_message(msg, handler):
    quit = False
    skip = False
    keep = False

    maillist = msg['To']
    destination = msg['Reply-To']
    if destination:
        replacements = {'.cmo': 'com', 'gmial.': 'gmail.', 'gamil.': 'gmail.'}
        for needle in replacements:
            destination = destination.replace(needle, replacements[needle])
    else:
        print 'Skipping non-mailing list message'
        handler.mark_read()
        return False

    if handler.seen_before(destination):
        print 'Skipping duplicate message'
        handler.mark_read()
        return False

    subject = msg['Subject']
    payload = msg.get_payload(decode=False)
    if isinstance(payload, list):
        payload = '\n'.join(map(str, payload))
    if not payload:
        print msg
    if not handler.is_interesting(payload):
        print 'Skipping non-English message'
        handler.mark_read()
        return False
    else:
        print 'Marking as unread...'
        handler.mark_unread()

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
        if not x:
            continue
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
            default = ['base'] if len(x) == 1 else x[1:]
            print 'Entering editor...'
            with tempfile.NamedTemporaryFile(suffix=".tmp") as f:
                f.write(comment + '\n' + '-' * 10 + '\n' + '\n'.join(map(lambda x: responses[x], default)))
                f.flush()
                call([EDITOR, f.name])
                f.flush()
                f.seek(0)
                contents = f.readlines()
                reply = ''.join(contents[contents.index('-'*10+'\r\n') + 1 :])
                break
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
        return False
    if keep:
        return True

    if reply:
        print ''
        print 'Sending reply:'
        print reply
        handler.send(destination, maillist, subject, reply)

    if actions['forward']:
        print ''
        print 'Forwarding...'
        handler.forward(actions['forward'], subject, payload)

    if reply or actions['forward'] or skip:
        print 'Marking as read...'
        handler.mark_seen(destination)
        handler.mark_read()

    return True
