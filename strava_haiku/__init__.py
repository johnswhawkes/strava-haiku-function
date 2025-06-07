import os
import requests
import datetime
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

def main(timer):
    print("Running Strava Haiku Function...")

    # Refresh Strava token
    refresh_resp = requests.post("https://www.strava.com/api/v3/oauth/token", data={
        "client_id": os.environ["STRAVA_CLIENT_ID"],
        "client_secret": os.environ["STRAVA_CLIENT_SECRET"],
        "grant_type": "refresh_token",
        "refresh_token": os.environ["STRAVA_REFRESH_TOKEN"]
    }).json()
    access_token = refresh_resp["access_token"]
    print("Token refreshed")

    # Get activities
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

        # Astrology tone
        birthdate = datetime.datetime.fromisoformat(act["start_date_local"].replace("Z", "+00:00"))
        month, day = birthdate.month, birthdate.day
        sign = zodiac_sign(month, day)

        prompt = (
            f"Write a surreal, poetic haiku about a {distance_km}km {activity_type} in {location} "
            f"on {date} at {time}. Use rich atmospheric imagery and tone it for the mood of {sign}. "
            "Stick to 5-7-5 syllables. Don’t reference astrology directly."
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
        update_url = f"https://www.strava.com/api/v3/activities/{activity_id}"
        update_resp = requests.put(update_url, headers=headers, json={"description": haiku})

        if update_resp.status_code == 200:
            print(f"Updated activity {activity_id} successfully.")
        else:
            print(f"Failed to update activity {activity_id}:", update_resp.text)

def zodiac_sign(month, day):
    signs = [
        (1, 20, "Capricorn"), (2, 19, "Aquarius"), (3, 20, "Pisces"),
        (4, 20, "Aries"), (5, 21, "Taurus"), (6, 21, "Gemini"),
        (7, 23, "Cancer"), (8, 23, "Leo"), (9, 23, "Virgo"),
        (10, 23, "Libra"), (11, 22, "Scorpio"), (12, 22, "Sagittarius")
    ]
    for m, d, sign in reversed(signs):
        if (month, day) >= (m, d):
            return sign
    return "Capricorn"

if __name__ == "__main__":
    class DummyTimer:
        pass

    main(DummyTimer())
