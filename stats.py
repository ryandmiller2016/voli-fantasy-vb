from flask import Flask, request, jsonify
import json
import requests

app = Flask(__name__)

def process_stats_from_url(file_url):
    """
    Downloads and processes a JSON-style TXT file from a given URL, 
    then extracts statistics and returns structured JSON data.
    """
    try:
        # Download the JSON-TXT file from Bubble’s upload system
        response = requests.get(file_url)
        response.raise_for_status()

        # Parse the JSON content
        data = json.loads(response.text)

        # Team code mapping
        team_code_mapping = {
            "Atlanta Vibe": "ATL",
            "Columbus Fury": "COL",
            "Grand Rapids Rise": "GRR",
            "Indy Ignite": "IND",
            "Omaha Supernovas": "OMA",
            "Orlando Valkyries": "ORL",
            "San Diego Mojo": "SDM",
            "Vegas Thrill": "LVT"
        }

        # Extract game_id from file_url (if applicable)
        game_id = "unknown_game"

        if "-" in file_url:
            parts = file_url.split("/")[-1].split("-")
            if len(parts) > 2:
                game_id = parts[2].split(".")[0]

        # Helper function to process team data
        def process_team(team_data, opponent_team_name):
            rows = []
            team_name = team_data["name"]
            for player in team_data["matchStatsSheets"]:
                row = {
                    "statistic_id": f"{team_code_mapping.get(team_name, 'UNK')}-{player['number']}-{game_id}",
                    "player_id": f"{team_code_mapping.get(team_name, 'UNK')}-{player['number']}",
                    "game_id": game_id,
                    "player_team": team_code_mapping.get(team_name, "UNK"),
                    "opponent_team": team_code_mapping.get(opponent_team_name, "UNK"),
                    "srv_sum": player["data"].get("serveTotal", 0),
                    "srv_ace": player["data"].get("serveWin", 0),
                    "srv_err": player["data"].get("serveErr", 0),
                    "rec_sum": player["data"].get("recTotal", 0),
                    "rec_pos": round((player["data"].get("recTotal", 0) * player["data"].get("recPosRatio", 0)), 0)
                                if player["data"].get("recPosRatio") is not None else 0,
                    "rec_prf": round((player["data"].get("recTotal", 0) * player["data"].get("recPerfRatio", 0)), 0)
                                if player["data"].get("recPerfRatio") is not None else 0,
                    "rec_err": player["data"].get("recErr", 0),
                    "atk_sum": player["data"].get("spikeTotal", 0),
                    "atk_kll": player["data"].get("spikeWin", 0),
                    "atk_err": player["data"].get("spikeErr", 0),
                    "atk_blk": player["data"].get("spikeHP", 0),
                    "blk_sum": player["data"].get("blockWin", 0),
                    "dig_sum": player["data"].get("successfulDigs", 0),
                    "ast_sum": player["data"].get("assists", 0),
                    "sets_played": int(player["playedSets"])
                }
                rows.append(row)
            return rows

        # Process home and away teams
        all_rows = []
        all_rows.extend(process_team(data["home"], data["away"]["name"]))
        all_rows.extend(process_team(data["away"], data["home"]["name"]))

        return {"game_id": game_id, "stats": all_rows[:10]}  # First 10 records for preview

    except Exception as e:
        return {"error": str(e)}

@app.route('/process-stats', methods=['POST'])
def process_stats():
    """
    API Endpoint to receive a file URL and process stats.
    """
    data = request.get_json()
    file_url = data.get('file_url')

    if not file_url:
        return jsonify({"error": "Missing file_url parameter"}), 400

    result = process_stats_from_url(file_url)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)
