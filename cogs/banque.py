import discord
from discord.ext import commands
import time
from database import load_db, save_db, get_user

TAUX_INTERET = 0.02  # 2% par jour
INTERET_COOLDOWN = 86400  # 24h

class Banque(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="banque", aliases=["bank"])
    async def banque(self, ctx):
        """Voir ton compte bancaire"""
        db = load_db()
        user = get_user(db, ctx.author.id)
        save_db(db)

        embed = discord.Embed(title="🏦 Ta Banque", color=0x2ECC71)
        embed.add_field(name="💰 Solde bancaire", value=f"**{user['banque']:,}** 💵", inline=False)
        embed.add_field(name="👛 Cash disponible", value=f"**{user['cash']:,}** 💵", inline=False)
        embed.add_field(name="📈 Intérêts", value=f"**{TAUX_INTERET*100}%** par jour", inline=False)
        embed.set_footer(text="$deposer <montant> • $retirer <montant> • $interets")
        await ctx.send(embed=embed)

    @commands.command(name="deposer", aliases=["deposit", "dep"])
    async def deposer(self, ctx, montant: str):
        """Déposer de l'argent en banque"""
        db = load_db()
        user = get_user(db, ctx.author.id)

        if montant.lower() == "tout" or montant.lower() == "all":
            montant = user["cash"]
        else:
            try:
                montant = int(montant)
            except:
                await ctx.send("❌ Montant invalide ! Utilise un nombre ou `tout`.")
                return

        if montant <= 0:
            await ctx.send("❌ Le montant doit être positif !")
            return
        if user["cash"] < montant:
            await ctx.send(f"❌ Tu n'as que **{user['cash']:,}** coins en cash !")
            return

        user["cash"] -= montant
        user["banque"] += montant
        save_db(db)

        embed = discord.Embed(title="🏦 Dépôt effectué !", color=0x2ECC71)
        embed.add_field(name="💰 Déposé", value=f"+**{montant:,}** 💵", inline=False)
        embed.add_field(name="🏦 Nouveau solde banque", value=f"**{user['banque']:,}** 💵", inline=False)
        embed.add_field(name="👛 Cash restant", value=f"**{user['cash']:,}** 💵", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="retirer", aliases=["withdraw", "ret"])
    async def retirer(self, ctx, montant: str):
        """Retirer de l'argent de la banque"""
        db = load_db()
        user = get_user(db, ctx.author.id)

        if montant.lower() == "tout" or montant.lower() == "all":
            montant = user["banque"]
        else:
            try:
                montant = int(montant)
            except:
                await ctx.send("❌ Montant invalide ! Utilise un nombre ou `tout`.")
                return

        if montant <= 0:
            await ctx.send("❌ Le montant doit être positif !")
            return
        if user["banque"] < montant:
            await ctx.send(f"❌ Tu n'as que **{user['banque']:,}** coins en banque !")
            return

        user["banque"] -= montant
        user["cash"] += montant
        save_db(db)

        embed = discord.Embed(title="🏦 Retrait effectué !", color=0x2ECC71)
        embed.add_field(name="💰 Retiré", value=f"**{montant:,}** 💵", inline=False)
        embed.add_field(name="👛 Nouveau cash", value=f"**{user['cash']:,}** 💵", inline=False)
        embed.add_field(name="🏦 Banque restante", value=f"**{user['banque']:,}** 💵", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="interets", aliases=["interests", "int"])
    async def interets(self, ctx):
        """Récupère tes intérêts bancaires (2% par jour)"""
        db = load_db()
        user = get_user(db, ctx.author.id)
        now = time.time()

        if user["banque"] == 0:
            await ctx.send("❌ Tu n'as rien en banque ! Dépose de l'argent avec `$deposer`.")
            return

        diff = now - user.get("last_interets", 0)
        if diff < INTERET_COOLDOWN:
            restant = INTERET_COOLDOWN - diff
            h = int(restant // 3600)
            m = int((restant % 3600) // 60)
            await ctx.send(f"⏰ Tes intérêts ne sont pas encore disponibles ! Reviens dans **{h}h {m}min**.")
            return

        gain = int(user["banque"] * TAUX_INTERET)
        if gain == 0:
            gain = 1

        user["banque"] += gain
        user["last_interets"] = now
        save_db(db)

        embed = discord.Embed(title="📈 Intérêts récupérés !", color=0x2ECC71)
        embed.add_field(name="💰 Intérêts", value=f"+**{gain:,}** coins (2%)", inline=False)
        embed.add_field(name="🏦 Nouveau solde banque", value=f"**{user['banque']:,}** 💵", inline=False)
        embed.set_footer(text="Reviens demain pour tes prochains intérêts !")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Banque(bot))
