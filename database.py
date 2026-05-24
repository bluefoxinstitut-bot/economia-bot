import json
import os

DB_FILE = "data.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return {}

def save_db(db):
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)

def get_user(db, user_id):
    uid = str(user_id)
    if uid not in db:
        db[uid] = {
            "cash": 500,
            "banque": 0,
            "xp": 0,
            "niveau": 1,
            "metier": None,
            "inventaire": [],
            "actions": {},
            "last_daily": 0,
            "last_travail": 0,
            "last_crime": 0,
            "last_braquer": 0,
            "last_voler": 0,
        }
    return db[uid]
