# References
# Tabulate: https://pypi.org/project/tabulate/
#

import configparser as cp
import os
import argparse
import requests
import json
from tabulate import tabulate

base_url_nfl = 'http://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard'
week_url = 'week='
week_num = None

week_csv_data = []

def httpbin(val):
    try:
        r = requests.post('https://httpbin.org/post', data=val)
        r.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print('bad response', r.status_code)
        raise SystemExit(err)
    except requests.exceptions.RequestException as err:
        print('request exception')
        raise SystemExit(err)

    print('Status code: {}'.format(r.status_code))
    print('Response data:\n{}'.format(r.text))


def get_by_week(weekval):
    print('Evaluating weekval: {}'.format(weekval))
    week_range = range(0, 0)
    if weekval is None:
        print('weekval is missing; use 1-17 or all')
        return
    # TODO handle looping through all weeks
    if str(weekval) == 'all':
        week_range = range(1, 17)
    else:
        weekval = int(weekval)
        week_range = range(weekval, weekval + 1)

    for week_number in week_range:
        print('week_number: {}'.format(week_number))
        try:
            cache_filename = 'cache/week-{}.json'.format(week_number)
            if (os.path.exists(cache_filename)):
                with open(cache_filename, 'r') as cache_file:
                    jsondata = json.loads(cache_file.read())

                print(jsondata.leagues)

            else:
                url = '{}?{}{}'.format(base_url_nfl, week_url, week_number)
                print('Retrieving: {}'.format(url))
                r = requests.get(url)
                r.raise_for_status()
                data = json.loads(r.text)
                with open(cache_filename, 'w') as cache_file:
                    cache_file.write(json.dumps(data, indent=2))


        except requests.exceptions.HTTPError as err:
            print('bad response', r.status_code)
            raise SystemExit(err)


def gen_csv():
    # Let's start with week 1
    _get_from_cache(1)

    pass

def _get_from_cache(week_num=None):
    if week_num:
        with open('cache/week-{}.json'.format(week_num), 'r') as cache_file:
            data = json.loads(cache_file.read())

        events = data['events']
        for event in events:
            game = {}
            week_csv_data.append(game)
            game['game_id'] = event['id']
            game['week'] = data['week']['number']
            game['date'] = event['date']
            game['name'] = event['shortName']
            game['attendance'] = event['competitions'][0]['attendance']

            # team0 looks to be always home so no validation at this time
            home =  event['competitions'][0]['competitors'][0]
            away =  event['competitions'][0]['competitors'][1]
            game['home'] = home['team']['abbreviation']
            game['away'] = away['team']['abbreviation']

            if 'winner' in home:
                home_win = home['winner']
                if home_win:
                    game['win'] = game['home']
                else:
                    game['win'] = game['away']
            else:
                game['win'] = None

            game['home_score'] = home['score']
            game['away_score'] = away['score']
            game_state = event['status']['type']['state']
            if game_state == 'post':
                game['game_over'] = True
            else:
                game['game_over'] = False

            # print(event)

        # print(week_csv_data)

def summary(week_num):
    _get_from_cache(week_num)
    print(tabulate(week_csv_data, headers='keys'))
    # print(week_csv_data)



def _init_argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--weeks', nargs='?', const='all', help="Weeks to retrieve")
    parser.add_argument('-q', '--quiet', nargs='?', const='n',
                        help="Skip confirmations and messages - TBD")
    parser.add_argument('--csv', help='Generate CSV file', action='store_true')
    parser.add_argument('--summary', nargs='?', help='Generate summary by week')
    parser.add_argument('--clean', nargs='?', help="Clear the cache folder")
    parser.add_argument('--sanity', nargs='?', const='{"foo": "bar"}',
                        help="Call httpbin.org just to see if things are okay")
    return parser.parse_args()


def handle_args(args):
    if (args.sanity):
        httpbin(args.sanity)
    if (args.weeks):
        print('handling weeks: {}'.format(args.weeks))
        get_by_week(args.weeks)
    if (args.csv):
        gen_csv()
        print(json.dumps(week_csv_data))

    if (args.summary):
        summary(args.summary)


def ensure_cache_folder(val, create=False):
    if os.path.exists(val):
        pass
    else:
        print('{} DOES NOT exist'.format(val))
        if create:
            print('creating the folder')
            os.mkdir(val)


if __name__ == '__main__':
    ensure_cache_folder('cache', True)
    handle_args(_init_argparser())
    quit()
