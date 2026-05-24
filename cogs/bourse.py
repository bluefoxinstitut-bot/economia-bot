import discord
from discord.ext import commands
import random
import time
from database import load_db, save_db, get_user

ACTIONS = {
    "TECH":  {"nom": "TechCorp",     "emoji": "💻", "prix": 100,  "volatilite": 0.15},
    "FOOD":  {"nom": "FoodInc",      "emoji": "🍔", "prix": 50,   "volatilite": 0.08},
    "AUTO":  {"nom": "AutoDrive",    "emoji": "🚗", "prix": 200,  "volatilite": 0.20},
    "GOLD":  {"nom": "GoldMine",     "emoji": "🥇", "prix": 500,  "volatilite": 0.10},
    "CRYPTO":{"nom": "CryptoCoin",   "emoji": "🪙", "prix": 75,   "volatilite": 0.40},
    "BANK":  {"nom": "MegaBank",     "emoji": "🏦", "prix": 300,  "volatilite": 0.07},
    "GAME":  {"nom": "GameStudios",  "emoji": "🎮", "prix": 150,  "volatilite": 0.25},
    "MED":   {"nom": "PharmaCorp",   "emoji": "💊", "prix": 400,  "volatilite": 0.12},
}

# Prix actuels (simulés, changent à chaque session)
prix_actuels = {k: v["prix"] for k, v in ACTIONS.items()}

def fluctuer_prix():
    """Fait fluctuer les prix des actions"""
    for ticker in prix_actuels:
        vol = ACTIONS[ticker]["volatilite"]
        changement = random.uniform(-vol, vol)
        prix_actuels[ticker] = max(1, int(prix_actuels[ticker] * (1 + changement)))

class Bourse(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Fluctuer les prix au démarrage
        fluctuer_prix()

    @commands.command(name="bourse", aliases=["marche", "market"])
    async def bourse(self, ctx):
        """Voir le marché boursier"""
        fluctuer_prix()

        embed = discord.Embed(
            title="📈 Bourse — Marché en temps réel",
            description="Investis avec `$investir <ACTION> <montant>`",
            color=0x2ECC71
        )

        for ticker, action in ACTIONS.items():
            prix = prix_actuels[ticker]
            base = ACTIONS[ticker]["prix"]
            diff = prix - base
            tendance = "📈" if diff >= 0 else "📉"
            pct = (diff / base) * 100
            embed.add_field(
                name=f"{action['emoji']} {ticker} — {action['nom']}",
                value=f"**{prix:,}** 💵 {tendance} ({pct:+.1f}%)\nVolatilité : {'⚡' * int(action['volatilite']*10)}",
                inline=True
            )

        embed.set_footer(text="$investir <ACTION> <montant> • $vendre <ACTION> • $portfolio")
        await ctx.send(embed=embed)

    @commands.command(name="investir", aliases=["buy_action", "acheteraction"])
    async def investir(self, ctx, ticker: str, montant: int):
        """Investir dans une action"""
        ticker = ticker.upper()
        if ticker not in ACTIONS:
            tickers = ", ".join(ACTIONS.keys())
            await ctx.send(f"❌ Action introuvable ! Choisis parmi : {tickers}")
            return

        if montant <= 0:
            await ctx.send("❌ Le montant doit être positif !")
            return

        db = load_db()
        user = get_user(db, ctx.author.id)

        if user["cash"] < montant:
            await ctx.send(f"❌ Tu n'as que **{user['cash']:,}** 💵 en cash !")
            return

        prix = prix_actuels[ticker]
        nb_actions = montant // prix

        if nb_actions == 0:
            await ctx.send(f"❌ Le prix d'une action **{ticker}** est de **{prix:,}** 💵. Tu n'as pas assez !")
            return

        cout_total = nb_actions * prix
        user["cash"] -= cout_total

        if "actions" not in user:
            user["actions"] = {}
        if ticker not in user["actions"]:
            user["actions"][ticker] = {"quantite": 0, "prix_achat": prix}

        user["actions"][ticker]["quantite"] += nb_actions
        save_db(db)

        action = ACTIONS[ticker]
        embed = discord.Embed(title="📈 Investissement effectué !", color=0x2ECC71)
        embed.add_field(name=f"{action['emoji']} Action", value=f"**{ticker}** ({action['nom']})", inline=True)
        embed.add_field(name="📊 Quantité", value=f"**{nb_actions}** actions", inline=True)
        embed.add_field(name="💰 Prix unitaire", value=f"**{prix:,}** 💵", inline=True)
        embed.add_field(name="💸 Coût total", value=f"**{cout_total:,}** 💵", inline=True)
        embed.add_field(name="👛 Cash restant", value=f"**{user['cash']:,}** 💵", inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="vendre", aliases=["sell_action", "vendreaction"])
    async def vendre(self, ctx, ticker: str, quantite: int = None):
        """Vendre tes actions"""
        ticker = ticker.upper()
        if ticker not in ACTIONS:
            await ctx.send(f"❌ Action introuvable !")
            return

        db = load_db()
        user = get_user(db, ctx.author.id)

        if "actions" not in user or ticker not in user["actions"] or user["actions"][ticker]["quantite"] == 0:
            await ctx.send(f"❌ Tu n'as pas d'actions **{ticker}** !")
            return

        possede = user["actions"][ticker]["quantite"]
        if quantite is None:
            quantite = possede

        if quantite > possede:
            await ctx.send(f"❌ Tu n'as que **{possede}** actions **{ticker}** !")
            return

        prix_actuel = prix_actuels[ticker]
        prix_achat = user["actions"][ticker]["prix_achat"]
        gain_total = quantite * prix_actuel
        profit = (prix_actuel - prix_achat) * quantite

        user["cash"] += gain_total
        user["actions"][ticker]["quantite"] -= quantite
        if user["actions"][ticker]["quantite"] == 0:
            del user["actions"][ticker]

        save_db(db)

        action = ACTIONS[ticker]
        couleur = 0x00FF00 if profit >= 0 else 0xFF0000
        embed = discord.Embed(title="📉 Actions vendues !", color=couleur)
        embed.add_field(name=f"{action['emoji']} Action", value=f"**{ticker}**", inline=True)
        embed.add_field(name="📊 Quantité vendue", value=f"**{quantite}**", inline=True)
        embed.add_field(name="💰 Prix de vente", value=f"**{prix_actuel:,}** 💵", inline=True)
        embed.add_field(name="💵 Recette totale", value=f"**{gain_total:,}** 💵", inline=True)
        embed.add_field(
            name="📊 Profit/Perte",
            value=f"{'📈 +' if profit >= 0 else '📉 '}{profit:,} 💵",
            inline=True
        )
        await ctx.send(embed=embed)

    @commands.command(name="portfolio", aliases=["portefeuille", "mesactions"])
    async def portfolio(self, ctx):
        """Voir ton portefeuille d'actions"""
        db = load_db()
        user = get_user(db, ctx.author.id)
        save_db(db)

        actions = user.get("actions", {})

        embed = discord.Embed(title="📊 Ton Portfolio", color=0x3498DB)

        if not actions:
            embed.description = "Tu n'as aucune action ! Investi avec `$investir <ACTION> <montant>`"
        else:
            valeur_totale = 0
            desc = ""
            for ticker, data in actions.items():
                if data["quantite"] == 0:
                    continue
                action = ACTIONS.get(ticker, {"nom": ticker, "emoji": "📊"})
                prix_actuel = prix_actuels.get(ticker, data["prix_achat"])
                valeur = data["quantite"] * prix_actuel
                profit = (prix_actuel - data["prix_achat"]) * data["quantite"]
                valeur_totale += valeur
                tendance = "📈" if profit >= 0 else "📉"
                desc += f"{action['emoji']} **{ticker}** — {data['quantite']}x @ {prix_actuel:,}💵 = **{valeur:,}💵** {tendance} ({profit:+,}💵)\n"

            embed.description = desc
            embed.add_field(name="💼 Valeur totale", value=f"**{valeur_totale:,}** 💵", inline=False)

        await ctx.send(embed=embed)

    @investir.error
    async def investir_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Utilisation : `$investir <ACTION> <montant>` (ex: `$investir TECH 1000`)")

async def setup(bot):
    await bot.add_cog(Bourse(bot))
