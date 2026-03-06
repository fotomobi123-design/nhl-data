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

# Zoznam viacerých RSS zdrojov pre maximálnu istotu (ak jeden padne, ide sa na dalsi)
RSS_URLS = [
    "https://www.cbssports.com/rss/headlines/nhl/",
    "https://www.espn.com/espn/rss/nhl/news",
    "https://www.tsn.ca/rss/nhl.xml"
]

def fetch_all_rss_data():
    combined_data = ""
    for url in RSS_URLS:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                combined_data += response.read().decode('utf-8') + "\n\n"
        except Exception as e:
            print(f"Chyba pri {url}: {e}")
            continue
    return combined_data

def process_with_gemini(raw_xml):
    prompt = """
    Si expert na NHL. Analyzuj tento text z RSS zdrojov a nájdi v ňom VŠETKY hokejové výmeny (trejdy). 
    Ignoruj bežné správy a duplikáty. Spoj kluby do dvojičiek (ak niekto odišiel za draft, zisti odkiaľ).
    Prelož do slovenčiny.
    Vráť STRIKTNE čistý JSON v tomto formáte:
    [{"date": "YYYY-MM-DD", "team1": "Skratka1", "team2": "Skratka2", "player_team1_received": "Meno", "player_team2_received": "Meno", "description_sk": "Preklad"}]
    """
    try:
        response = model.generate_content([prompt, raw_xml])
        clean_text = response.text.strip()
        if clean_text.startswith("
http://googleusercontent.com/immersive_entry_chip/0
http://googleusercontent.com/immersive_entry_chip/1
