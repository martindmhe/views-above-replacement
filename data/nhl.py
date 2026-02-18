import csv

from datetime import datetime
from nhlpy import NHLClient

LFR_TO_SEASON = {
    "19": "20252026",
    "18": "20242025",
    "17": "20232024",
    "16": "20222023",
    "15": "20212022",
    "14": "20202021",
}

INCLUDED_SEASONS = ["20202021", "20212022", "20222023", "20232024", "20242025"]

client = NHLClient()

season_schedules = {}

def build_views_map():
    steve_map = {
        "20252026": {}, 
        "20242025": {},
        "20232024": {},
        "20222023": {},
        "20212022": {},
        "20202021": {},
    }

    # 2025-11-12,111385,"LFR19 - Game 17 - GAVIN - Maple Leafs 3, Bruins 5",iqnUb6lNUjA

    with open("data/steve_dangle_videos.csv", "r") as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0] == "date":
                continue
            title = row[2]
            views = row[1]

            lfr_number = title.split(" ")[0].split("LFR")[1].split("-")[0].strip()
            if not lfr_number:
                print(f"No LFR number found for {title}")
                continue

            season = LFR_TO_SEASON[lfr_number]

            game_number = title.split("Game ")[1].split("-")[0].strip()
            if not game_number:
                print(f"No game number found for {title}")
                continue
            steve_map[season][int(game_number)] = views

    return steve_map


# build dict that maps game number of each season to the game id 
def build_game_map():
    game_map = {
        "20252026": {},
        "20242025": {},
        "20232024": {},
        "20222023": {},
        "20212022": {},
        "20202021": {},
    }


    for season in INCLUDED_SEASONS:
        current_game_number = 1
        full_schedule = client.schedule.team_season_schedule(team_abbr="TOR", season=season)
        season_schedules[season] = full_schedule
        games = full_schedule.get('games')
        if games:
            for game in games:
                # not regular season games
                if game.get('gameType') != 2:
                    continue
                game_map[season][current_game_number] = game.get('id')
                current_game_number += 1
        print(f"Built game map for {season}")
        # print(game_map[season])

    return game_map

# take game id -> return the data we will feed into our model as a dict
# caller will use to construct a dataframe/csv
def process_game_data(game_id: int) -> dict:
    game_data = client.game_center.match_up(game_id)

    away_team = game_data.get('awayTeam')
    home_team = game_data.get('homeTeam')

    isHome = True
    away_team_name = away_team.get('abbrev')
    leafs_goals = home_team.get('score')
    away_team_goals = away_team.get('score')

    if away_team.get('abbrev') == 'TOR':
        isHome = False
        away_team_name = home_team.get('abbrev')

        leafs_goals = away_team.get('score')
        away_team_goals = home_team.get('score')

    isLoss = leafs_goals < away_team_goals
    max_leafs_blown_leads = 0
    max_leafs_lead = 0


    summary = game_data.get('summary')

    scoring = summary.get('scoring')
    # penalties = summary.get('penalties')

    # penalties metrics? 

    current_leafs_score = 0
    current_away_score = 0

    for period in scoring:
        for goal in period.get('goals'):
            if goal.get('teamAbbrev').get('default') == 'TOR':
                current_leafs_score += 1
                max_leafs_lead = max(max_leafs_lead, current_leafs_score - current_away_score)
            else:
                current_away_score += 1
                if current_leafs_score == current_away_score:
                    max_leafs_blown_leads = max(max_leafs_blown_leads, max_leafs_lead)
                    max_leafs_lead = 0

    return {
        "game_id": game_id,
        "game_date": game_data.get("gameDate"),
        "season": game_data.get("season"),
        "max_leafs_blown_leads": max_leafs_blown_leads,
        "is_loss": isLoss,
        "leafs_goals": leafs_goals,
        "opponent_goals": away_team_goals,
        "is_home": isHome,
        "opponent": away_team_name,
        "opponent_hatred_score": get_opponent_magnitude(away_team_name, game_data.get("gameDate")),
        "goal_differential": leafs_goals - away_team_goals,
    }


CSV_COLUMNS = [
    "game_id",
    "season",
    "game_number",
    "game_date",
    "opponent",
    "is_home",
    "leafs_goals",
    "opponent_goals",
    "goal_differential",
    "is_loss",
    "max_leafs_blown_leads",
    "opponent_hatred_score",
    "views"
]

# fuck these teams
opponent_magnitude = {
    'BOS': 4, 'MTL': 4, 
    'OTT': 3,
    'DET': 2, 'NYR': 2, 'EDM': 2, 'CHI': 2,
    'BUF': 2, 'VAN': 2, 'WPG': 2, 'CGY': 2,
    'WSH': 2, 'VGK': 2, 'NYI': 2,
}

timestamped_opponent_magnitude = {
    'FLA': [
        {
            'date': '2025-05-18',
            'magnitude': 4,
        },
        {
            'date': '2023-05-12',
            'magnitude': 2,
        },
    ],
    'TBL': [
        {
            'date': '2022-04-23',
            'magnitude': 3,
        },
    ]
}

def get_opponent_magnitude(opponent: str, game_date: str) -> int:
    if opponent in opponent_magnitude:
        return opponent_magnitude[opponent]
    for timestamp in timestamped_opponent_magnitude.get(opponent, []):
        if datetime.strptime(game_date, "%Y-%m-%d") > datetime.strptime(timestamp.get('date'), "%Y-%m-%d"):
            return timestamp.get('magnitude')
    return 1

def build_games_csv(output_path: str = "data/games.csv") -> None:
    game_map = build_game_map()
    views_map = build_views_map()

    rows = []
    for season in INCLUDED_SEASONS:
        for game_number, game_id in sorted(game_map[season].items(), key=lambda x: x[0]):
            try:
                data = process_game_data(game_id)
                data["game_number"] = game_number
                data["views"] = views_map[season].get(game_number, -1)

                rows.append([str(data.get(c, "")) for c in CSV_COLUMNS])
            except Exception as e:
                print(f"Skip game_id={game_id} season={season} game_number={game_number}: {e}")

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_COLUMNS)
        writer.writerows(rows)
    

def main():
    game_map = build_game_map()

    print(game_map)

    with open("data/steve_dangle_videos.csv", "r") as f:
        reader = csv.reader(f)
        for row in reader:
            date, views, title, video_id = row
            if row[0] == "date":
                continue

            lfr_number = title.split(" ")[0].split("LFR")[1].split("-")[0].strip()
            print(lfr_number)
            if not lfr_number:
                print(f"No LFR number found for {title}")

                continue
            season = LFR_TO_SEASON[lfr_number]

            # LFR15 - Game 15 - Red (Light) - CGY 1, TOR 2 (OT)
            game_number = title.split("Game ")[1].split("-")[0].strip()
            if not game_number:
                print(f"No game number found for {title}")
                continue

            game_id = game_map[season].get(int(game_number))

            if not game_id:
                print(f"No game id found for {title}")
                continue
            print(game_id)

            game_data = process_game_data(game_id)
            print(game_data)

            
            break

if __name__ == "__main__":
    build_games_csv()
