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
    "https://www.cbssports.com/rss/headlines/nhl/",
    "https://www.espn.com/espn/rss/nhl/news",
    "https://www.tsn.ca/rss/nhl.xml"
]
DATA_FILE = "data.json"

def fetch_all_rss_data():
    combined_data = ""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
    for url in RSS_URLS:
        print(f"Stahujem z: {url}")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                combined_data += response.read().decode('utf-8') + "\n\n"
        except Exception as e:
            print(f" -> Chyba pri stahovani z {url}: {e}")
            continue
    return combined_data

def process_with_gemini(raw_xml):
    # UPRAVENÝ PROMPT: Žiadame už aj zranenia!
    prompt = (
        "Si expert na NHL. Analyzuj text a najdi VSETKY hokejove vymeny (trejdy) A ZAROVEN VSETKY zranenia hracov. "
        "Ignoruj bezne spravy, hladaj len fakty o zraneniach a prestupoch. "
        "Preloz vsetko do slovenciny. "
        "Vrat STRIKTNE cisty JSON s dvoma hlavnymi klucmi 'trades' a 'injuries' v tomto formate: "
        '{"trades": [{"date": "YYYY-MM-DD", "team1": "Skratka1", "team2": "Skratka2", '
        '"player_team1_received": "Meno", "player_team2_received": "Meno", "description_sk": "Preklad"}], '
        '"injuries": [{"date": "YYYY-MM-DD", "player": "Meno Hraca", "team": "Skratka Timu", "injury_type_sk": "Typ zranenia a predpokladany navrat"}]}'
    )
    try:
        response = model.generate_content([prompt, raw_xml])
        clean_text = response.text.strip()
       
        prefix = "`" * 3 + "json"
        suffix = "`" * 3
       
        if clean_text.startswith(prefix): clean_text = clean_text[7:]
        if clean_text.endswith(suffix): clean_text = clean_text[:-3]
           
        return json.loads(clean_text)
    except Exception as e:
        print(f"Chyba umelej inteligencie: {e}")
        return {"trades": [], "injuries": []}

def load_existing_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Teraz vraciam celý slovník s oboma kľúčmi
                return data
        except json.JSONDecodeError:
            return {"trades": [], "injuries": []}
    return {"trades": [], "injuries": []}

def is_new_season(existing_trades):
    today = datetime.now()
    if not existing_trades: return False
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
    print("Startujem NHL Scraper...")
    existing_data = load_existing_data()
   
    # Preistotu ak subor existuje, ale ma stary format bez injuries kluca
    existing_trades = existing_data.get("trades", [])
    existing_injuries = existing_data.get("injuries", [])
   
    if is_new_season(existing_trades):
        print("Nova sezona! Mazem staru historiu.")
        existing_trades = []
        existing_injuries = []

    raw_data = fetch_all_rss_data()
   
    if raw_data.strip():
        print("Data stiahnute, analyzujem...")
        new_data = process_with_gemini(raw_data)
       
        # Spracovanie novych trejdov
        new_trades = new_data.get("trades", [])
        existing_descriptions = [t.get("description_sk") for t in existing_trades]
        for trade in new_trades:
            if trade.get("description_sk") not in existing_descriptions:
                existing_trades.insert(0, trade)
               
        # Spracovanie novych zraneni
        new_injuries = new_data.get("injuries", [])
        existing_injury_desc = [i.get("injury_type_sk") for i in existing_injuries]
        for injury in new_injuries:
            # Nechceme ukladat to iste zranenie toho isteho hraca viackrat
            if injury.get("injury_type_sk") not in existing_injury_desc:
                 existing_injuries.insert(0, injury)
    else:
        print("Upozornenie: Nepodarilo sa stiahnut data.")

    final_output = {
        "last_updated": datetime.now().isoformat(),
        "trades": existing_trades,
        "injuries": existing_injuries
    }

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)
    print("HOTOVO! Data so zraneniami uspesne ulozene.")

if __name__ == "__main__":
    main()

