import os
import json
import requests
import datetime
import random
import urllib.parse
from openai import AzureOpenAI
from dotenv import load_dotenv
from astral import LocationInfo
from astral.sun import sun
from syllapy import count as syllable_count
from dateutil import parser
import azure.functions as func

load_dotenv()

def get_time_label(dt):
    hour = dt.hour
    if hour < 6:
        return "pre-dawn"
    elif hour < 9:
        return "early morning"
    elif hour < 12:
        return "late morning"
    elif hour < 15:
        return "afternoon"
    elif hour < 18:
        return "late afternoon"
    elif hour < 21:
        return "evening"
    else:
        return "night"

def get_season(month):
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:
        return "autumn"

def get_time_since_last(current_time, previous_time):
    delta = current_time - previous_time
    hours = delta.total_seconds() / 3600
    if hours < 6:
        return "shortly after another activity"
    elif hours < 24:
        return "later the same day"
    else:
        return f"after {int(hours // 24)} day(s) of rest"

def build_prompt(context):
    return f"""
You are a poet crafting a haiku about a physical activity.

Activity Details:
- Type: {context['type']}
- Distance: {context['distance']} km
- Location: {context['location']}
- Date: {context['date']}
- Time: {context['time']}
- Day: {context['day']}
- Time of Day: {context['time_of_day']}
- Season: {context['season']}
- Terrain: {context['terrain']}
- Title: {context['title']}
- Heart Rate: {context['heart_rate']} bpm
- Time Since Last Activity: {context['time_since_last']}

Task:
Write a surreal, evocative haiku based on the above experience.
Use sensory imagery drawn from the environment and the act of movement.
Let your style be dreamlike and minimal.
Stick strictly to 5-7-5 syllables.
Avoid rhymes. Do not mention zodiac signs, horoscopes, or astrology.
"""

def main(timer: func.TimerRequest) -> None:
    print("Running Strava Haiku Function...")

    # Refresh token
    data = urllib.parse.urlencode({
        "client_id": os.environ["STRAVA_CLIENT_ID"],
        "client_secret": os.environ["STRAVA_CLIENT_SECRET"],
        "grant_type": "refresh_token",
        "refresh_token": os.environ["STRAVA_REFRESH_TOKEN"]
    })
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post("https://www.strava.com/api/v3/oauth/token", data=data, headers=headers)
    access_token = response.json()["access_token"]
    print("Token refreshed")

    # Get activities
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get("https://www.strava.com/api/v3/athlete/activities", headers=headers)
    activities = response.json()

    now = datetime.datetime.now(datetime.timezone.utc)
    cutoff = now - datetime.timedelta(hours=24)
    previous_time = None

    for act in activities:
        start_time = parser.isoparse(act["start_date"]).astimezone(datetime.timezone.utc)
        if act.get("description") or start_time < cutoff:
            continue

        location = act.get("location_city") or act.get("name", "an unknown place")
        terrain = "Let the AI infer the terrain from the location name and context."
        time_label = get_time_label(start_time)
        season = get_season(start_time.month)
        time_since_last = get_time_since_last(start_time, previous_time) if previous_time else "first activity in dataset"
        previous_time = start_time

        context = {
            "type": act["type"].lower(),
            "distance": round(act["distance"] / 1000, 1),
            "location": location,
            "date": start_time.date().isoformat(),
            "time": start_time.time().isoformat(timespec='minutes'),
            "day": start_time.strftime('%A'),
            "time_of_day": time_label,
            "season": season,
            "terrain": terrain,
            "title": act.get("name", "Untitled"),
            "heart_rate": act.get("average_heartrate", "unknown"),
            "time_since_last": time_since_last
        }

        prompt = build_prompt(context)

        client = AzureOpenAI(
            api_key=os.environ["AZURE_OPENAI_KEY"],
            api_version="2023-05-15",
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"]
        )

        response = client.chat.completions.create(
            model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=100
        )

        haiku = response.choices[0].message.content.strip()
        lines = haiku.splitlines()
        if len(lines) != 3:
            print(f"Invalid haiku structure for activity {act['id']}, skipping.")
            continue

        print(f"\nGenerated haiku for activity {act['id']}\n{haiku}\n")

        update_body = json.dumps({"description": haiku})
        update_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        update_url = f"https://www.strava.com/api/v3/activities/{act['id']}"
        update_resp = requests.put(update_url, headers=update_headers, data=update_body)

        if update_resp.status_code == 200:
            print(f"Updated activity {act['id']} successfully.")
        else:
            print(f"Failed to update activity {act['id']}: {update_resp.text}")
