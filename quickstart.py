#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
import argparse
import codecs
import locale
import os
import string
import datetime
import sys
import oauth2
import urllib
import json

import pytz

try:
    import tzlocal
    _DEFAULT_TIMEZONE = tzlocal.get_localzone().zone
except:
    _DEFAULT_TIMEZONE = 'Europe/Paris'

import six

__version__ = "1.0.dev0"


# url for list of valid timezones
_TZ_URL = 'http://en.wikipedia.org/wiki/List_of_tz_database_time_zones'


CONF = {
    'consumer_key': '',
    'consumer_secret': '',
    'api_key': '',
    'api_secret': '',
    'data_to_fetch': 1,
    'query': '',
    'geocode': '',
    'lang': '',
    'result_type': 'popular',
    'count': 100,
    'until': None,
    'since_id': None,
}

RESULT_MAP = {
    '1': 'popular',
    '2': 'recent',
    '3': 'mixed'
}


def decoding_strings(f):
    def wrapper(*args, **kwargs):
        out = f(*args, **kwargs)
        if isinstance(out, six.string_types) and not six.PY3:
            # todo: make encoding configurable?
            if six.PY3:
                return out
            else:
                return out.decode(sys.stdin.encoding)
        return out
    return wrapper


def _input_compat(prompt):
    if six.PY3:
        r = input(prompt)
    else:
        r = raw_input(prompt)
    return r

if six.PY3:
    str_compat = str
else:
    str_compat = unicode

dateObject = 'YYYY-MM-DD'


@decoding_strings
def ask(question, answer=str_compat, default=None, l=None, options=None):
    if answer == str_compat:
        r = ''
        while True:
            if default:
                r = _input_compat('> {0} [{1}] '.format(question, default))
            else:
                r = _input_compat('> {0} '.format(question, default))

            r = r.strip()

            if len(r) <= 0:
                if default:
                    r = default
                    break
                else:
                    print('You must enter something')
            else:
                if l and len(r) != l:
                    print('You must enter a {0} letters long string'.format(l))
                else:
                    break

        return r

    elif answer == bool:
        r = None
        while True:
            if default is True:
                r = _input_compat('> {0} (Y/n) '.format(question))
            elif default is False:
                r = _input_compat('> {0} (y/N) '.format(question))
            else:
                r = _input_compat('> {0} (y/n) '.format(question))

            r = r.strip().lower()

            if r in ('y', 'yes'):
                r = True
                break
            elif r in ('n', 'no'):
                r = False
                break
            elif not r:
                r = default
                break
            else:
                print("You must answer 'yes' or 'no'")
        return r
    elif answer == int:
        r = None
        while True:
            if default:
                r = _input_compat('> {0} [{1}] '.format(question, default))
            else:
                r = _input_compat('> {0} '.format(question))

            r = r.strip()

            if not r:
                r = default
                break

            try:
                r = int(r)
                break
            except:
                print('You must enter an integer')
        return r
    elif answer == list:
        # For checking multiple options
        r = None
        while True:
            if default:
                r = _input_compat('> {0} [{1}] '.format(question, default))
            else:
                r = _input_compat('> {0} '.format(question))

            r = r.strip()

            if not r:
                r = default
                break

            # try:
            if int(r) in range(1, len(options)+1):
                break
            else:
                print('Please select valid option: ' + '/'.join('{}'.format(s) for _, s in enumerate(options)))
            # except:
            #     print('Not a valid option')
        return r
    if answer == dateObject:
        r = ''
        while True:
            if default:
                r = _input_compat('> {0} [{1}] '.format(question, default))
            else:
                r = _input_compat('> {0} '.format(question, default))

            r = r.strip()

            if not r:
                r = default
                break

            try:
                datetime.datetime.strptime(r, '%Y-%m-%d')
                break
            except ValueError:
                print("Incorrect data format, should be YYYY-MM-DD")

        return r

    else:
        raise NotImplemented(
            'Argument `answer` must be str_compat, bool, or integer')


def ask_timezone(question, default, tzurl):
    """Prompt for time zone and validate input"""
    lower_tz = [tz.lower() for tz in pytz.all_timezones]
    while True:
        r = ask(question, str_compat, default)
        r = r.strip().replace(' ', '_').lower()
        if r in lower_tz:
            r = pytz.all_timezones[lower_tz.index(r)]
            break
        else:
            print('Please enter a valid time zone:\n'
                  ' (check [{0}])'.format(tzurl))
    return r


def oauth_req(url, consumer_key, consumer_secret, key, secret, http_method="GET", post_body="", http_headers=None):
    consumer = oauth2.Consumer(key=consumer_key, secret=consumer_secret)
    token = oauth2.Token(key=key, secret=secret)
    client = oauth2.Client(consumer, token)
    resp, content = client.request(url, method=http_method, body=post_body, headers=http_headers)
    return content


def get_json_data(url, parameters, consumer_key, consumer_secret, key, secret):
    parameter_encode = urllib.urlencode(parameters)
    search_result = oauth_req(url + parameter_encode, consumer_key, consumer_secret, key, secret)
    search_result = json.loads(search_result)
    return search_result


def main():

    parser = argparse.ArgumentParser(
        description="CLI tool to fetch twitter data",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-l', '--lang', metavar="lang",
                        help='Set the default language')

    args = parser.parse_args()

    print('''Welcome to Twitter API for ALL v{v}.

  _____        _ _   _               _   ___ ___    __           _  _ _   _ __  __   _   _  _ ___
 |_   _|_ __ _(_) |_| |_ ___ _ _    /_\ | _ \_ _|  / _|___ _ _  | || | | | |  \/  | /_\ | \| / __|
   | | \ V  V / |  _|  _/ -_) '_|  / _ \|  _/| |  |  _/ _ \ '_| | __ | |_| | |\/| |/ _ \| .` \__
   |_|  \_/\_/|_|\__|\__\___|_|   /_/ \_\_| |___| |_| \___/_|   |_||_|\___/|_|  |_/_/ \_\_|\_|___/


This script will help you fetch tweet/user search data from Twitter API and convert it to
your required format.

Please answer the following questions so this script can generate your
required output.

    '''.format(v=__version__))

    CONF['consumer_key'] = ask('Your Application\'s Consumer Key(API Key)? Found here: https://apps.twitter.com/',
                               answer=str_compat)
    CONF['consumer_secret'] = ask('Your Application\'s Consumer Secret(API Secret)? ' +
                                  'Found here: https://apps.twitter.com/app/{ Your API}/keys',
                                  answer=str_compat)
    CONF['api_key'] = ask('Your Access Token? ' +
                          'Found here: https://apps.twitter.com/app/{ Your API}/keys',
                          answer=str_compat)
    CONF['api_secret'] = ask('Your Access Token Secret? ' +
                             'Found here: https://apps.twitter.com/app/{ Your API}/keys',
                             answer=str_compat)
    CONF['data_to_fetch'] = ask('Fetch Tweet Data or User Data? 1/Tweet 2/User',
                                answer=list, default='2', options=[1, 2])
    request_params = {}
    if CONF['data_to_fetch'] == '2':
        print("You requested User Data")
        CONF['query'] = ask('Search terms? ' +
                            'Found here: https://dev.twitter.com/rest/public/search',
                            answer=str_compat)
        request_params['q'] = CONF['query']
        url = 'https://api.twitter.com/1.1/users/search.json?'
        print (get_json_data(url, request_params, CONF['consumer_key'], CONF['consumer_secret'],
                             CONF['api_key'], CONF['api_secret']))
    else:
        print("You requested Tweet Data")
        CONF['query'] = ask('Search terms? ' +
                            'Found here: https://dev.twitter.com/rest/public/search',
                            answer=str_compat)
        request_params['q'] = CONF['query']
        result_data_type = ask('Type of search results? 1/Popular 2/Recent 3/Mixed',
                               answer=list, default='1', options=[1, 2, 3])
        request_params['result_type'] = RESULT_MAP[result_data_type]
        date = ask('Include tweets before? eg. 2015-07-19', answer=dateObject, default=None)
        if date:
            request_params['until'] = date
        url = 'https://api.twitter.com/1.1/search/tweets.json?'
        print(get_json_data(url, request_params, CONF['consumer_key'], CONF['consumer_secret'],
                            CONF['api_key'], CONF['api_secret']))

if __name__ == "__main__":
    main()
