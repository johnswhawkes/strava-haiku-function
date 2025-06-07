import os
import json
import datetime
import http.client
import urllib.parse
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

def main(timer):
    print("Running Strava Haiku Function...")

    # Step 1: Refresh token if needed
    refresh_token = os.environ["STRAVA_REFRESH_TOKEN"]
    client_id = os.environ["STRAVA_CLIENT_ID"]
    client_secret = os.environ["STRAVA_CLIENT_SECRET"]

    refresh_resp = requests.post("https://www.strava.com/api/v3/oauth/token", data={
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }).json()

    access_token = refresh_resp["access_token"]
    print("Token refreshed")

    # Step 2: Get latest activity
    headers = {"Authorization": f"Bearer {access_token}"}
    activities = requests.get("https://www.strava.com/api/v3/athlete/activities", headers=headers).json()

    if not activities:
        print("No activities found.")
        return

    for act in activities:
        if act.get("description"):
            continue

        activity_id = act["id"]
        distance_km = round(act["distance"] / 1000, 1)
        date = act["start_date_local"].split("T")[0]
        time = act["start_date_local"].split("T")[1][:5]
        location = act.get("location_city", "an unknown place")
        activity_type = act["type"].lower()

        # Zodiac tone
        birthdate = datetime.datetime.fromisoformat(act["start_date_local"].replace("Z", "+00:00"))
        tone_description = zodiac_influence(birthdate.month, birthdate.day)

        prompt = (
            f"Write a surreal, poetic haiku about a {distance_km}km {activity_type} in {location} "
            f"on {date} at {time}. Include time of day and seasonal atmosphere. "
            f"Use rich imagery. Let the tone be {tone_description}. "
            "Stick strictly to 5-7-5 syllables. Never mention zodiac signs or horoscopes."
        )

        # Generate haiku
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
        print(f"\nGenerated haiku for activity {activity_id}:\n{haiku}\n")

        # Update activity
        update_body = json.dumps({"description": haiku})
        update_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        conn = http.client.HTTPSConnection("www.strava.com")
        conn.request("PUT", f"/api/v3/activities/{activity_id}", update_body, update_headers)
        update_resp = conn.getresponse()

        if update_resp.status == 200:
            print(f"Updated activity {activity_id} successfully.")
        else:
            print(f"Failed to update activity {activity_id}:", update_resp.read().decode())
        conn.close()

def zodiac_influence(month, day):
    tones = [
        (1, 20, "a stoic, time-worn tone — patient and enduring"),
        (2, 19, "a cool, distant tone — eccentric and windswept"),
        (3, 20, "a dreamy, dissolving tone — drifting and melancholic"),
        (4, 20, "a bold, impulsive tone — reckless and burning"),
        (5, 21, "a calm, grounded tone — earthy and sensual"),
        (6, 21, "a lively, flickering tone — curious and quick"),
        (7, 23, "a nostalgic, lunar tone — gentle and emotionally vivid"),
        (8, 23, "a radiant, regal tone — proud and sunlit"),
        (9, 23, "a clean, precise tone — observant and restrained"),
        (10, 23, "a cool, balanced tone — reflective and measured"),
        (11, 22, "an intense, secretive tone — dark and magnetic"),
        (12, 22, "an expansive, searching tone — mythic and restless"),
    ]
    for m, d, tone in reversed(tones):
        if (month, day) >= (m, d):
            return tone
    return "a stoic, time-worn tone — patient and enduring"

if __name__ == "__main__":
    class DummyTimer:
        pass

    main(DummyTimer())