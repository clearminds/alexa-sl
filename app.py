# -*- coding: utf-8 -*-
import os
from config import Config
from flask import Flask
from flask_ask import Ask, request, session, question, statement
from werkzeug.contrib.fixers import ProxyFix
from unidecode import unidecode
import logging

from sl import SL

config = Config()

app = Flask(__name__)
ask = Ask(app, "/")
logging.getLogger('flask_ask').setLevel(logging.DEBUG)
sl = SL(os.environ['SL_API_KEY'])

def get_site_id(transporatation):
    return os.environ.get('SL_%s_SITE_ID' % transporatation.upper())

@ask.launch
def launch():
    speech_text = 'Welcome to S L Real Time Alexa Skill'
    return question(speech_text).reprompt(speech_text).simple_card('SL', speech_text)

@ask.intent('SLRealTimeCityIntent')
def real_time_city(transportation):
    sl.reset_filter()
    if transportation in ('metro', 'subway'):
        sl.metro = True
        sl.journey_direction = 1
        sl.site_id = get_site_id('metro')
    else:
        speech_text = "I only support metro with this quetion"
        return statement(speech_text).simple_card('SL', speech_text)

    return _generate_answer(transportation)

@ask.intent('SLRealTimeIntent')
def real_time(transportation):
    sl.reset_filter()
    if transportation in ('metro', 'subway'):
        sl.metro = True
        sl.site_id = get_site_id('metro')
    elif transportation == 'bus':
        sl.bus = True
        sl.site_id = get_site_id('bus') 
    else:
        speech_text = "Sorry I didn't catch what you asked for there, which transporatation did you want to go with. Bus or Metro?"
        return question(speech_text).reprompt(speech_text).simple_card('SL', speech_text)

    return _generate_answer(transportation)

def _generate_answer(transportation):
    result = sl.simple_list()
    if not result:
        speech_text = u'I can not find any departures with the %s' % transportation
        return statement(unidecode(speech_text)).simple_card('SL', speech_text)

    speech_reply =  []
    card_reply =  []
    for r in result:
        r['transportation'] = transportation
        cnt = len(speech_reply)
        if cnt < 4:
            if cnt == 0:
                speech_reply.append(u'<s>The next %(transportation)s %(line_number)s to %(destination)s will depart %(time_left)s</s>' % r)
            if cnt == 1:
                speech_reply.append(u'<s>Followed by %(line_number)s to %(destination)s %(time_left)s</s>' % r)
            if cnt > 1:
                speech_reply.append(u'<s>%(line_number)s to %(destination)s %(time_left)s</s>' % r)

            card_reply.append(u'%(transport_type)s %(line_number)s to %(destination)s will depart %(time_left)s.' % r)

    speech_text = ''.join(speech_reply)
    speech_text = '<speak>' + speech_text + '</speak>'
    card_text = '\n'.join(card_reply)
    return statement(unidecode(speech_text)).simple_card('SL', card_text)


@ask.intent('AMAZON.HelpIntent')
def help():
    speech_text = 'You can ask me when the bus or subway goes. For example, When does the next bus go?'
    return question(speech_text).reprompt(speech_text).simple_card('SL', speech_text)


@ask.session_ended
def session_ended():
    return "", 200


if __name__ == '__main__':
    # Be sure to set config.debug_mode to False in production
    port = int(os.environ.get("PORT", config.port))
    if port != config.port:
        config.debug = False
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.run(host='0.0.0.0', debug=config.debug_mode, port=port)
