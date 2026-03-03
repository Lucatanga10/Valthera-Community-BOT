from flask import Flask, request, render_template_string
import requests, os, asyncio
import bot as discord_bot

CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")

app = Flask(__name__)
HTML_SUCCESS = open("verify.html", encoding="utf-8").read()

app = Flask(__name__)

# Import bot for role granting
import bot as discord_bot

# ✅ Dopo
HTML_SUCCESS = open("verify.html", encoding="utf-8").read()

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "❌ No code provided", 400

    # Exchange code for token
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post("https://discord.com/api/oauth2/token", data=data, headers=headers)
    token_data = r.json()
    access_token = token_data.get("access_token")

    if not access_token:
        return "❌ Failed to get token", 400

    # Get user info
    user_r = requests.get(
        "https://discord.com/api/users/@me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    user = user_r.json()
    user_id = int(user["id"])
    username = user.get("username", "Unknown")

    # Grant role via bot
    loop = discord_bot.bot.loop
    future = asyncio.run_coroutine_threadsafe(
        discord_bot.grant_verified_role(user_id), loop
    )
    success = future.result(timeout=10)

    return render_template_string(HTML_SUCCESS, username=username, success=success)


if __name__ == "__main__":
    app.run(port=5000)
