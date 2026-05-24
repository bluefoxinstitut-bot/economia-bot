import discord
from discord.ext import commands
import time
import random
from database import load_db, save_db, get_user

CRIME_COOLDOWN = 7200    # 2h
VOLER_COOLDOWN = 3600    # 1h
BRAQUER_COOLDOWN = 14400 # 4h

CRIMES = [
    {"nom": "Vente de contrebande",    "gain_min": 300,  "gain_max": 800,  "amende": 400,  "succes": 65},
    {"nom": "Pickpocket",              "gain_min": 100,  "gain_max": 400,  "amende": 200,  "succes": 70},
    {"nom": "Piratage informatique",   "gain_min": 500,  "gain_max": 1500, "amende": 800,  "succes": 50},
    {"nom": "Trafic de faux billets",  "gain_min": 400,  "gain_max": 1000, "amende": 600,  "succes": 55},
    {"nom": "Vol de voiture",          "gain_min": 600,  "gain_max": 1200, "amende": 700,  "succes": 60},
    {"nom": "Arnaque en ligne",        "gain_min": 200,  "gain_max": 700,  "amende": 300,  "succes": 75},
]

BRAQUAGES = [
    {"nom": "Épicerie du coin",     "gain_min": 500,  "gain_max": 1500,  "amende": 1000, "succes": 70},
    {"nom": "Bureau de change",     "gain_min": 1000, "gain_max": 3000,  "amende": 2000, "succes": 55},
    {"nom": "Bijouterie",           "gain_min": 2000, "gain_max": 5000,  "amende": 3500, "succes": 45},
    {"nom": "Casino",               "gain_min": 3000, "gain_max": 8000,  "amende": 5000, "succes": 35},
    {"nom": "Banque centrale",      "gain_min": 5000, "gain_max": 15000, "amende": 8000, "succes": 25},
]

class Crime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="crime", aliases=["delinquance"])
    async def crime(self, ctx):
        """Commettre un crime pour gagner de l'argent (risqué !)"""
        db = load_db()
        user = get_user(db, ctx.author.id)
        now = time.time()

        diff = now - user["last_crime"]
        if diff < CRIME_COOLDOWN:
            restant = CRIME_COOLDOWN - diff
            h = int(restant // 3600)
            m = int((restant % 3600) // 60)
            await ctx.send(f"⏰ La police te surveille encore ! Attends **{h}h {m}min**.")
            return

        crime = random.choice(CRIMES)
        user["last_crime"] = now

        if random.randint(1, 100) <= crime["succes"]:
            gain = random.randint(crime["gain_min"], crime["gain_max"])
            user["cash"] += gain
            user["xp"] += 15
            save_db(db)

            embed = discord.Embed(title="🦹 Crime réussi !", color=0x9B59B6)
            embed.add_field(name="🎯 Crime", value=crime["nom"], inline=False)
            embed.add_field(name="💰 Gain", value=f"+**{gain:,}** 💵", inline=True)
            embed.add_field(name="⭐ XP", value="+15 XP", inline=True)
            embed.set_footer(text="Tu t'en es sorti ! Prochaine fois dans 2h.")
        else:
            amende = crime["amende"]
            user["cash"] = max(0, user["cash"] - amende)
            save_db(db)

            embed = discord.Embed(title="🚔 Arrêté par la police !", color=0xFF0000)
            embed.add_field(name="🎯 Crime raté", value=crime["nom"], inline=False)
            embed.add_field(name="💸 Amende", value=f"-**{amende:,}** 💵", inline=True)
            embed.set_footer(text="La prochaine fois sois plus prudent...")

        await ctx.send(embed=embed)

    @commands.command(name="voler", aliases=["steal", "rob"])
    async def voler(self, ctx, cible: discord.Member):
        """Essayer de voler quelqu'un"""
        if cible == ctx.author:
            await ctx.send("❌ Tu ne peux pas te voler toi-même !")
            return
        if cible.bot:
            await ctx.send("❌ Tu ne peux pas voler un bot !")
            return

        db = load_db()
        voleur = get_user(db, ctx.author.id)
        victime = get_user(db, cible.id)
        now = time.time()

        diff = now - voleur["last_voler"]
        if diff < VOLER_COOLDOWN:
            restant = VOLER_COOLDOWN - diff
            m = int(restant // 60)
            await ctx.send(f"⏰ Tu dois attendre **{m}min** avant de voler à nouveau !")
            return

        if victime["cash"] < 100:
            await ctx.send(f"❌ **{cible.display_name}** n'a pas assez de cash à voler !")
            return

        voleur["last_voler"] = now
        succes = random.randint(1, 100)

        if succes <= 45:
            max_vol = min(victime["cash"] // 3, 2000)
            gain = random.randint(50, max(51, max_vol))
            victime["cash"] -= gain
            voleur["cash"] += gain
            voleur["xp"] += 10
            save_db(db)

            embed = discord.Embed(title="🦹 Vol réussi !", color=0x9B59B6)
            embed.add_field(name="🎯 Victime", value=cible.display_name, inline=True)
            embed.add_field(name="💰 Volé", value=f"**{gain:,}** 💵", inline=True)
        else:
            amende = random.randint(100, 500)
            voleur["cash"] = max(0, voleur["cash"] - amende)
            save_db(db)

            embed = discord.Embed(title="🚔 Vol raté !", color=0xFF0000)
            embed.add_field(name="😤 Tu t'es fait attraper !", value=f"Amende : **{amende:,}** 💵", inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="braquer", aliases=["heist", "hold"])
    async def braquer(self, ctx):
        """Braquer un établissement (très risqué, très rentable !)"""
        db = load_db()
        user = get_user(db, ctx.author.id)
        now = time.time()

        diff = now - user["last_braquer"]
        if diff < BRAQUER_COOLDOWN:
            restant = BRAQUER_COOLDOWN - diff
            h = int(restant // 3600)
            m = int((restant % 3600) // 60)
            await ctx.send(f"⏰ Tu prépares encore ton prochain braquage... Attends **{h}h {m}min**.")
            return

        cible = random.choice(BRAQUAGES)
        user["last_braquer"] = now

        if random.randint(1, 100) <= cible["succes"]:
            gain = random.randint(cible["gain_min"], cible["gain_max"])
            user["cash"] += gain
            user["xp"] += 50
            save_db(db)

            embed = discord.Embed(title="💥 BRAQUAGE RÉUSSI !", color=0xFF6B00)
            embed.add_field(name="🏦 Cible", value=cible["nom"], inline=False)
            embed.add_field(name="💰 Butin", value=f"+**{gain:,}** 💵", inline=True)
            embed.add_field(name="⭐ XP", value="+50 XP", inline=True)
            embed.set_footer(text="Incroyable, tu t'en es sorti ! Prochain dans 4h.")
        else:
            amende = cible["amende"]
            user["cash"] = max(0, user["cash"] - amende)
            save_db(db)

            embed = discord.Embed(title="🚨 BRAQUAGE RATÉ !", color=0xFF0000)
            embed.add_field(name="🏦 Cible", value=cible["nom"], inline=False)
            embed.add_field(name="💸 Amende", value=f"-**{amende:,}** 💵", inline=True)
            embed.set_footer(text="Le SWAT t'a eu... Prochaine tentative dans 4h.")

        await ctx.send(embed=embed)

    @voler.error
    async def voler_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Utilisation : `$voler @utilisateur`")

async def setup(bot):
    await bot.add_cog(Crime(bot))
