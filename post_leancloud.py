# -*- coding: utf8 -*-

import leancloud
import pytz

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


def data_file_name(name):
    return 'official_data/' + name + '.json'


def object_id_key(name, id_value):
    return name + "_" + str(id_value)


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


def get_schedule():
    schedule = load_json(data_file_name('schedule'))
    # ['id', 'enabled', 'name', 'tournaments', 'matches']
    matches = []
    current_year_no, current_week_no, current_week_day = datetime.datetime.now(
        tz=pytz.timezone('Asia/Shanghai')).isocalendar()
    for stage_info in schedule['data']['stages']:
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
                print(match_info['id'], match_info['startDateTS'])
                year_no, week_no, week_day = datetime.datetime.fromtimestamp(
                    match_info['startDateTS'] / 1000, tz=pytz.timezone('Asia/Shanghai')).isocalendar()
                match['week_no'] = current_week_no - \
                                   week_no + (current_year_no - year_no) * 52
            for key, value in match_info.items():
                match[key] = value
            for competitor in match['competitors']:
                if competitor:
                    del competitor['content']

            matches.append(match)
    return matches


def upload_data():
    object_data = {
        'Schedule': {'data': get_schedule(), 'id_key': 'id'},
    }

    for name, info in object_data.items():
        data_objects = []
        LEANCLOUD_OBJECT_DATA = load_json(os.path.join('leancloud_data', name))
        data_dict = {}
        for item in info['data']:
            if data_changed(LEANCLOUD_OBJECT_DATA.get(object_id_key(
                    name, item.get(info['id_key'])), {}), item):
                if info['id_key'] not in item:
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
        for data_object in data_objects:
            OBJECT_ID_MAP[object_id_key(
                name, data_object.get(info['id_key']))] = data_object.id
            LEANCLOUD_OBJECT_DATA[object_id_key(
                name, data_object.get(info['id_key']))] = data_dict[data_object.get(info['id_key'])]
        write_json('official_data/object_id_map.json', OBJECT_ID_MAP)
        write_json(os.path.join('leancloud_data', name), LEANCLOUD_OBJECT_DATA)


if __name__ == '__main__':
    LEANCLOUD_OBJECT_DATA = {}
    OBJECT_ID_MAP = load_json('official_data/object_id_map.json')
    # upload_data()
    get_schedule()
