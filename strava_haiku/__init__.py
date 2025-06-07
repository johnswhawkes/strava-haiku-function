import datetime
import os
import requests
import openai
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
if __name__ == "__main__":
    class DummyTimer:
        pass

    main(DummyTimer())