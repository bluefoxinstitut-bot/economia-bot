import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN_ECO")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.dm_messages = True

bot = commands.Bot(command_prefix="$", intents=intents)

async def load_extensions():
    await bot.load_extension("cogs.economie")
    await bot.load_extension("cogs.banque")
    await bot.load_extension("cogs.travail")
    await bot.load_extension("cogs.crime")
    await bot.load_extension("cogs.shop")
    await bot.load_extension("cogs.bourse")
    await bot.load_extension("cogs.niveaux")

@bot.event
async def on_ready():
    print(f"✅ {bot.user} est connecté !")
    await bot.change_presence(activity=discord.Game(name="$aide 💰"))

@bot.command(name="aide")
async def aide(ctx):
    embed = discord.Embed(
        title="💰 Bot Économie — Commandes",
        description="Préfixe : `$`",
        color=0xFFD700
    )
    embed.add_field(
        name="💵 Économie de base",
        value="`$solde` `$daily` `$pay @user <montant>` `$top`",
        inline=False
    )
    embed.add_field(
        name="🏦 Banque",
        value="`$banque` `$deposer <montant>` `$retirer <montant>` `$interets`",
        inline=False
    )
    embed.add_field(
        name="💼 Travail",
        value="`$travailler` `$metier` `$choisirmetier <nom>`",
        inline=False
    )
    embed.add_field(
        name="🦹 Crime",
        value="`$crime` `$voler @user` `$braquer`",
        inline=False
    )
    embed.add_field(
        name="🛒 Shop",
        value="`$shop` `$acheter <item>` `$inventaire` `$utiliser <item>`",
        inline=False
    )
    embed.add_field(
        name="📈 Bourse",
        value="`$bourse` `$investir <action> <montant>` `$vendre <action>` `$portfolio`",
        inline=False
    )
    embed.add_field(
        name="⭐ Niveaux",
        value="`$niveau` `$classement` `$xp`",
        inline=False
    )
    embed.set_footer(text="Bot Économie • Bonne chance ! 🍀")
    await ctx.send(embed=embed)

async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

import asyncio
asyncio.run(main())
