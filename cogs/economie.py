import discord
from discord.ext import commands
import time
from database import load_db, save_db, get_user

DAILY_MONTANT = 500
DAILY_COOLDOWN = 86400  # 24h

class Economie(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="solde", aliases=["bal", "argent", "wallet"])
    async def solde(self, ctx, membre: discord.Member = None):
        """Voir ton solde"""
        cible = membre or ctx.author
        db = load_db()
        user = get_user(db, cible.id)
        save_db(db)

        total = user["cash"] + user["banque"]
        embed = discord.Embed(title=f"💰 Solde de {cible.display_name}", color=0xFFD700)
        embed.add_field(name="👛 Cash", value=f"**{user['cash']:,}** 💵", inline=True)
        embed.add_field(name="🏦 Banque", value=f"**{user['banque']:,}** 💵", inline=True)
        embed.add_field(name="📊 Total", value=f"**{total:,}** 💵", inline=True)
        embed.set_thumbnail(url=cible.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command(name="daily")
    async def daily(self, ctx):
        """Récupère tes coins quotidiens"""
        db = load_db()
        user = get_user(db, ctx.author.id)
        now = time.time()
        diff = now - user["last_daily"]

        if diff < DAILY_COOLDOWN:
            restant = DAILY_COOLDOWN - diff
            h = int(restant // 3600)
            m = int((restant % 3600) // 60)
            await ctx.send(f"⏰ Tu as déjà récupéré ton daily ! Reviens dans **{h}h {m}min**.")
            return

        # Bonus de streak (simplifié)
        import random
        bonus = random.randint(0, 200)
        gain = DAILY_MONTANT + bonus

        user["cash"] += gain
        user["last_daily"] = now
        save_db(db)

        embed = discord.Embed(title="🎁 Daily récupéré !", color=0x00FF00)
        embed.add_field(name="💵 Gain", value=f"+**{gain:,}** coins !", inline=False)
        embed.add_field(name="👛 Nouveau solde", value=f"**{user['cash']:,}** coins", inline=False)
        embed.set_footer(text="Reviens demain pour ton prochain daily !")
        await ctx.send(embed=embed)

    @commands.command(name="pay", aliases=["donner", "transfer"])
    async def pay(self, ctx, membre: discord.Member, montant: int):
        """Envoyer de l'argent à quelqu'un"""
        if membre == ctx.author:
            await ctx.send("❌ Tu ne peux pas te payer toi-même !")
            return
        if montant <= 0:
            await ctx.send("❌ Le montant doit être positif !")
            return

        db = load_db()
        expediteur = get_user(db, ctx.author.id)
        destinataire = get_user(db, membre.id)

        if expediteur["cash"] < montant:
            await ctx.send(f"❌ Tu n'as que **{expediteur['cash']:,}** coins en cash !")
            return

        expediteur["cash"] -= montant
        destinataire["cash"] += montant
        save_db(db)

        embed = discord.Embed(title="💸 Transfert effectué !", color=0x00FF00)
        embed.add_field(name="De", value=ctx.author.display_name, inline=True)
        embed.add_field(name="À", value=membre.display_name, inline=True)
        embed.add_field(name="Montant", value=f"**{montant:,}** 💵", inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="top", aliases=["leaderboard", "classement_argent"])
    async def top(self, ctx):
        """Voir le classement des plus riches"""
        db = load_db()
        if not db:
            await ctx.send("❌ Pas encore de données !")
            return

        # Trier par total (cash + banque)
        classement = []
        for uid, data in db.items():
            total = data.get("cash", 0) + data.get("banque", 0)
            classement.append((uid, total))

        classement.sort(key=lambda x: x[1], reverse=True)

        embed = discord.Embed(title="🏆 Top 10 — Les plus riches", color=0xFFD700)
        medailles = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

        desc = ""
        for i, (uid, total) in enumerate(classement[:10]):
            try:
                user = await self.bot.fetch_user(int(uid))
                nom = user.display_name
            except:
                nom = f"Utilisateur {uid[:4]}"
            desc += f"{medailles[i]} **{nom}** — {total:,} 💵\n"

        embed.description = desc or "Aucun joueur pour l'instant."
        await ctx.send(embed=embed)

    @pay.error
    async def pay_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Utilisation : `$pay @utilisateur <montant>`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Mentionne un utilisateur et donne un montant valide.")

async def setup(bot):
    await bot.add_cog(Economie(bot))
