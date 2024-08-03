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
        if inter.type == disnake.InteractionType.application_command:
            try:
                await inter.response.defer()
            except Exception as e:
                print(f"Error deferring response: {e}")
                return

        if участник is None:
            участник = inter.author

        embed = disnake.Embed(title=f"Информация об участнике ``{участник.name}``:", url="",
                              description="", color=0x00b7ff, timestamp=datetime.now())
        embed.set_author(name=f"{участник.display_name}",
                         icon_url=f"{участник.avatar}")
        embed.set_thumbnail(url="https://media0.giphy.com/media/epyCv3K3uvRXw4LaPY/giphy.gif")

        def get_user_info(member):
            try:
                user_data = collusers.find_one({'id': member.id, 'guild_id': inter.guild.id})
                warns_count = user_data.get('warns', 0)
                ban = user_data.get('ban', 'False')
                ban = 'Заблокирован' if ban == 'True' else 'Не заблокирован'
                mute = 'Замучен' if member.current_timeout else 'Не замучен'
                highest_role = sorted(member.roles, key=lambda r: r.position, reverse=True)[0]
                registration_time = member.created_at.strftime('%d-%m-%Y в %H:%M:%S')
                join_time = member.joined_at.strftime('%d-%m-%Y в %H:%M:%S')
                number_of_roles = user_data.get('number_of_roles')

                return warns_count, ban, mute, highest_role, registration_time, join_time, number_of_roles
            except Exception as e:
                print(f"Error getting user info: {e}")
                return (0, 'Неизвестно', 'Неизвестно', None, 'Неизвестно', 'Неизвестно', 0)

        warns_count, ban, mute, highest_role, registration_time, join_time, number_of_roles = get_user_info(участник)

        try:
            embed.add_field(name=f'',
                            value=f'**Основная роль:** {highest_role.mention if highest_role else "``Неизвестно``"}',
                            inline=False)
            embed.add_field(name=f'', value=f'**Идентификатор:** ``{участник.id}``')
            embed.add_field(name=f'', value=f'**Дата регистрации:** ``{registration_time}``', inline=False)
            embed.add_field(name=f'', value=f'**Присоединился:** ``{join_time}``', inline=False)
            embed.add_field(name=f'', value=f'-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-', inline=False)
            embed.add_field(name=f'', value=f'**Предупреждений:** ``{warns_count}``', inline=True)
            embed.add_field(name=f'', value=f'**Временных ролей:** ``{number_of_roles}``', inline=True)
            embed.add_field(name=f'', value=f'', inline=False)
            embed.add_field(name=f'', value=f'**Бан:** ``{ban}``', inline=True)
            embed.add_field(name=f'', value=f'**Мут:** ``{mute}``', inline=True)


            await inter.edit_original_response(embed=embed)
        except Exception as e:
            print(f"Error editing response: {e}")
            await inter.response.send_message(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(InfoCog(bot))
    print("InfoCog is ready")