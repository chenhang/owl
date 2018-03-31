#-*- coding: utf8 -*-
from util import *
competitors = load_json('leancloud_data/Competitor')
divisions = load_json('leancloud_data/Division')
name_mapping = {'Boston Uprising': 'BOS', 'Dallas Fuel': 'DAL', 'Florida Mayhem': 'FLA',
                'Los Angeles Gladiators': 'GLA', 'Houston Outlaws': 'HOU', 'London Spitfire': 'LDN',
                'New York Excelsior': 'NYE', 'Philadelphia Fusion': 'PHI', 'Seoul Dynasty':
                'SEO', 'San Francisco Shock': 'SFS', 'Shanghai Dragons': 'SHD', 'Los Angeles Valiant': 'VAL'}
winstonlab_teams = {'336': 'New York Excelsior', '331': 'Houston Outlaws', '332': 'London Spitfire',
                    '318': 'Boston Uprising', '337': 'Philadelphia Fusion', '335': 'Florida Mayhem',
                    '333': 'Los Angeles Valiant', '329': 'Seoul Dynasty', '334': 'Los Angeles Gladiators',
                    '338': 'San Francisco Shock', '330': 'Dallas Fuel', '328': 'Shanghai Dragons'}
teams = {competitor['abbreviatedName']: {**competitor, **{'owl_division_info': divisions['Division_' + str(competitor['owl_division'])]}} for _,
         competitor in competitors.items()}
teams_by_id = {competitor['id']: {**competitor, **{'owl_division_info': divisions['Division_' + str(competitor['owl_division'])]}} for _,
               competitor in competitors.items()}
competitors_keys = ['secondaryPhoto', 'addressCountry', 'handle',
                    'name', 'logo', 'abbreviatedName',
                    'game', 'accounts', 'players',
                    'primaryColor', 'owl_division',
                    'secondaryColor', 'attributes',
                    'homeLocation', 'id', 'icon']

composition_stats = load_json('stats/composition_stats.json')
for item in composition_stats:
    item['id'] = '_'.join([''.join([pos[0] for pos in sorted(item['composition'])]),
                           item['category'], item['map_name']]).lower()

player_hero_stats = load_json('stats/player_hero_stats.json')
for item in player_hero_stats:
    item['id'] = '_'.join(['_'.join(sorted(item['heros'])),
                           item['category'], item['map_name']]).lower()

# PLAYERS
player_stats = load_json('stats/player_stats.json')
players = {}
player_stats_avg_min = {}
player_stats_keys = ['map_played', 'kills', 'deathes',
                     'plusminus', 'ultimates', 'ultimates_percent',
                     'percent_of_team', 'hero_kd', 'role']
for _, competitor in competitors.items():
    for player in competitor['players']:
        if player['player']['name'].lower() in players:
            print(player['name'].lower())
        else:
            players[player['player']['name'].lower()] = player

for item in player_stats:
    key = item['name'].lower().replace('bigg00se', 'biggoose')
    if key in players:
        item['winstonlab_id'] = item['id']
        item['id'] = players[key]['player']['id']
        item['player_info'] = players[key]
        for stat_key in ['map_played']:
            item[stat_key] = int(item[stat_key])
        for stat_key in ['kills', 'deathes', 'plusminus', 'ultimates']:
            item[stat_key] = float(item[stat_key])
        item['ultimates_percent'] = str(int(item['ultimates'] * 100)) + "%"
        if item['category'] == 'Allmaps' and item['display_type'] == 'avg/min' and item['map_name'] == 'all_maps':
            player_stats_avg_min[key] = item
    else:
        print(item['name'])
        del item

player_ranks = load_json('stats/player_ranks.json')
hero_ranks = load_json('stats/hero_ranks.json')
for item in player_ranks:
    key = item['name'].lower().replace('bigg00se', 'biggoose')
    if key in players:
        item['id'] = item['overall_rank']
        item['key'] = key
        item['player_info'] = players[key]
        item['player_id'] = players[key]['player']['id']
        item['team_info'] = {team_key: teams_by_id[players[key]
                                                   ['team']['id']][team_key] for team_key in competitors_keys}
        item['team_info']['players'] = []

        for hero_rank in item['hero_ranks']:
            hero_rank['hero_name'] = hero_rank['hero_name'].replace(
                ': ', '-').replace('.', '')
        for stat_key in player_stats_keys:
            item[stat_key] = player_stats_avg_min[key][stat_key]
    else:
        print(item['name'])
        del item

for item in hero_ranks:
    key = item['name'].lower().replace('bigg00se', 'biggoose')
    if key in players:
        item['hero_name'] = item['hero_name'].replace(
            ': ', '-').replace('.', '')
        item['id'] = '_'.join([item['hero_name'], str(item['hero_rank'])])
        item['player_info'] = players[key]
        item['player_id'] = players[key]['player']['id']
        item['team_info'] = {team_key: teams_by_id[players[key]
                                                   ['team']['id']][team_key] for team_key in competitors_keys}
        item['team_info']['players'] = []

    else:
        print(item['name'])
        del item

# TEAMS
team_hero_stats = load_json('stats/team_hero_stats.json')
for item in team_hero_stats:
    item['winstonlab_id'] = item['id']
    item['en_name'] = item['name']
    for key in competitors_keys:
        item[key] = teams[name_mapping[item['en_name']]][key]

player_hero_keys = ['gameNumber', 'roundtype', 'player', 'team', 'hero', 'timePlayed',
                    'matchID', 'playerPic', 'playerName', 'teamPic', 'nameCSFriendly', 'map', 'teamName']

player_heros = load_json('stats/player_heros.json')
player_usage = {}
for player_hero in player_heros:
    key = player_hero['playerName'].lower().replace('bigg00se', 'biggoose')
    if key in players:
        if key not in player_usage:
            player_usage[key] = {'player_info': players[key],
                                 'total_games': 0, 'total_time': 0, 'hero_usage': {}}
            player_usage[key]['team_info'] = {team_key: teams_by_id[players[key]
                                                                    ['team']['id']][team_key] for team_key in competitors_keys}
            player_usage[key]['team_info']['players'] = []
            player_usage[key]['hero_usage'] = {}
            player_usage[key]['id'] = players[key]['player']['id']
        hero_key = player_hero['nameCSFriendly'].replace(
            'soldier76', 'soldier-76')
        if hero_key not in player_usage[key]['hero_usage']:
            player_usage[key]['hero_usage'][hero_key] = {'games': 0, 'time': 0}
        player_usage[key]['total_games'] += int(player_hero['gameNumber'])
        player_usage[key]['total_time'] += int(player_hero['timePlayed'])
        player_usage[key]['hero_usage'][hero_key]['games'] += int(
            player_hero['gameNumber'])
        player_usage[key]['hero_usage'][hero_key]['time'] += int(
            player_hero['timePlayed'])

player_pick_rate = []
player_pick_rate_dict = {}
for key, player_hero in player_usage.items():
    for hero, usage in player_hero['hero_usage'].items():
        usage['game_percent'] = float(
            usage['games']) / player_hero['total_games']
        usage['game_percent_str'] = str(
            int(usage['game_percent'] * 1000)/10.0) + '%'
        usage['time_percent'] = float(
            usage['time']) / player_hero['total_time']
        usage['time_percent_str'] = str(
            int(usage['time_percent'] * 1000)/10.0) + '%'

    player_pick_rate.append(player_hero)
    player_pick_rate_dict[key] = player_hero

for item in player_ranks:
    item['pick_rate'] = player_pick_rate_dict[key]


team_hero_keys = ['gameNumber', 'roundtype', 'team', 'tcString',
                  'gameWasPlayed', 'map', 'maptype', 'timePlayed', 'matchID']
team_heros = load_json('stats/team_heros.json')
team_usage = {}
for team_hero in team_heros:
    key = team_hero['team']
    if key not in team_usage:
        team_usage[key] = {'total_games': 0, 'total_time': 0, 'hero_usage': {
        }, 'id': name_mapping[winstonlab_teams[team_hero['team']]]}
        team_usage[key]['team_info'] = {
            team_key: teams[name_mapping[winstonlab_teams[team_hero['team']]]][team_key] for team_key in competitors_keys}
        team_usage[key]['team_info']['players'] = []
        team_usage[key]['tcString'] = {}
    hero_key = team_hero['tcString'].replace('soldier76', 'soldier-76')
    if hero_key not in team_usage[key]['hero_usage']:
        team_usage[key]['hero_usage'][hero_key] = {'games': 0, 'time': 0}
    team_usage[key]['total_games'] += int(team_hero['gameNumber'])
    team_usage[key]['total_time'] += int(team_hero['timePlayed'])
    team_usage[key]['hero_usage'][hero_key]['games'] += int(
        team_hero['gameNumber'])
    team_usage[key]['hero_usage'][hero_key]['time'] += int(
        team_hero['timePlayed'])

team_pick_rate = []
for key, team_hero in team_usage.items():
    for hero, usage in team_hero['hero_usage'].items():
        usage['game_percent'] = float(
            usage['games']) / team_hero['total_games']
        usage['game_percent_str'] = str(
            int(usage['game_percent'] * 1000)/10.0) + '%'
        usage['time_percent'] = float(
            usage['time']) / team_hero['total_time']
        usage['time_percent_str'] = str(
            int(usage['time_percent'] * 1000)/10.0) + '%'
    team_pick_rate.append(team_hero)

write_json('data/team_hero_stats.json', team_hero_stats)
write_json('data/composition_stats.json', composition_stats)
write_json('data/player_hero_stats.json', player_hero_stats)
write_json('data/player_stats.json', player_stats)
write_json('data/player_ranks.json', player_ranks)
write_json('data/hero_ranks.json', hero_ranks)
write_json('data/player_pick_rate.json', player_pick_rate)
write_json('data/team_pick_rate.json', team_pick_rate)
