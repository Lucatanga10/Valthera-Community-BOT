from flask import Flask, request, render_template_string
import requests, os, asyncio, threading
import discord
from discord.ext import commands
from discord.ui import Button, View

CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))
VERIFIED_ROLE_ID = int(os.getenv("VERIFIED_ROLE_ID"))
UNVERIFIED_ROLE_ID = int(os.getenv("UNVERIFIED_ROLE_ID"))

app = Flask(__name__)
HTML_SUCCESS = open("index.html", encoding="utf-8").read()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def get_oauth_url():
    return (
        f"https://discord.com/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=identify"
    )

class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="✅  Verify / Verifica", style=discord.ButtonStyle.link, url=get_oauth_url()))

@bot.event
async def on_ready():
    print(f"✅ Bot online: {bot.user}")
    bot.add_view(VerifyView())

@bot.event
async def on_member_join(member):
    role = member.guild.get_role(UNVERIFIED_ROLE_ID)
    if role:
        await member.add_roles(role)

@bot.command(name="setup_verify")
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    embed = discord.Embed(color=0x5865F2)
    embed.add_field(name="🇬🇧  Server Verification", value="Click the button below to verify and gain access to the server.\nYou will be redirected to Discord to authorize your account.", inline=False)
    embed.add_field(name="\u200b", value="\u200b", inline=False)
    embed.set_footer(text="Powered by VerifyBot")
    await ctx.send(embed=embed, view=VerifyView())
    try:
        await ctx.message.delete()
    except:
        pass

async def grant_verified_role(user_id: int):
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return False
    try:
        member = guild.get_member(user_id) or await guild.fetch_member(user_id)
    except discord.NotFound:
        return False
    verified = guild.get_role(VERIFIED_ROLE_ID)
    unverified = guild.get_role(UNVERIFIED_ROLE_ID)
    if verified:
        await member.add_roles(verified)
    if unverified and unverified in member.roles:
        await member.remove_roles(unverified)
    return True

@app.route("/")
def index():
    return "VerifyBot is running! ✅"

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "❌ No code provided", 400
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }
    r = requests.post("https://discord.com/api/oauth2/token", data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    token_data = r.json()
    access_token = token_data.get("access_token")
    if not access_token:
        return render_template_string(HTML_SUCCESS, username="Unknown", success=False)
    user = requests.get("https://discord.com/api/users/@me", headers={"Authorization": f"Bearer {access_token}"}).json()
    user_id = int(user["id"])
    username = user.get("username", "Unknown")
    future = asyncio.run_coroutine_threadsafe(grant_verified_role(user_id), bot.loop)
    try:
        success = future.result(timeout=10)
    except:
        success = False
    return render_template_string(HTML_SUCCESS, username=username, success=success)

def run_bot():
    bot.run(TOKEN)

if __name__ == "__main__":
    t = threading.Thread(target=run_bot, daemon=True)
    t.start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
