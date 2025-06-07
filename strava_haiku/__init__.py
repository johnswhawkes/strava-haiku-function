<<<<<<< HEAD
import os
import json
import datetime
import http.client
import urllib.parse
from openai import AzureOpenAI
=======
import datetime
import os
import requests
import openai
>>>>>>> 8cd385d (Initial commit)
from dotenv import load_dotenv

load_dotenv()

def main(timer):
    print("Running Strava Haiku Function...")

<<<<<<< HEAD
    # Refresh Strava token
    data = urllib.parse.urlencode({
        "client_id": os.environ["STRAVA_CLIENT_ID"],
        "client_secret": os.environ["STRAVA_CLIENT_SECRET"],
        "grant_type": "refresh_token",
        "refresh_token": os.environ["STRAVA_REFRESH_TOKEN"]
    })
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    conn = http.client.HTTPSConnection("www.strava.com")
    conn.request("POST", "/api/v3/oauth/token", data, headers)
    response = conn.getresponse()
    refresh_resp = json.loads(response.read())
    access_token = refresh_resp["access_token"]
    conn.close()
    print("Token refreshed")

    # Get recent activities
    headers = {"Authorization": f"Bearer {access_token}"}
    conn = http.client.HTTPSConnection("www.strava.com")
    conn.request("GET", "/api/v3/athlete/activities", headers=headers)
    response = conn.getresponse()
    activities = json.loads(response.read())
    conn.close()
=======
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
>>>>>>> 8cd385d (Initial commit)

    if not activities:
        print("No activities found.")
        return

<<<<<<< HEAD
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

=======
    latest = activities[0]
    if latest.get("description"):
        print("Activity already has description. Skipping.")
        return

    # Step 3: Prepare prompt
    distance_km = round(latest["distance"] / 1000, 1)
    date = latest["start_date_local"].split("T")[0]
    time = latest["start_date_local"].split("T")[1][:5]
    location = latest.get("location_city", "an unknown place")
    activity_type = latest["type"].lower()

    prompt = (
        f"Write a haiku about a {distance_km}km {activity_type} in {location} on {date} at {time}. "
        "Use natural or atmospheric imagery. Make it poetic, not modern or jokey. Stick to 5-7-5 syllable form."
    )

    # Step 4: Call Azure OpenAI
    openai.api_key = os.environ["AZURE_OPENAI_KEY"]
    openai.api_base = os.environ["AZURE_OPENAI_ENDPOINT"]
    openai.api_type = "azure"
    openai.api_version = "2023-05-15"  # Use the latest supported version

    response = openai.ChatCompletion.create(
        engine=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=100
    )

    haiku = response["choices"][0]["message"]["content"].strip()
    print("Generated haiku:\n", haiku)

    # Step 5: Update Strava description
    activity_id = latest["id"]
    update_url = f"https://www.strava.com/api/v3/activities/{activity_id}"
    update_resp = requests.put(update_url, headers=headers, json={"description": haiku})

    if update_resp.status_code == 200:
        print("Activity updated successfully.")
    else:
        print("Failed to update activity:", update_resp.text)
>>>>>>> 8cd385d (Initial commit)
if __name__ == "__main__":
    class DummyTimer:
        pass

    main(DummyTimer())