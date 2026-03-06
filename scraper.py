import os
import json
import urllib.request
from datetime import datetime
import google.generativeai as genai

# Nastavenie Gemini API
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("CHYBA: API kluc nenajdeny!")
    exit(1)

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

RSS_URLS = [
    "[https://www.cbssports.com/rss/headlines/nhl/](https://www.cbssports.com/rss/headlines/nhl/)",
    "[https://www.espn.com/espn/rss/nhl/news](https://www.espn.com/espn/rss/nhl/news)",
    "[https://www.tsn.ca/rss/nhl.xml](https://www.tsn.ca/rss/nhl.xml)"
]
DATA_FILE = "data.json"

def fetch_all_rss_data():
    combined_data = ""
    for url in RSS_URLS:
        print(f"Stahujem: {url}")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                combined_data += response.read().decode('utf-8') + "\n\n"
        except Exception as e:
            print(f"Chyba pri {url}: {e}")
            continue
    return combined_data

def process_with_gemini(raw_xml):
    # Text je spojeny normalne, aby to nerozbilo zobrazenie
    prompt = (
        "Si expert na NHL. Analyzuj text a najdi VSETKY hokejove vymeny (trejdy). "
        "Ignoruj duplikaty. Spoj kluby do dvojiciek. Preloz do slovenciny. "
        "Vrat STRIKTNE cisty JSON v tomto formate: "
        '[{"date": "YYYY-MM-DD", "team1": "Skratka1", "team2": "Skratka2", '
        '"player_team1_received": "Meno", "player_team2_received": "Meno", "description_sk": "Preklad"}]'
    )
    try:
        response = model.generate_content([prompt, raw_xml])
        clean_text = response.text.strip()
        
        # Osetrenie pre spravne citanie textu bez vizualneho rozbitia
        prefix = "`" * 3 + "json"
        suffix = "`" * 3
        
        if clean_text.startswith(prefix): 
            clean_text = clean_text[7:]
        if clean_text.endswith(suffix): 
            clean_text = clean_text[:-3]
            
        return json.loads(clean_text)
    except Exception:
        return []

def load_existing_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("trades", [])
        except json.JSONDecodeError:
            return []
    return []

def is_new_season(existing_trades):
    today = datetime.now()
    if not existing_trades:
        return False
        
    # =====================================================================
    # TU SA MAZU DATA PRE NOVU SEZONU! 
    # =====================================================================
    if today.month == 7 and today.day == 1 and today.hour == 0:
        last_trade_date_str = existing_trades[0].get("date", "2000-01-01")
        try:
            last_trade_date = datetime.strptime(last_trade_date_str, "%Y-%m-%d")
            if last_trade_date.month < 7 or last_trade_date.year < today.year:
                return True
        except ValueError:
            pass
            
    return False

def main():
    print("Start...")
    existing_trades = load_existing_data()
    
    if is_new_season(existing_trades):
        print("Je 1. jula po polnoci! Nova sezona zacina. Mazem stare data.")
        existing_trades = []

    raw_data = fetch_all_rss_data()
    if not raw_data.strip(): return
    
    new_trades = process_with_gemini(raw_data)
    
    existing_descriptions = [t.get("description_sk") for t in existing_trades]
    for trade in new_trades:
        if trade.get("description_sk") not in existing_descriptions:
            existing_trades.insert(0, trade)

    final_output = {
        "last_updated": datetime.now().isoformat(),
        "trades": existing_trades
    }

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
