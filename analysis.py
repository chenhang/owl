from util import *


def match_paths():
    paths = []
    for match_name in os.listdir('stats/matches'):
        if '.json' in match_name:
            match_path = os.path.join('stats/matches', match_name)
            paths.append(match_path)
    return paths


matches = []
for match_path in match_paths():
    data = load_json(match_path)
    date_format = '%H:%M - %d/%m/%Y' if '/' in data['date'] else '%H:%M - %b %d, %Y'
    date = datetime.datetime.strptime(data['date'], date_format).timestamp()
    for map_data in data['maps']:
        ranks = [int(team['score']) for team in map_data['teams']]
        team_names = [team['name'] for team in map_data['teams']]
        teams = [[player['name'] for player in stats] for stats in map_data['stats']]
        matches.append({'date': date, 'ranks': ranks, 'teams': teams, 'team_names': team_names})

write_json('stats/matches.json', sorted(matches, key=lambda x:x['date']))