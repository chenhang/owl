# -*- coding: utf8 -*-

from requests import get

from util import *

HEADERS = {
    'user-agent':
        ('Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36'
         ),  # noqa: E501
    'Dnt': ('1'),
    'Accept-Encoding': ('gzip, deflate, sdch'),
    'Accept-Language': ('en'),
    'origin': ('http://stats.nba.com')
}


def live_match_api():
    return "https://api.overwatchleague.cn/live-match?expand=team.content&locale=zh-cn"


def schedule_api():
    return "https://api.overwatchleague.cn/schedule?expand=team.content&locale=zh_CN"


def teams_api():
    return "https://api.overwatchleague.cn/teams?expand=team.content&locale=zh-cn"


def standings_api():
    return "https://api.overwatchleague.cn/standings?expand=team.content&locale=zh_CN"


def standings_v2_api():
    return "https://api.overwatchleague.cn/v2/standings?expand=team.content&locale=zh_CN"


def maps_api():
    return "https://api.overwatchleague.cn/maps"


def team_api(team_id):
    return "https://api.overwatchleague.cn/v2/teams/" + str(team_id) + "?expand=article,schedule&locale=zh_CN"


API_LIST = {'live_match': live_match_api(), 'schedule': schedule_api(),
            'teams': teams_api(), 'standings': standings_api(),
            'maps': maps_api(), 'standings_v2': standings_v2_api()}


def data_file_name(name):
    return 'official_data/' + name + '.json'


def update_data():
    for name, api in API_LIST.items():
        res = get(api, headers=HEADERS, timeout=50).json()
        write_json(data_file_name(name), res)


if __name__ == '__main__':
    if not os.path.exists('official_data'):
        os.mkdir('official_data')
    update_data()
