import os
import pickle
import pandas as pd
from supabase import create_client, Client
from nhlpy import NHLClient
from dotenv import load_dotenv
from pathlib import Path

client = NHLClient()

TOR_ABBREV = "TOR"

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")


def add_daily_game(supabase: Client):

    existing = supabase.table("views").select("game_id").execute()
    existing_ids = {int(row["game_id"]) for row in existing.data}

    games_data = client.schedule.daily_schedule()
    date = games_data.get("date")

    games = games_data.get("games")

    for game in games:
        home_team = game.get("homeTeam")
        away_team = game.get("awayTeam")
        if not (home_team.get("abbrev") == TOR_ABBREV or away_team.get("abbrev") == TOR_ABBREV):
            continue

        print(f"Processing TOR game {game.get('id')}")
        
        is_home = False
        if home_team.get("abbrev") == TOR_ABBREV:
            is_home = True

        opponent_abbrev = away_team.get("abbrev") if is_home else home_team.get("abbrev")

        id = game.get("id")

        if id in existing_ids:
            return id 
        
        supabase.table('views').insert({
            "game_id": id,
            "game_date": date,
            "opponent": opponent_abbrev,
            "is_home": is_home,
        }).execute()
        
        print(f"Inserted views for game {id}")

        return id



def get_standings_data(standings, team_abbrs):
    teams = set(team_abbrs)
    res = {}
    for team in standings:
        teamAbbrev = team["teamAbbrev"]["default"]
        if teamAbbrev in teams:
            res[teamAbbrev] = {
                "pointPctg": team["pointPctg"],
                "gamesPlayed": team["gamesPlayed"],
                "l10Wins": team["l10Wins"],
                "l10Losses": team["l10Losses"],
                "l10OtLosses": team["l10OtLosses"],
                "l10Points": team["l10Points"],
                "l10GamesPlayed": team["l10GamesPlayed"],
                "streakCode": team["streakCode"],
                "streakCount": team["streakCount"],
            }

    return res

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


    # isRival = away_team_name in rival_teams

    isLoss = leafs_goals < away_team_goals
    max_leafs_blown_leads = 0
    max_leafs_lead = 0

    goals_against_while_leading = 0


    summary = game_data.get('summary')

    scoring = summary.get('scoring')
    penalties = summary.get('penalties')

    leafs_penalties = 0
    opponent_penalties = 0
    major_penalties = 0
    misconducts = 0
    fights = 0

    # penalties metrics? 
    for period in penalties:
        for penalty in period.get("penalties"):
            if not penalty:
                continue
            if not penalty.get('teamAbbrev'):
                continue
            if penalty.get('teamAbbrev').get('default') == 'TOR':
                leafs_penalties += 1
            else:
                opponent_penalties += 1

            if penalty.get('duration') == 5 and penalty.get('descKey') != 'fighting':
                major_penalties += 1

            if penalty.get('descKey') == 'misconduct' or penalty.get('descKey') == 'game-misconduct':
                misconducts += 1

            if penalty.get('descKey') == 'fighting':
                fights += 0.5

    current_leafs_score = 0
    current_away_score = 0

    for period in scoring:
        for goal in period.get('goals'):
            if goal.get('teamAbbrev').get('default') == 'TOR':
                current_leafs_score += 1
                max_leafs_lead = max(max_leafs_lead, current_leafs_score - current_away_score)
            else:
                if current_leafs_score > current_away_score:
                    goals_against_while_leading += 1

                current_away_score += 1
                if current_leafs_score == current_away_score:
                    max_leafs_blown_leads = max(max_leafs_blown_leads, max_leafs_lead)
                    max_leafs_lead = 0

    return {
        "game_date": game_data.get("gameDate"),
        "max_leafs_blown_leads": max_leafs_blown_leads,
        "goals_against_while_leading": goals_against_while_leading,
        "is_loss": isLoss,
        "leafs_goals": leafs_goals,
        "opponent_goals": away_team_goals,
        "is_home": isHome,
        "opponent": away_team_name,
        # "is_rival": isRival,
        "goal_differential": leafs_goals - away_team_goals,
        "leafs_penalties": leafs_penalties,
        "opponent_penalties": opponent_penalties,
        "major_penalties": major_penalties,
        "misconducts": misconducts,
        "fights": int(fights),
    }

# calculate views for completed games
def predict_views(game_id: int):

    boxscore = client.game_center.boxscore(game_id)

    if boxscore.get('gameState') != 'OFF':
        print(f"Game {game_id} is not completed")
        return None, None

    print(f"Game {game_id} is completed")

    game_data = client.game_center.match_up(game_id)
    game_date = game_data["gameDate"]

    standings_at_time = client.standings.league_standings(
        date=(pd.to_datetime(game_date) - pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
    )
    standings_data = get_standings_data(standings_at_time["standings"], ["TOR"])
    leafs_standings = standings_data["TOR"]
    leafs_streak = (
        leafs_standings["streakCount"]
        if leafs_standings["streakCode"] == "W"
        else -leafs_standings["streakCount"]
    )

    game_data = process_game_data(game_id)
    total_goals = game_data["leafs_goals"] + game_data["opponent_goals"]

    # Features used by model in dermott.ipynb (training list)
    features = {
        "is_loss": int(game_data["is_loss"]),
        "goal_differential": game_data["goal_differential"],
        "total_goals": total_goals,
        "max_leafs_blown_leads": game_data["max_leafs_blown_leads"],
        "goals_against_while_leading": game_data["goals_against_while_leading"],
        "leafs_streak": leafs_streak,
    }

    model_path = Path(__file__).resolve().parent.parent / "saved_models" / "model.pkl"
    with open(model_path, "rb") as f:
        model = pickle.load(f)

    prediction = model.predict(pd.DataFrame([features]))[0]

    return [prediction, features]

def update():
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")

    supabase: Client = create_client(url, key)

    # check for game today
    add_daily_game(supabase)
     
    # prediction for finished games missing predicted_views
    rows = supabase.table("views").select("game_id").is_("predicted_views", "null").eq("should_predict", True).execute()
    for row in rows.data:
        game_id = row["game_id"]

        boxscore = client.game_center.boxscore(game_id)
        leafs_score = boxscore.get('homeTeam').get('score') if boxscore.get('homeTeam').get('abbrev') == 'TOR' else boxscore.get('awayTeam').get('score')
        opponent_score = boxscore.get('awayTeam').get('score') if boxscore.get('homeTeam').get('abbrev') == 'TOR' else boxscore.get('homeTeam').get('score')
        # + any other main game data we need (not for inference)

        prediction, features = predict_views(game_id)
        
        if prediction is not None:
            supabase.table("views").update(
                {
                    "predicted_views": round(prediction),
                    "features": features,
                    "leafs_score": leafs_score,
                    "opponent_score": opponent_score,
                }
            ).eq("game_id", game_id).execute()
            print(f"Updated predicted_views for game {game_id}: {round(prediction)}")

        
if __name__ == "__main__":
    print("Start LFR update")
    update()
    print("Done")