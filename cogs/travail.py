import discord
from discord.ext import commands
import time
import random
from database import load_db, save_db, get_user

TRAVAIL_COOLDOWN = 3600  # 1h

METIERS = {
    "sans_emploi":   {"nom": "Sans emploi",    "emoji": "😴", "min": 100,  "max": 250,  "xp": 5,  "requis": 0},
    "livreur":       {"nom": "Livreur",         "emoji": "🛵", "min": 200,  "max": 400,  "xp": 10, "requis": 1},
    "serveur":       {"nom": "Serveur",         "emoji": "🍽️", "min": 250,  "max": 450,  "xp": 12, "requis": 2},
    "commercant":    {"nom": "Commerçant",      "emoji": "🏪", "min": 350,  "max": 600,  "xp": 15, "requis": 5},
    "informaticien": {"nom": "Informaticien",   "emoji": "💻", "min": 500,  "max": 900,  "xp": 20, "requis": 8},
    "medecin":       {"nom": "Médecin",         "emoji": "👨‍⚕️", "min": 800,  "max": 1400, "xp": 30, "requis": 12},
    "avocat":        {"nom": "Avocat",          "emoji": "⚖️", "min": 900,  "max": 1600, "xp": 35, "requis": 15},
    "pdg":           {"nom": "PDG",             "emoji": "👔", "min": 1500, "max": 3000, "xp": 50, "requis": 20},
}

PHRASES_TRAVAIL = {
    "livreur":       ["Tu as livré 15 colis sous la pluie !", "Tu as fait 50km à vélo !", "Tu as livré une pizza brûlante !"],
    "serveur":       ["Tu as servi 30 tables ce soir !", "Un client t'a laissé un gros pourboire !", "Tu as géré une heure de rush !"],
    "commercant":    ["Tu as vendu tout ton stock !", "Tu as négocié un super deal !", "Les clients ont adoré tes promos !"],
    "informaticien": ["Tu as corrigé 10 bugs critiques !", "Tu as développé une nouvelle fonctionnalité !", "Tu as sécurisé le serveur !"],
    "medecin":       ["Tu as sauvé 3 patients aujourd'hui !", "Tu as effectué une opération complexe !", "Tu as fait une longue garde !"],
    "avocat":        ["Tu as gagné un procès difficile !", "Tu as négocié un contrat juteux !", "Ton client a été acquitté !"],
    "pdg":           ["Ton entreprise a battu ses records !", "Tu as signé un contrat international !", "Ton action a monté en bourse !"],
    "sans_emploi":   ["Tu as ramassé des bouteilles !", "Tu as fait quelques petits boulots !", "Tu as aidé un voisin contre quelques pièces !"],
}

class Travail(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="travailler", aliases=["work", "boulot"])
    async def travailler(self, ctx):
        """Travailler pour gagner des coins"""
        db = load_db()
        user = get_user(db, ctx.author.id)
        now = time.time()

        diff = now - user["last_travail"]
        if diff < TRAVAIL_COOLDOWN:
            restant = TRAVAIL_COOLDOWN - diff
            m = int(restant // 60)
            s = int(restant % 60)
            await ctx.send(f"⏰ Tu es fatigué ! Reviens dans **{m}min {s}s**.")
            return

        metier_id = user.get("metier") or "sans_emploi"
        metier = METIERS.get(metier_id, METIERS["sans_emploi"])

        gain = random.randint(metier["min"], metier["max"])
        xp = metier["xp"]

        user["cash"] += gain
        user["xp"] += xp
        user["last_travail"] = now

        # Vérifier montée de niveau
        niveau_avant = user["niveau"]
        while user["xp"] >= user["niveau"] * 100:
            user["xp"] -= user["niveau"] * 100
            user["niveau"] += 1

        save_db(db)

        phrases = PHRASES_TRAVAIL.get(metier_id, PHRASES_TRAVAIL["sans_emploi"])
        phrase = random.choice(phrases)

        embed = discord.Embed(
            title=f"{metier['emoji']} Tu as travaillé !",
            description=f"*{phrase}*",
            color=0x2ECC71
        )
        embed.add_field(name="💰 Salaire", value=f"+**{gain:,}** 💵", inline=True)
        embed.add_field(name="⭐ XP", value=f"+**{xp}** XP", inline=True)
        embed.add_field(name="👛 Solde", value=f"**{user['cash']:,}** 💵", inline=True)

        if user["niveau"] > niveau_avant:
            embed.add_field(name="🎉 NIVEAU SUPÉRIEUR !", value=f"Tu es maintenant **niveau {user['niveau']}** !", inline=False)

        embed.set_footer(text=f"Métier : {metier['nom']} • Reviens dans 1h !")
        await ctx.send(embed=embed)

    @commands.command(name="metier", aliases=["job"])
    async def voir_metier(self, ctx):
        """Voir ton métier et les métiers disponibles"""
        db = load_db()
        user = get_user(db, ctx.author.id)
        save_db(db)

        metier_id = user.get("metier") or "sans_emploi"
        metier_actuel = METIERS.get(metier_id, METIERS["sans_emploi"])

        embed = discord.Embed(title="💼 Métiers disponibles", color=0x3498DB)
        embed.add_field(
            name="Ton métier actuel",
            value=f"{metier_actuel['emoji']} **{metier_actuel['nom']}** — {metier_actuel['min']:,} à {metier_actuel['max']:,} 💵/h",
            inline=False
        )

        desc = ""
        for mid, m in METIERS.items():
            if mid == "sans_emploi":
                continue
            statut = "✅" if user["niveau"] >= m["requis"] else f"🔒 Niv.{m['requis']}"
            current = " ← Actuel" if mid == metier_id else ""
            desc += f"{statut} {m['emoji']} **{m['nom']}** — {m['min']:,}~{m['max']:,} 💵/h{current}\n"

        embed.add_field(name="📋 Tous les métiers", value=desc, inline=False)
        embed.set_footer(text="$choisirmetier <nom> pour changer de métier")
        await ctx.send(embed=embed)

    @commands.command(name="choisirmetier", aliases=["setjob", "emploi"])
    async def choisir_metier(self, ctx, *, nom: str):
        """Choisir un métier"""
        db = load_db()
        user = get_user(db, ctx.author.id)

        # Trouver le métier
        metier_id = None
        for mid, m in METIERS.items():
            if nom.lower() in m["nom"].lower() or nom.lower() == mid:
                metier_id = mid
                break

        if not metier_id:
            noms = ", ".join(m["nom"] for mid, m in METIERS.items() if mid != "sans_emploi")
            await ctx.send(f"❌ Métier introuvable ! Choisis parmi : {noms}")
            return

        metier = METIERS[metier_id]
        if user["niveau"] < metier["requis"]:
            await ctx.send(f"❌ Tu dois être **niveau {metier['requis']}** pour ce métier ! Tu es niveau **{user['niveau']}**.")
            return

        user["metier"] = metier_id
        save_db(db)

        embed = discord.Embed(
            title=f"{metier['emoji']} Nouveau métier !",
            description=f"Tu es maintenant **{metier['nom']}** !",
            color=0x2ECC71
        )
        embed.add_field(name="💰 Salaire", value=f"{metier['min']:,} à {metier['max']:,} 💵/h", inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Travail(bot))
