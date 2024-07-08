import time
from asyncio import tasks
import disnake
from disnake.ext import commands, tasks
from datetime import datetime, timedelta
from pymongo import MongoClient

current_datetime = datetime.today()

cluster = MongoClient(
    "mongodb+srv://Skeletron:1337@cluster0.knkajvi.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
collusers = cluster.server.users
collservers = cluster.server.servers
collbans = cluster.server.bans


class InfoCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(name='userinfo', description='Выводит нужную информацию об участнике')
    async def user(self, inter: disnake.ApplicationCommandInteraction, участник: disnake.Member = None):
        embed = disnake.Embed(title=f"Информация об участнике **{участник.name}**:", url="",
                              description="", color=0x00b7ff, timestamp=datetime.now())
        embed.set_author(name=f"{участник.name}",
                         icon_url=f"{участник.avatar}")
        embed.set_thumbnail(url="https://media0.giphy.com/media/epyCv3K3uvRXw4LaPY/giphy.gif")
        if участник is None:
            warns_count = collusers.find_one({'id': inter.author.id, 'guild_id': inter.guild.id})['warns']
            ban = collbans.find_one({'id': inter.author.id, 'guild_id': inter.guild.id})['ban']
            case = collservers.find_one({'_id': inter.guild.id})['case']
            if ban == 'True':
                ban = 'Да.'
            else:
                ban = 'Нет.'

            if inter.author.current_timeout is not None:
                mute = 'Да.'
            else:
                mute = 'Нет.'

            embed.add_field(name=f'', value=f'Идентификатор: {inter.author.id}')
            embed.add_field(name=f'', value=f'Количество предупреждений: {warns_count}', inline=False)
            embed.add_field(name=f'', value=f'Находится ли участник в бане?: {ban}', inline=False)
            embed.add_field(name=f'', value=f'Находится ли участник в муте?: {mute}', inline=False)

            await inter.response.send_message(embed=embed, ephemeral=True)
            return
        warns_count = collusers.find_one({'id': участник.id, 'guild_id': inter.guild.id})['warns']
        ban = collbans.find_one({'id': участник.id, 'guild_id': inter.guild.id})['ban']
        case = collservers.find_one({'_id': inter.guild.id})['case']
        if ban == 'True':
            ban = 'Да'
        else:
            ban = 'Нет'
        if участник.current_timeout is not None:
            mute = 'Да'
        else:
            mute = 'Нет'
        embed.add_field(name=f'', value=f'**Идентификатор:** ``{inter.author.id}``')
        embed.add_field(name=f'', value=f'**Количество предупреждений:** ``{warns_count}``', inline=False)
        embed.add_field(name=f'', value=f'**Находится ли участник в бане?:** ``{ban}``', inline=False)
        embed.add_field(name=f'', value=f'**Находится ли участник в муте?:** ``{mute}``', inline=False)
        await inter.response.send_message(embed=embed, ephemeral=True)
        return


def setup(bot):
    bot.add_cog(InfoCog(bot))
    print("InfoCog is ready")
