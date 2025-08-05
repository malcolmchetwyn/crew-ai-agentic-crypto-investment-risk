import os
import sys
import warnings
from dotenv import load_dotenv
import requests
import csv
import re

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.crew import HierarchicalAnalysisCrew

# Load environment variables from .env file
load_dotenv()

# Configuration
COINGECKO_API = (
    "https://api.coingecko.com/api/v3/coins/markets"
    "?vs_currency=usd"
    "&order=market_cap_desc"
    "&per_page=5"
    "&page=1"
)
CONSIDER_THRESHOLD = 60
EXEC_SUMMARY_FILE = "exec_summaries.txt"
SCORES_CSV_FILE = "coin_scores.csv"


def fetch_top_coins():
    """
    Fetch the top coins by market cap from CoinGecko.
    """
    resp = requests.get(COINGECKO_API)
    resp.raise_for_status()
    return resp.json()

def append_exec_summary(label, summary):
    """
    Append the executive summary for a coin to the summaries file.
    """
    with open(EXEC_SUMMARY_FILE, "a", encoding="utf-8") as f:
        f.write(f"=== {label} ===\n")
        f.write(summary.strip() + "\n\n")

def append_score_row(label, score):
    """
    Append a single row to the CSV of coin scores.
    """
    file_exists = os.path.isfile(SCORES_CSV_FILE)
    with open(SCORES_CSV_FILE, "a", newline='', encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(["symbol - name", "score"])
        writer.writerow([label, score])


def parse_crew_output(text):
    """
    Parses the raw text output from the crew to extract the score and summary.
    This version is more robust and handles missing markdown asterisks.
    """
    # Regex pattern now treats asterisks as optional
    score_match = re.search(r"\**Total Quantitative Score:\**\s*(\d+\.?\d*)/100", text)
    score = float(score_match.group(1)) if score_match else None

    # Regex for the executive summary remains the same
    summary_match = re.search(r"## Executive Summary\s*([\s\S]*?)\s*## Final Score & Recommendation", text)
    summary = summary_match.group(1).strip() if summary_match else ""
    
    # Fallback for kill-switch cases (score of 0)
    if score is None:
        if "Quantitative Score:** 0" in text or "quantitative score of 0" in text:
            score = 0.0

    return {"score": score, "exec_summary": summary}

def run():
    """
    Main execution function.
    """
    print("--- Checking Environment Variables ---")
    serper_api_key = os.getenv("SERPER_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    print(f"SERPER_API_KEY: {'✅' if serper_api_key else '❌'}")
    print(f"OPENAI_API_KEY: {'✅' if openai_api_key else '❌'}")
    print("--------------------------------------\n")

    print("## Fetching top coins from CoinGecko... ##")
    top_coins = fetch_top_coins()
    print(f"Retrieved {len(top_coins)} coins.\n")


    #print("## Using hard-coded coin for testing: Solana ##\n")
    top_coins = [
        {'id': 'stellar', 'symbol': 'xlm', 'name': 'Stellar'},
        {'id': 'hedera-hashgraph', 'symbol': 'hbar', 'name': 'Hedera'},
        {'id': 'xdce-crowd-sale', 'symbol': 'xdc', 'name': 'XDC Network'},
        {'id': 'algorand', 'symbol': 'algo', 'name': 'Algorand'}
    ]

    for coin in top_coins:
        coin_id = coin.get("id", "")
        symbol = coin.get("symbol", "").upper()
        name = coin.get("name", "")
        label = f"{symbol} - {name}"

        if coin_id.lower() in ("bitcoin", "ethereum"):
            continue

        print(f"Analyzing {label}...")

        crew = HierarchicalAnalysisCrew(label)
        crew_result = crew.run()

        # --- THIS IS THE FIX ---
        # Convert the CrewOutput object to a string before parsing
        raw_output = str(crew_result)
        # --- END OF FIX ---

        parsed_result = parse_crew_output(raw_output)
        score = parsed_result.get("score")
        exec_summary = parsed_result.get("exec_summary")

        if score is not None:
            append_score_row(label, score)

            if score >= CONSIDER_THRESHOLD:
                summary_to_write = exec_summary if exec_summary else raw_output
                append_exec_summary(label, summary_to_write)
        else:
            print(f"Warning: Could not parse a numeric score for {label}. Skipping file writes.")

    print("\n✅ Analysis complete. Results written to files.")

if __name__ == "__main__":
    run()

