import discord
from discord.ext import commands
from discord.ui import Button, View
import os

TOKEN = os.getenv("DISCORD_TOKEN")
CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
GUILD_ID = int(os.getenv("GUILD_ID"))
VERIFIED_ROLE_ID = int(os.getenv("VERIFIED_ROLE_ID"))
UNVERIFIED_ROLE_ID = int(os.getenv("UNVERIFIED_ROLE_ID"))


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
        button = Button(
            label="✅  Verify / Verifica",
            style=discord.ButtonStyle.link,
            url=get_oauth_url(),
        )
        self.add_item(button)


@bot.event
async def on_ready():
    print(f"✅ Bot online: {bot.user}")
    bot.add_view(VerifyView())


@bot.event
async def on_member_join(member: discord.Member):
    unverified_role = member.guild.get_role(UNVERIFIED_ROLE_ID)
    if unverified_role:
        await member.add_roles(unverified_role)


@bot.command(name="setup_verify")
@commands.has_permissions(administrator=True)
async def setup_verify(ctx):
    embed = discord.Embed(color=0x5865F2)
    embed.add_field(
        name="🇬🇧  Server Verification",
        value="Click the button below to verify and gain access to the server.\nYou will be redirected to Discord to authorize your account.",
        inline=False,
    )
    embed.add_field(name="\u200b", value="\u200b", inline=False)
    embed.add_field(
        name="🇮🇹  Verifica del server",
        value="Clicca sul pulsante qui sotto per verificare e ottenere l'accesso al server.\nVerrai reindirizzato su Discord per autorizzare il tuo account.",
        inline=False,
    )
    embed.set_footer(text="Powered by VerifyBot")
    await ctx.send(embed=embed, view=VerifyView())
    await ctx.message.delete()


# Called by server.py after successful OAuth
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


if __name__ == "__main__":
    bot.run(TOKEN)
