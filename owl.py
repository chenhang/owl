# -*- coding: utf8 -*-

import leancloud
import pytz
from requests import get

import config
from util import *

logging.basicConfig(level=logging.DEBUG)

leancloud.init(config.leancloud_app_id, config.leancloud_app_key)

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


APIS = {'live_match': live_match_api(), 'schedule': schedule_api(),
        'teams': teams_api(), 'standings': standings_api(),
        'maps': maps_api(), 'standings_v2': standings_v2_api()}


def data_file_name(name):
    return 'data/' + name + '.json'


def object_id_key(name, id_value):
    return name + "_" + str(id_value)


def update_data():
    for name, api in APIS.items():
        res = get(api, headers=HEADERS, timeout=50).json()
        write_json(data_file_name(name), res)


def leancloud_object(name, data, id_key='id'):
    DataObject = leancloud.Object.extend(name)
    if object_id_key(name, data[id_key]) in OBJECT_ID_MAP and name not in []:
        data_object = DataObject.create_without_data(
            OBJECT_ID_MAP[object_id_key(name, data[id_key])])
    else:
        data_object = DataObject()
    for key, value in data.items():
        data_object.set(key, value)
    return data_object


def parse_standings():
    standings = load_json(data_file_name('standings'))
    ranks = standings['ranks']
    standings_v2 = load_json(data_file_name('standings_v2'))
    stage_ranks = []
    ranks_by_id = {rank['id']: rank for rank in standings_v2['data']}
    stages, matches = parse_schedule()
    stages_by_id = {('stage' + str(stage['id'])): stage for stage in stages}
    stage_ranks_keys = ['id', 'divisionId', 'name', 'abbreviatedName',
                        'logo', 'colors']
    for rank in standings_v2['data']:
        stage_rank_basic = {key: rank[key] for key in stage_ranks_keys}
        for key, name in [('preseason', "季前赛"), ('league', "OWL")]:
            if len(rank[key]) == 0:
                continue
            stage_rank = {**stage_rank_basic, **rank[key]}
            stage_rank['stage_id'] = key
            stage_rank['placement_id'] = '_'.join(
                [key, str(stage_rank['id'])])
            stage_rank['stage_name'] = name
            stage_ranks.append(stage_rank)
        for key, records in rank['stages'].items():
            stage_rank = {**stage_rank_basic, **rank['stages'][key]}
            stage_rank['stage_id'] = key.split('stage')[-1]
            stage_rank['placement_id'] = '_'.join(
                [key, str(stage_rank['id'])])
            stage_rank['stage_name'] = stages_by_id[key]['name']
            stage_ranks.append(stage_rank)
    return stages, matches, ranks, stage_ranks, ranks_by_id


def upload_data():
    stages, matches, ranks, stage_ranks, ranks_by_id = parse_standings()
    teams = load_json(data_file_name('teams'))
    # KEYS
    # ['owl_divisions', 'description', 'availableLanguages',
    # 'game', 'strings', 'competitors', 'logo', 'id', 'name']
    league = {'id': teams['id'], 'name': teams['name'],
              'description': teams['description'], 'logo': teams['logo']}
    divisions = teams['owl_divisions']
    division_mapping = {division['id']: division for division in divisions}

    # ['secondaryPhoto', 'addressCountry', 'handle',
    # 'name', 'logo', 'type', 'availableLanguages',
    # 'abbreviatedName', 'attributesVersion',
    # 'players', 'game', 'content', 'accounts',
    # 'primaryColor', 'owl_division', 'secondaryColor',
    # 'attributes', 'homeLocation', 'id', 'icon']
    competitors_keys = ['secondaryPhoto', 'addressCountry', 'handle',
                        'name', 'logo', 'abbreviatedName',
                        'game', 'content', 'accounts', 'players',
                        'primaryColor', 'owl_division',
                        'secondaryColor', 'attributes',
                        'homeLocation', 'id', 'icon']
    competitors = []
    for item in teams['competitors']:
        competitor = {key: item['competitor'][key] for key in competitors_keys}
        competitor['owl_division_info'] = division_mapping[str(
            competitor['owl_division'])]
        competitor['ranks'] = ranks_by_id[competitor['id']]

    composition_stats = load_json('data/composition_stats.json')
    player_hero_stats = load_json('data/player_hero_stats.json')
    player_stats = load_json('data/player_stats.json')
    team_hero_stats = load_json('data/team_hero_stats.json')
    player_ranks = load_json('data/player_ranks.json')
    hero_ranks = load_json('data/hero_ranks.json')
    player_pick_rate = load_json('data/player_pick_rate.json')
    team_pick_rate = load_json('data/team_pick_rate.json')
    for team_hero_stat in team_hero_stats:
        # print(team_hero_stat)
        # print(ranks_by_id)
        team_hero_stat['ranks'] = ranks_by_id[int(team_hero_stat['id'])]
        team_hero_stat['owl_division_info'] = division_mapping[str(
            team_hero_stat['owl_division'])]
        team_hero_stat['schedule'] = get(team_api(team_hero_stat["id"]), headers=HEADERS, timeout=50).json()['data'][
            'schedule']
        for schedule in team_hero_stat['schedule']:
            del schedule['games']
            for game_competitor in schedule['competitors']:
                del game_competitor['players']

    object_data = {
        'League': {'data': [league], 'id_key': 'id'},
        'Division': {'data': divisions, 'id_key': 'id'},
        'Competitor': {'data': competitors, 'id_key': 'id'},
        'Rank': {'data': ranks, 'id_key': 'placement'},
        'StageRank': {'data': stage_ranks, 'id_key': 'placement_id'},
        'Stage': {'data': stages, 'id_key': 'id'},
        'Match': {'data': matches, 'id_key': 'id'},
        'CompositionUsage': {'data': composition_stats, 'id_key': 'id'},
        'TeamHeroUsage': {'data': team_hero_stats, 'id_key': 'id'},
        'PlayerRank': {'data': player_ranks, 'id_key': 'id'},
        'HeroRank': {'data': hero_ranks, 'id_key': 'id'},
        'PlayerPickRate': {'data': player_pick_rate, 'id_key': 'id'},
        'TeamPickRate': {'data': team_pick_rate, 'id_key': 'id'},
    }

    for name, info in object_data.items():
        data_objects = []
        LEANCLOUD_OBJECT_DATA = load_json(os.path.join('leancloud_data', name))
        data_dict = {}
        for item in info['data']:
            if data_changed(LEANCLOUD_OBJECT_DATA.get(object_id_key(
                    name, item.get(info['id_key'])), {}), item):
                if info['id_key'] not in item:
                    # print(item, name)
                    continue
                data_objects.append(leancloud_object(
                    name, item, info['id_key']))
            data_dict[item.get(info['id_key'])] = item
        print(name + " Total Count:" + str(len(info['data'])))
        print(name + " Changed Count:" + str(len(data_objects)))
        i = 0
        batch_size = 50
        while True:
            if len(data_objects[i:i + batch_size]) > 0:
                leancloud.Object.save_all(data_objects[i:i + batch_size])
                i += batch_size
            else:
                break
        # if len(data_objects) > 0:
        #     leancloud.Object.save_all(data_objects)
        for data_object in data_objects:
            OBJECT_ID_MAP[object_id_key(
                name, data_object.get(info['id_key']))] = data_object.id
            LEANCLOUD_OBJECT_DATA[object_id_key(
                name, data_object.get(info['id_key']))] = data_dict[data_object.get(info['id_key'])]
        write_json('data/object_id_map.json', OBJECT_ID_MAP)
        write_json(os.path.join('leancloud_data', name), LEANCLOUD_OBJECT_DATA)


def parse_schedule():
    schedule = load_json(data_file_name('schedule'))
    # ['id', 'enabled', 'name', 'tournaments', 'matches']
    stages = []
    matches = []
    current_year_no, current_week_no, current_week_day = datetime.datetime.now(
        tz=pytz.timezone('Asia/Shanghai')).isocalendar()
    for stage_info in schedule['data']['stages']:
        stage = stage_info
        stage_matches = []
        # ['id', 'competitors', 'scores',
        # 'round', 'ordinal', 'winnersNextMatch',
        # 'winnerRound', 'winnerOrdinal', 'bestOf',
        # 'conclusionValue', 'conclusionStrategy',
        # 'winner', 'state', 'attributes', 'games',
        # 'clientHints', 'dateCreated', 'flags',
        # 'handle', 'startDate', 'endDate',
        # 'showStartTime', 'showEndTime',
        # 'startDateTS', 'endDateTS', 'youtubeId',
        # 'wins', 'ties', 'losses', 'videos', 'tournament']
        for match_info in stage_info['matches']:
            match = {'stageId': stage_info['id'],
                     'stageName': stage_info['name']}
            if match_info['startDateTS']:
                year_no, week_no, week_day = datetime.datetime.fromtimestamp(
                    match_info['startDateTS'] / 1000, tz=pytz.timezone('Asia/Shanghai')).isocalendar()
                match['week_no'] = current_week_no - \
                                   week_no + (current_year_no - year_no) * 52
            for key, value in match_info.items():
                match[key] = value
            for competitor in match['competitors']:
                if competitor:
                    del competitor['content']
            if match_info['startDateTS'] / 1000 < datetime.datetime.now().timestamp() + 14 * 24 * 3600 and match_info['startDateTS'] / 1000 > datetime.datetime.now().timestamp() - 7 * 24 * 3600:
                matches.append(match)
                stage_matches.append(match)
        del stage['matches']  # stage_matches
        for week in stage['weeks']:
            del week['matches']
        stages.append(stage)
    return stages, matches


if __name__ == '__main__':
    LEANCLOUD_OBJECT_DATA = {}
    OBJECT_ID_MAP = load_json('data/object_id_map.json')
    update_data()
    upload_data()
