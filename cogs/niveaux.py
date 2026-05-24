import discord
from discord.ext import commands
from database import load_db, save_db, get_user

RECOMPENSES_NIVEAU = {
    5:  500,
    10: 1500,
    15: 3000,
    20: 5000,
    25: 8000,
    30: 12000,
    40: 20000,
    50: 50000,
}

def get_rang(niveau):
    if niveau >= 50: return "👑 Légende"
    if niveau >= 40: return "💎 Diamant"
    if niveau >= 30: return "🏆 Platine"
    if niveau >= 20: return "🥇 Or"
    if niveau >= 15: return "🥈 Argent"
    if niveau >= 10: return "🥉 Bronze"
    if niveau >= 5:  return "⭐ Apprenti"
    return "🌱 Débutant"

def xp_requis(niveau):
    return niveau * 100

class Niveaux(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @bot.event
    async def on_message(message):
        if message.author.bot:
            return

        db = load_db()
        user = get_user(db, message.author.id)

        import random
        xp_gain = random.randint(3, 8)
        user["xp"] += xp_gain

        niveau_avant = user["niveau"]
        xp_need = xp_requis(user["niveau"])

        while user["xp"] >= xp_need:
            user["xp"] -= xp_need
            user["niveau"] += 1
            xp_need = xp_requis(user["niveau"])

        if user["niveau"] > niveau_avant:
            recompense = RECOMPENSES_NIVEAU.get(user["niveau"], 0)
            user["cash"] += recompense
            save_db(db)

            rang = get_rang(user["niveau"])
            embed = discord.Embed(
                title="🎉 NIVEAU SUPÉRIEUR !",
                description=f"**{message.author.display_name}** est maintenant **niveau {user['niveau']}** !",
                color=0xFFD700
            )
            embed.add_field(name="🏅 Rang", value=rang, inline=True)
            if recompense > 0:
                embed.add_field(name="🎁 Récompense", value=f"+**{recompense:,}** 💵", inline=True)
            try:
                await message.channel.send(embed=embed)
            except:
                pass
        else:
            save_db(db)

    @commands.command(name="niveau", aliases=["level", "lvl", "rang"])
    async def niveau(self, ctx, membre: discord.Member = None):
        """Voir ton niveau et ton XP"""
        cible = membre or ctx.author
        db = load_db()
        user = get_user(db, cible.id)
        save_db(db)

        xp_actuel = user["xp"]
        xp_need = xp_requis(user["niveau"])
        progression = int((xp_actuel / xp_need) * 20)
        barre = "█" * progression + "░" * (20 - progression)
        rang = get_rang(user["niveau"])

        embed = discord.Embed(
            title=f"⭐ Niveau de {cible.display_name}",
            color=0xFFD700
        )
        embed.add_field(name="🏅 Rang", value=rang, inline=True)
        embed.add_field(name="📊 Niveau", value=f"**{user['niveau']}**", inline=True)
        embed.add_field(name="⭐ XP", value=f"**{xp_actuel}/{xp_need}**", inline=True)
        embed.add_field(name="Progression", value=f"`[{barre}]` {xp_actuel}/{xp_need} XP", inline=False)

        # Prochain niveau
        prochaine_recompense = None
        for niv, recompense in sorted(RECOMPENSES_NIVEAU.items()):
            if niv > user["niveau"]:
                prochaine_recompense = (niv, recompense)
                break

        if prochaine_recompense:
            embed.add_field(
                name="🎯 Prochain palier",
                value=f"Niveau **{prochaine_recompense[0]}** → **{prochaine_recompense[1]:,}** 💵",
                inline=False
            )

        embed.set_thumbnail(url=cible.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="classement", aliases=["leaderboard_xp", "top_niveau"])
    async def classement(self, ctx):
        """Voir le classement des niveaux"""
        db = load_db()
        if not db:
            await ctx.send("❌ Pas encore de données !")
            return

        joueurs = []
        for uid, data in db.items():
            joueurs.append((uid, data.get("niveau", 1), data.get("xp", 0)))

        joueurs.sort(key=lambda x: (x[1], x[2]), reverse=True)

        embed = discord.Embed(title="🏆 Classement — Niveaux", color=0xFFD700)
        medailles = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

        desc = ""
        for i, (uid, niveau, xp) in enumerate(joueurs[:10]):
            try:
                user = await self.bot.fetch_user(int(uid))
                nom = user.display_name
            except:
                nom = f"Joueur {uid[:4]}"
            rang = get_rang(niveau)
            desc += f"{medailles[i]} **{nom}** — Niveau **{niveau}** {rang}\n"

        embed.description = desc or "Aucun joueur."
        await ctx.send(embed=embed)

    @commands.command(name="xp")
    async def voir_xp(self, ctx):
        """Voir ton XP rapidement"""
        db = load_db()
        user = get_user(db, ctx.author.id)
        save_db(db)
        await ctx.send(f"⭐ Tu as **{user['xp']} XP** et tu es **niveau {user['niveau']}** ({get_rang(user['niveau'])}).")

    @commands.command(name="paliers")
    async def paliers(self, ctx):
        """Voir les récompenses par niveau"""
        embed = discord.Embed(title="🎁 Récompenses par niveau", color=0xFFD700)
        desc = ""
        for niveau, recompense in sorted(RECOMPENSES_NIVEAU.items()):
            rang = get_rang(niveau)
            desc += f"**Niveau {niveau}** {rang} → **{recompense:,}** 💵\n"
        embed.description = desc
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Niveaux(bot))
