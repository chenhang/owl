#-*- encoding:utf-8 -*-
from requests_html import HTMLSession
from util import *


def lab_id(id):
    return "_winstonslab_" + str(id) + "_"


def owl_index_url(event_id=86):
    return "https://www.winstonslab.com/events/event.php?id=" + str(event_id)


def match_url(match_id):
    return "https://www.winstonslab.com/matches/match.php?id=" + str(match_id)


def player_stats_url(event_id=86):
    return "https://www.winstonslab.com/lib/playerStatsSection.php?event%5B%5D=" + str(event_id)


def hero_stats_url():
    return "https://www.winstonslab.com/lib/heroStatsSectionFunctionUser.php"


def player_rank_url(event_id=86):
    return "https://www.winstonslab.com/player_rankings/singleEvent.php?id=" + str(event_id)


def get_teams_and_matches():
    session = HTMLSession()
    res = session.get(owl_index_url())
    res.html.render(timeout=60)
    match_rows = res.html.find(
        '.tab-pane#past')[0].find('table')[0].find('.past-matches-row')
    updated = True
    # TODO get match data in future
    # for row in match_rows:
    #     if parse_match_row(row):
    #         updated = True
    if updated:
        teams = {td.text: td.absolute_links.pop()
                 for td in res.html.find('td.team')}
        write_json('stats/team_hero_stats.json',
                   [parse_team(team_name, team_url) for team_name, team_url in teams.items()])


def get_event_player_rank():
    session = HTMLSession()
    res = session.get(player_rank_url())
    table = res.html.find('table.ranking-table', first=True)
    player_ranks = []
    hero_ranks = []
    for tr in table.find('tr')[2:]:

        overall_rank = int(tr.find('td.rank', first=True).text)
        overall_rating = int(tr.find('.rating-number', first=True).text)
        team_name = tr.find('.small-team-logo',
                            first=True).attrs['title'].split(': ')[-1]
        stars = int(tr.find(
            '.star-rating', first=True).attrs['class'][-1].replace('star', '').split('-')[0])
        info_div, heros_div = tr.find('.team-info-td > div')
        name = info_div.find('a', first=True).text
        time, sos_rank, win_percent = [div.text.split(
            ': ')[-1] for div in info_div.find('.secondary-stats')]
        rank_data = {'overall_rank': overall_rank, 'overall_rating': overall_rating, 'team_name': team_name,
                     'stars': stars, 'name': name, 'time': time, 'sos_rank': int(sos_rank),
                     'win_percent': win_percent, 'hero_ranks': []}
        for span in heros_div.find('span.secondary-ranking'):
            hero_name = span.attrs['title'].split(' Rank:')[0].lower()
            hero_rank_by_total, hero_rating, hero_time, hero_win_percent = [
                text.split(': ')[-1] for text in span.attrs['title'].split('\n')]
            hero_rank, total_count = hero_rank_by_total.split('/')
            hero_rank_data = {'hero_name': hero_name, 'hero_rank_by_total': hero_rank_by_total,
                              'hero_rating': int(hero_rating), 'hero_time': hero_time,
                              'hero_win_percent': hero_win_percent, 'hero_rank': int(hero_rank),
                              'total_count': int(total_count), 'name': name, 'overall_rank': overall_rank,
                              'overall_rating': overall_rating, 'team_name': team_name, 'stars': stars, }
            hero_ranks.append(hero_rank_data)
            rank_data['hero_ranks'].append(hero_rank_data)
        player_ranks.append(rank_data)
    write_json('stats/player_ranks.json', player_ranks)
    write_json('stats/hero_ranks.json', hero_ranks)


def get_hero_stats():
    hero_stats = []
    session = HTMLSession()
    res = session.post(hero_stats_url(), data={
                       'event[]': 86, 'teamcompTypes': 1})
    player_heros = []
    team_heros = []

    # ['gameNumber', 'roundtype', 'player', 'team', 'hero',
    # 'timePlayed', 'matchID', 'playerPic', 'playerName', 'teamPic',
    # 'nameCSFriendly', 'map', 'teamName']
    for result in res.html.search_all("heroStatsArr.concat({})"):
        player_heros += json.loads(result[0])

    # keys = ['gameNumber', 'roundtype', 'team', 'tcString',
    # 'gameWasPlayed', 'map', 'maptype', 'timePlayed', 'matchID']
    for result in res.html.search_all("teamcompsArr.concat({})"):
        team_heros += json.loads(result[0])
    write_json('stats/player_heros.json', player_heros)
    write_json('stats/team_heros.json', team_heros)


def get_player_stats():
    player_stats = []
    composition_stats = []
    player_hero_stats = []
    session = HTMLSession()
    res = session.get(player_stats_url())
    map_divs = res.html.find('.map-wrapper')
    table_divs = res.html.find('.side-by-side-stats')
    category = 'Allmaps'
    for div in res.html.find('.match-div > div'):
        if 'map-wrapper' in div.attrs.get('class', []):
            map_name = div.find(
                '.label-info', first=True).text.lower().replace(' ', '_')
        elif 'side-by-side-stats' in div.attrs.get('class', []):
            composition_stat, hero_stat = parse_overall_hero_stat_div(
                div, category=category, map_name=map_name)
            composition_stats += composition_stat
            player_hero_stats += hero_stat
            player_stats += parse_overall_stat_div(
                div, category=category, map_name=map_name)
        else:
            category = div.text
    write_json('stats/composition_stats.json', composition_stats)
    write_json('stats/player_hero_stats.json', player_hero_stats)
    write_json('stats/player_stats.json', player_stats)


def parse_team(team_name, team_url):
    session = HTMLSession()
    return {'id': team_url.split('id=')[-1], 'name': team_name, 'heros': [{'win_rate': div.text, 'heros': [span.attrs['title'].replace('soldier76', 'soldier-76') for span in div.find('span')]}
                                                                          for div in session.get(team_url).html.find('.team-comp-wrapper > .team-comp')]}


def parse_match_row(row):
    match_path = os.path.join(
        'stats', 'matches', row.attrs['matchid'] + '.json')
    if os.path.exists(match_path):
        return False
    match = {}
    session = HTMLSession()
    match_res = session.get(match_url(row.attrs['matchid']))
    render_result = match_res.html.render(timeout=600)
    print(render_result)
    team_names = [{'name': team_name_div.text,
                   'id': team_name_div.links.pop().split('id=')[-1]} for team_name_div in match_res.html.find('.names-and-score', first=True).find('div')[1::2]]
    maps = []
    for map_div in match_res.html.find('.map-wrapper'):
        map_data = {'name': map_div.find(
            '.mapname', first=True).text, 'teams': []}
        mapping = {'name': 3, 'score': 4,
                   'progress': 5, 'fights': 6, 'kills': 7}
        for i in range(1, 3):
            team_data = {}
            for key, index in mapping.items():
                team_data[key] = map_div.find('div')[index].text.split('\n')[i]
            map_data['teams'].append(team_data)
        maps.append(map_data)
    stat_divs = match_res.html.find('.side-by-side-stats')
    overall_stats = parse_stat_div(stat_divs.pop(0))
    for i, map_stat_div in enumerate(stat_divs):
        maps[i]['stats'] = parse_stat_div(map_stat_div)

    hero_stats = parse_hero_stat_div(match_res.html.find(
        '#allMapsAllRoundsAllTeams', first=True))
    hero_stats_by_team = []
    # TODO FIX the script problem
    # for team in team_names:
    #     hero_stats_by_team.append(parse_hero_stat_div(match_res.html.find(
    #         '#allMapsAllRoundsTeam' + team['id'], first=True)))
    write_json(match_path, {'maps': maps, 'stats': overall_stats, 'hero_stats': hero_stats,
                            'hero_stats_by_team': hero_stats_by_team,
                            'teams': team_names, 'date': row.find('td')[0].text})
    return True


# side-by-side-stats in match page
def parse_hero_stat_div(hero_stat_div):
    print()
    data = {'full_time': hero_stat_div.find(
        '.full-time-played', first=True).attrs['time'], 'heros': [], 'compositions': []}
    left, right = hero_stat_div.find('.no-padding-when-big')
    for div in left.find('div.progress.progress-hero'):
        name, usage = div.text.split('\n')
        use_time, percent = usage.replace(')', '').split(' (')
        data['heros'].append(
            {'name': name, 'time': use_time, 'percent': percent})
    for div in right.find('.tct-bar-row'):
        use_time, percent = div.find(
            '.progress', first=True).attrs['title'].replace(')', '').split(' (')
        [img.attrs['title'] for img in div.find('img')]
        data['compositions'].append(
            {'compositions': [img.attrs['title'] for img in div.find('img')], 'time': use_time, 'percent': percent})
    return data


# side-by-side-stats in event index page
def parse_overall_hero_stat_div(stat_div, category="", map_name=""):
    composition_stats = []
    hero_stats = []
    # TODO ADD suport to more divs
    composition_divs, hero_divs = stat_div.find('.tc-wrapper-wrapper')[:2]
    for composition_div in composition_divs.find('.team-comp'):
        composition_stats.append({'composition': [img.attrs['title'] for img in composition_div.find(
            'img')], 'percent': composition_div.text, 'category': category, 'map_name': map_name})
    for hero_div in hero_divs.find('.team-comp'):
        hero_stats.append({'heros': [img.attrs['src'].split('/')[-1].replace(
            '_full.png', '') for img in hero_div.find('img')],
            'percent': hero_div.text, 'category': category, 'map_name': map_name})
    return composition_stats, hero_stats


# side-by-side-stats in event index page
def parse_overall_stat_div(stat_div, category="", map_name="", headers=['name', 'map_played', 'kills', 'deathes', 'plusminus',
                                                                        'ultimates', 'percent_of_team', 'hero_kd', 'role']):
    data = []
    display_types = ['avg/min', 'avg/game', 'total']
    for table in stat_div.find('table'):
        players = []
        for i, tbody in enumerate(table.find('tbody')):
            for tr in tbody.find('tr'):
                tds = tr.find('td')
                player_data = list(zip(headers, [td.text for td in tds]))
                player_data += [('id', tds[0].links.pop().split('id=')[-1]), ('category', category),
                                ('display_type',
                                 display_types[i]), ('map_name', map_name),
                                ('hero_kd', {div.find(
                                    'img', first=True).attrs['title'].lower().replace('.', '').replace(': ', '-'): div.text for div in tr.find('td.hero-kdu-td > div')})]
                players.append(dict(player_data))
            data += players
    return data


# side-by-side-stats in match page
def parse_stat_div(stat_div, headers=['name', 'kills', 'deathes', 'plusminus',
                                      'ultimates', 'firstbloods', 'rating']):
    data = []
    for table in stat_div.find('table'):
        players = []
        for tr in table.find('tbody', first=True).find('tr'):
            tds = tr.find('td')
            player_data = dict(zip(headers, [td.text for td in tds[:-1]]))
            player_data['id'] = tds[0].links.pop().split('id=')[-1]
            players.append(player_data)
        data.append(players)
    return data


if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR)
    get_player_stats()
    get_hero_stats()
    get_teams_and_matches()
    get_event_player_rank()
