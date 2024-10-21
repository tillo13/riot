from collections import defaultdict
import os
import json
from tabulate import tabulate

VERBOSE_MODE = False
SORT_BY = "15+Kills_rate"  # You can set this to any column name based on which you want to sort

SORT_MAPPING = {
    "champion": 0,
    "total_games": 1,
    "wins": 2,
    "losses": 3,
    "win_rate": 4,
    "pentakills": 5,
    "win_rate_penta": 6,
    "quadrakills": 7,
    "win_rate_quad": 8,
    "triple_kills": 9,
    "double_kills": 10,
    "single_kills": 11,
    "max_kill_streak": 12,
    "15+Kills": 13,
    "15+Kills_rate": 14
}

def get_all_json_files(directory):
    return [os.path.join(directory, file) for file in os.listdir(directory) if file.endswith('.json')]

def normalize_summoner_name(name):
    return name.lower().replace(" ", "")

def split_characters_in_names(names):
    return [normalize_summoner_name(name) for name in names]

def process_summoner(target_summoner_name, json_files):
    normalized_target = normalize_summoner_name(target_summoner_name)

    total_games = 0
    total_wins = 0
    total_pentakills = 0
    total_quadrakills = 0
    total_triple_kills = 0
    total_double_kills = 0
    total_single_kills = 0
    games_with_15_plus_kills = 0

    champion_stats = defaultdict(lambda: {
        "count": 0,
        "wins": 0,
        "losses": 0,
        "pentakills": 0,
        "pentakill_wins": 0,
        "quadrakills": 0,
        "quadrakill_wins": 0,
        "triple_kills": 0,
        "double_kills": 0,
        "single_kills": 0,
        "maxKillStreak": 0,
        "15+Kills": 0,
    })

    for json_file in json_files:
        with open(json_file, "r") as file:
            match_data = json.load(file)

        participants = match_data["info"]["participants"]
        target_participant = None

        for participant in participants:
            summoner_name = participant["summonerName"]
            normalized_summoner_name = normalize_summoner_name(summoner_name)
            if normalized_summoner_name == normalized_target:
                target_participant = participant
                break

        if target_participant:
            total_games += 1
            champ_name = target_participant.get("championName", str(target_participant["championId"]))
            win = target_participant["win"]

            # Collect stats
            kills = target_participant["kills"]
            pentakills = target_participant.get("pentaKills", 0)
            quadrakills = target_participant.get("quadraKills", 0)
            triple_kills = target_participant.get("tripleKills", 0)
            double_kills = target_participant.get("doubleKills", 0)
            single_kills = kills - (double_kills + triple_kills + quadrakills + pentakills)
            max_kill_streak = target_participant.get("largestKillingSpree", 0)

            total_pentakills += pentakills
            total_quadrakills += quadrakills
            total_triple_kills += triple_kills
            total_double_kills += double_kills
            total_single_kills += max(single_kills, 0)
            total_wins += 1 if win else 0
            if kills >= 15:
                games_with_15_plus_kills += 1

            champion_stats[champ_name]["count"] += 1
            champion_stats[champ_name]["pentakills"] += pentakills
            champion_stats[champ_name]["quadrakills"] += quadrakills
            champion_stats[champ_name]["triple_kills"] += triple_kills
            champion_stats[champ_name]["double_kills"] += double_kills
            champion_stats[champ_name]["single_kills"] += max(single_kills, 0)
            champion_stats[champ_name]["maxKillStreak"] = max(champion_stats[champ_name]["maxKillStreak"], max_kill_streak)
            if kills >= 15:
                champion_stats[champ_name]["15+Kills"] += 1

            if win:
                champion_stats[champ_name]["wins"] += 1
            else:
                champion_stats[champ_name]["losses"] += 1

            if pentakills > 0 and win:
                champion_stats[champ_name]["pentakill_wins"] += 1

            if quadrakills > 0 and win:
                champion_stats[champ_name]["quadrakill_wins"] += 1

    # Prepare the champion stats for tabulation
    champion_stats_list = []
    for champ, stats in champion_stats.items():
        win_rate = (stats["wins"] / stats["count"]) * 100 if stats["count"] > 0 else 0
        win_rate_penta = (stats["pentakill_wins"] / stats["pentakills"]) * 100 if stats["pentakills"] > 0 else 0
        win_rate_quad = (stats["quadrakill_wins"] / stats["quadrakills"]) * 100 if stats["quadrakills"] > 0 else 0
        kills_15_plus_rate = (stats["15+Kills"] / stats["count"]) * 100 if stats["count"] > 0 else 0

        champion_stats_list.append((
            champ, stats["count"], stats["wins"], stats["losses"], win_rate,
            stats["pentakills"], win_rate_penta,
            stats["quadrakills"], win_rate_quad,
            stats["triple_kills"], stats["double_kills"], stats["single_kills"], 
            stats["maxKillStreak"], stats["15+Kills"], kills_15_plus_rate
        ))

    # Sort by the selected column
    champion_stats_list.sort(key=lambda x: -x[SORT_MAPPING[SORT_BY]])

    overall_win_rate = (total_wins / total_games) * 100 if total_games > 0 else 0
    overall_15_kills_rate = (games_with_15_plus_kills / total_games) * 100 if total_games > 0 else 0

    return target_summoner_name, total_games, total_pentakills, total_quadrakills, total_triple_kills, total_double_kills, total_single_kills, champion_stats_list, overall_win_rate, overall_15_kills_rate, games_with_15_plus_kills, total_wins

def main():
    matches_directory = "matches/"
    json_files = get_all_json_files(matches_directory)

    if not json_files:
        print("No match files found in the directory.")
        return

    # List of summoner names to process
    ANDYS_SUMMONERS = [
        "anonobot", "cardyflower", "statfame", "certainlylukey", "milltill005", "lillabryar"
    ]
    LUKES_SUMMONERS = ["britneyphi"]

    # Normalize and split characters in summoner names
    ANDYS_SUMMONERS = split_characters_in_names(ANDYS_SUMMONERS)
    LUKES_SUMMONERS = split_characters_in_names(LUKES_SUMMONERS)

    results = []
    luke_winning_games = 0
    andy_luke_correlation = 0

    for summoner_name in ANDYS_SUMMONERS + LUKES_SUMMONERS:
        if VERBOSE_MODE:
            print(f"\nProcessing summoner: {summoner_name}")
        else:
            print(f"Processing {summoner_name}...")

        result = process_summoner(summoner_name, json_files)
        results.append(result)

    for json_file in json_files:
        with open(json_file, "r") as file:
            match_data = json.load(file)

        participants = match_data["info"]["participants"]
        
        andy_achieved_15_kills = False
        luke_wins = False

        for participant in participants:
            summoner_name = participant["summonerName"]
            normalized_summoner_name = normalize_summoner_name(summoner_name)
            if normalized_summoner_name in ANDYS_SUMMONERS and participant["kills"] >= 15:
                andy_achieved_15_kills = True
            if normalized_summoner_name in LUKES_SUMMONERS and participant["win"]:
                luke_wins = True
                luke_winning_games += 1

        if andy_achieved_15_kills and luke_wins:
            andy_luke_correlation += 1

    # Aggregate results for Andy's summoners
    andy_aggregated_stats = {
        "total_games": 0,
        "total_pentakills": 0,
        "total_quadrakills": 0,
        "total_triple_kills": 0,
        "total_double_kills": 0,
        "total_single_kills": 0,
        "total_wins": 0,
        "games_with_15_plus_kills": 0
    }

    andys_champion_stats = defaultdict(lambda: {
        "count": 0,
        "wins": 0,
        "losses": 0,
        "pentakills": 0,
        "pentakill_wins": 0,
        "quadrakills": 0,
        "quadrakill_wins": 0,
        "triple_kills": 0,
        "double_kills": 0,
        "single_kills": 0,
        "maxKillStreak": 0,
        "15+Kills": 0,
        "15+Kills%": 0
    })

    for result in results:
        (summoner_name, total_games, total_pentakills, total_quadrakills,
         total_triple_kills, total_double_kills, total_single_kills, champion_stats_list,
         overall_win_rate, overall_15_kills_rate, games_with_15_plus_kills, total_wins) = result

        if summoner_name in ANDYS_SUMMONERS:
            andy_aggregated_stats["total_games"] += total_games
            andy_aggregated_stats["total_pentakills"] += total_pentakills
            andy_aggregated_stats["total_quadrakills"] += total_quadrakills
            andy_aggregated_stats["total_triple_kills"] += total_triple_kills
            andy_aggregated_stats["total_double_kills"] += total_double_kills
            andy_aggregated_stats["total_single_kills"] += total_single_kills
            andy_aggregated_stats["total_wins"] += total_wins
            andy_aggregated_stats["games_with_15_plus_kills"] += games_with_15_plus_kills

            # Aggregate the champion stats for all of Andy's summoners
            for champ, count, wins, losses, win_rate, pentakills, win_rate_penta, quadrakills, win_rate_quad, triple_kills, double_kills, single_kills, max_kill_streak, kills_15_plus, kills_15_plus_rate in champion_stats_list:
                andys_champion_stats[champ]["count"] += count
                andys_champion_stats[champ]["wins"] += wins
                andys_champion_stats[champ]["losses"] += losses
                andys_champion_stats[champ]["pentakills"] += pentakills
                andys_champion_stats[champ]["pentakill_wins"] += pentakills * (win_rate_penta / 100) if pentakills > 0 else 0
                andys_champion_stats[champ]["quadrakills"] += quadrakills
                andys_champion_stats[champ]["quadrakill_wins"] += quadrakills * (win_rate_quad / 100) if quadrakills > 0 else 0
                andys_champion_stats[champ]["triple_kills"] += triple_kills
                andys_champion_stats[champ]["double_kills"] += double_kills
                andys_champion_stats[champ]["single_kills"] += single_kills
                andys_champion_stats[champ]["maxKillStreak"] = max(andys_champion_stats[champ]["maxKillStreak"], max_kill_streak)
                andys_champion_stats[champ]["15+Kills"] += kills_15_plus

        # Print individual stats for each summoner
        print(f"\n{summoner_name} champ counts (total games played: {total_games}, "
              f"Penta: {total_pentakills}, Quadra: {total_quadrakills}, "
              f"Triple: {total_triple_kills}, Double: {total_double_kills}, "
              f"Kills: {total_single_kills}, Win %: {overall_win_rate:.2f}%, "
              f"15+Kills %: {overall_15_kills_rate:.2f}%):")

        table_headers = [
            "Champion", "Total Games", "Wins", "Losses", "Win %",
            "Penta", "Win% Penta", "Quadra", "Win% Quad",
            "Triple", "Double", "Kills", "maxKillStreak", "15+Kills", "15+Kills%"
        ]

        table_data = [
            (champ, count, wins, losses, f"{win_rate:.2f}%", pentakills, f"{win_rate_penta:.2f}%", quadrakills, f"{win_rate_quad:.2f}%", triple_kills, double_kills, single_kills, max_kill_streak, kills_15_plus, f"{kills_15_plus_rate:.2f}%")
            for champ, count, wins, losses, win_rate, pentakills, win_rate_penta, quadrakills, win_rate_quad, triple_kills, double_kills, single_kills, max_kill_streak, kills_15_plus, kills_15_plus_rate in champion_stats_list
        ]

        print(tabulate(table_data, headers=table_headers, tablefmt="pretty"))

    # Print aggregated results for Andy's summoners
    print("\nAggregate stats for Andy's Summoners:")
    total_win_rate = (andy_aggregated_stats["total_wins"] / andy_aggregated_stats["total_games"]) * 100 if andy_aggregated_stats["total_games"] > 0 else 0
    total_15_kills_rate = (andy_aggregated_stats["games_with_15_plus_kills"] / andy_aggregated_stats["total_games"]) * 100 if andy_aggregated_stats["total_games"] > 0 else 0
    print(f"Total games played: {andy_aggregated_stats['total_games']}, "
          f"Penta: {andy_aggregated_stats['total_pentakills']}, Quadra: {andy_aggregated_stats['total_quadrakills']}, "
          f"Triple: {andy_aggregated_stats['total_triple_kills']}, Double: {andy_aggregated_stats['total_double_kills']}, "
          f"Kills: {andy_aggregated_stats['total_single_kills']}, Win %: {total_win_rate:.2f}%, "
          f"15+Kills %: {total_15_kills_rate:.2f}%")

    # Prepare the aggregated champion stats for tabulation
    aggregated_champion_stats_list = []
    for champ, stats in andys_champion_stats.items():
        win_rate = (stats["wins"] / stats["count"]) * 100 if stats["count"] > 0 else 0
        win_rate_penta = (stats["pentakill_wins"] / stats["pentakills"]) * 100 if stats["pentakills"] > 0 else 0
        win_rate_quad = (stats["quadrakill_wins"] / stats["quadrakills"]) * 100 if stats["quadrakills"] > 0 else 0
        kills_15_plus_rate = (stats["15+Kills"] / stats["count"]) * 100 if stats["count"] > 0 else 0

        aggregated_champion_stats_list.append((
            champ, stats["count"], stats["wins"], stats["losses"], win_rate,
            stats["pentakills"], win_rate_penta,
            stats["quadrakills"], win_rate_quad,
            stats["triple_kills"], stats["double_kills"], stats["single_kills"], 
            stats["maxKillStreak"], stats["15+Kills"], kills_15_plus_rate
        ))

    aggregated_champion_stats_list.sort(key=lambda x: -x[SORT_MAPPING[SORT_BY]])

    # Print combined champion stats for Andy's Summoners
# Print combined champion stats for Andy's Summoners
    print("\nCombined champion stats for Andy's Summoners:")
    table_headers = [
        "Champion", "Total Games", "Wins", "Losses", "Win %",
        "Penta", "Win% Penta", "Quadra", "Win% Quad",
        "Triple", "Double", "Kills", "maxKillStreak", "15+Kills", "15+Kills%"
    ]
    table_data = [
        (champ, count, wins, losses, f"{win_rate:.2f}%", pentakills, f"{win_rate_penta:.2f}%", quadrakills, f"{win_rate_quad:.2f}%", triple_kills, double_kills, single_kills, max_kill_streak, kills_15_plus, f"{kills_15_plus_rate:.2f}%")
        for champ, count, wins, losses, win_rate, pentakills, win_rate_penta, quadrakills, win_rate_quad, triple_kills, double_kills, single_kills, max_kill_streak, kills_15_plus, kills_15_plus_rate in aggregated_champion_stats_list
    ]
    print(tabulate(table_data, headers=table_headers, tablefmt="pretty"))

    # Calculate the correlation rate based on Luke’s total wins
    total_luke_wins = int(luke_winning_games)
    print(f"\nCorrelation of games where Luke wins and Andy's summoners get 15+ kills: {andy_luke_correlation} out of {total_luke_wins}.")
    correlation_rate = (andy_luke_correlation / total_luke_wins) * 100 if total_luke_wins else 0
    print(f"Correlation rate: {correlation_rate:.2f}%")

if __name__ == "__main__":
    main()