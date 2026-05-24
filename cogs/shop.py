import discord
from discord.ext import commands
from database import load_db, save_db, get_user

ITEMS = {
    "cafe":         {"nom": "Café ☕",          "prix": 50,    "desc": "Réduit le cooldown de travail de 10min",  "emoji": "☕"},
    "pizza":        {"nom": "Pizza 🍕",          "prix": 150,   "desc": "Restaure de l'énergie, +20 XP",           "emoji": "🍕"},
    "ordinateur":   {"nom": "Ordinateur 💻",     "prix": 2000,  "desc": "+10% de salaire pendant 24h",             "emoji": "💻"},
    "voiture":      {"nom": "Voiture 🚗",        "prix": 5000,  "desc": "+20% de salaire pendant 24h",             "emoji": "🚗"},
    "manteau":      {"nom": "Manteau 🧥",        "prix": 800,   "desc": "Réduit l'amende de crime de 20%",         "emoji": "🧥"},
    "pistolet":     {"nom": "Pistolet 🔫",       "prix": 3000,  "desc": "+15% de chances de réussite au crime",    "emoji": "🔫"},
    "coffre":       {"nom": "Coffre-fort 🔒",    "prix": 10000, "desc": "Protège 30% de ton cash contre les vols", "emoji": "🔒"},
    "crypto":       {"nom": "Crypto 🪙",         "prix": 500,   "desc": "Investissement risqué, x2 ou x0",         "emoji": "🪙"},
    "energie":      {"nom": "Boisson énergisante ⚡", "prix": 200, "desc": "+50 XP instantanément",               "emoji": "⚡"},
    "bouclier":     {"nom": "Bouclier 🛡️",       "prix": 4000,  "desc": "Immunité contre le vol pendant 6h",       "emoji": "🛡️"},
}

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="shop", aliases=["magasin", "boutique"])
    async def shop(self, ctx):
        """Voir le shop"""
        embed = discord.Embed(title="🛒 Boutique", description="Achète des objets avec `$acheter <nom>`", color=0xE74C3C)

        for item_id, item in ITEMS.items():
            embed.add_field(
                name=f"{item['emoji']} {item['nom']} — {item['prix']:,} 💵",
                value=f"*{item['desc']}*",
                inline=False
            )

        embed.set_footer(text="$inventaire pour voir tes objets • $utiliser <nom> pour utiliser")
        await ctx.send(embed=embed)

    @commands.command(name="acheter", aliases=["buy", "achat"])
    async def acheter(self, ctx, *, nom: str):
        """Acheter un objet du shop"""
        db = load_db()
        user = get_user(db, ctx.author.id)

        item_id = None
        for iid, item in ITEMS.items():
            if nom.lower() in item["nom"].lower() or nom.lower() == iid:
                item_id = iid
                break

        if not item_id:
            noms = ", ".join(ITEMS.keys())
            await ctx.send(f"❌ Objet introuvable ! Choisis parmi : {noms}")
            return

        item = ITEMS[item_id]

        if user["cash"] < item["prix"]:
            await ctx.send(f"❌ Tu n'as pas assez de cash ! Il te faut **{item['prix']:,}** 💵 (tu as **{user['cash']:,}** 💵).")
            return

        user["cash"] -= item["prix"]
        if "inventaire" not in user:
            user["inventaire"] = []
        user["inventaire"].append(item_id)
        save_db(db)

        embed = discord.Embed(title="✅ Achat effectué !", color=0x00FF00)
        embed.add_field(name=f"{item['emoji']} {item['nom']}", value=f"Payé : **{item['prix']:,}** 💵", inline=False)
        embed.add_field(name="👛 Cash restant", value=f"**{user['cash']:,}** 💵", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="inventaire", aliases=["inv", "sac"])
    async def inventaire(self, ctx, membre: discord.Member = None):
        """Voir ton inventaire"""
        cible = membre or ctx.author
        db = load_db()
        user = get_user(db, cible.id)
        save_db(db)

        inv = user.get("inventaire", [])

        embed = discord.Embed(title=f"🎒 Inventaire de {cible.display_name}", color=0x9B59B6)

        if not inv:
            embed.description = "Ton inventaire est vide ! Va au `$shop` !"
        else:
            from collections import Counter
            compte = Counter(inv)
            desc = ""
            for item_id, qte in compte.items():
                item = ITEMS.get(item_id, {"nom": item_id, "emoji": "❓"})
                desc += f"{item['emoji']} **{item['nom']}** x{qte}\n"
            embed.description = desc

        embed.set_thumbnail(url=cible.display_avatar.url)
        embed.set_footer(text="$utiliser <nom> pour utiliser un objet")
        await ctx.send(embed=embed)

    @commands.command(name="utiliser", aliases=["use"])
    async def utiliser(self, ctx, *, nom: str):
        """Utiliser un objet de ton inventaire"""
        import time
        db = load_db()
        user = get_user(db, ctx.author.id)

        inv = user.get("inventaire", [])

        item_id = None
        for iid in ITEMS:
            if nom.lower() in ITEMS[iid]["nom"].lower() or nom.lower() == iid:
                item_id = iid
                break

        if not item_id or item_id not in inv:
            await ctx.send(f"❌ Tu n'as pas cet objet dans ton inventaire !")
            return

        item = ITEMS[item_id]
        inv.remove(item_id)
        user["inventaire"] = inv

        resultat = ""

        if item_id == "cafe":
            user["last_travail"] = max(0, user["last_travail"] - 600)
            resultat = "☕ Ton cooldown de travail a été réduit de 10 minutes !"
        elif item_id == "pizza":
            user["xp"] += 20
            resultat = "🍕 Tu as récupéré de l'énergie ! +20 XP"
        elif item_id == "energie":
            user["xp"] += 50
            resultat = "⚡ Boost d'énergie ! +50 XP"
        elif item_id == "crypto":
            import random
            if random.random() > 0.5:
                gain = 1000
                user["cash"] += gain
                resultat = f"🪙 Ta crypto a explosé ! +**{gain:,}** 💵 !"
            else:
                resultat = "🪙 Ta crypto s'est effondrée... Tu as tout perdu !"
        elif item_id == "bouclier":
            user["bouclier_until"] = time.time() + 21600
            resultat = "🛡️ Tu es protégé contre les vols pendant 6 heures !"
        elif item_id == "ordinateur":
            user["bonus_salaire_until"] = time.time() + 86400
            user["bonus_salaire"] = 0.10
            resultat = "💻 +10% de salaire pendant 24h !"
        elif item_id == "voiture":
            user["bonus_salaire_until"] = time.time() + 86400
            user["bonus_salaire"] = 0.20
            resultat = "🚗 +20% de salaire pendant 24h !"
        elif item_id == "manteau":
            user["manteau_until"] = time.time() + 86400
            resultat = "🧥 -20% d'amende sur les crimes pendant 24h !"
        elif item_id == "pistolet":
            user["pistolet_until"] = time.time() + 86400
            resultat = "🔫 +15% de chances de réussite au crime pendant 24h !"
        elif item_id == "coffre":
            user["coffre"] = True
            resultat = "🔒 Ton coffre-fort protège maintenant 30% de ton cash !"
        else:
            resultat = "✅ Objet utilisé !"

        save_db(db)

        embed = discord.Embed(title=f"{item['emoji']} Objet utilisé !", color=0x00FF00)
        embed.add_field(name="Effet", value=resultat, inline=False)
        await ctx.send(embed=embed)

    @acheter.error
    async def acheter_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Utilisation : `$acheter <nom de l'objet>`")

async def setup(bot):
    await bot.add_cog(Shop(bot))
