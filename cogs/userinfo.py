import time
from asyncio import tasks
import disnake
from disnake.ext import commands, tasks
from datetime import datetime, timedelta
from pymongo import MongoClient
from datetime import datetime
from main import cluster

current_datetime = datetime.today()

collusers = cluster.server.users
collservers = cluster.server.servers
collbans = cluster.server.bans


class InfoCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(name='user-info', description='Выводит основную информацию об участнике')
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
                if warns_count == 0:
                    warns_count = "Не имеется"
                ban = user_data.get('ban', 'False')
                ban = 'Заблокирован' if ban == 'True' else 'Не заблокирован'
                mute = 'Замучен' if member.current_timeout else 'Не замучен'
                highest_role = sorted(member.roles, key=lambda r: r.position, reverse=True)[0]
                registration_time = member.created_at
                join_time = member.joined_at
                temporary_roles = user_data.get('role_ids', [])
                number_of_roles = user_data.get('number_of_roles', 0)
                if number_of_roles == 0:
                    number_of_roles = 'Не имеется'
                message_count = user_data.get('message_count', 0)
                time_in_voice = user_data.get('time_in_voice', 0)
                balance = round(user_data.get('balance', 0), 2)
                number_of_deal = user_data.get('number_of_deal', 0)

                return warns_count, ban, mute, highest_role, registration_time, join_time, temporary_roles, number_of_roles, message_count, time_in_voice, balance, number_of_deal
            except Exception as e:
                print(f"Error getting user info: {e}")
                return (0, 'Неизвестно', 'Неизвестно', None, 'Неизвестно', 'Неизвестно', [], 0, 0, 0, 0, 0)

        warns_count, ban, mute, highest_role, registration_time, join_time, temporary_roles, number_of_roles, message_count, time_in_voice, balance, number_of_deal = get_user_info(
            участник)

        def format_minutes(minutes):
            if 11 <= minutes % 100 <= 19:
                return "минут"
            elif minutes % 10 == 1:
                return "минута"
            elif 2 <= minutes % 10 <= 4:
                return "минуты"
            else:
                return "минут"

        # Определение статуса пользователя
        status_dict = {
            disnake.Status.online: "🟢 В сети",
            disnake.Status.offline: "⚫️ Не в сети",
            disnake.Status.idle: "🟡 Неактивен",
            disnake.Status.dnd: "🔴 Не беспокоить"
        }
        status = status_dict.get(участник.status, "Неизвестно")
        voice_channel = участник.voice.channel.mention if участник.voice and участник.voice.channel else "Не в голосовом канале"
        current_game = None
        for activity in участник.activities:
            if isinstance(activity, disnake.Game):
                current_game = activity.name
                break

        try:
            embed.add_field(name=f'',
                            value=f'**Основная роль:** {highest_role.mention if highest_role else "``Неизвестно``"}',
                            inline=False)
            embed.add_field(name=f'', value=f'**👁️‍🗨️ Статус:** ``{status}``', inline=False)
            if участник.voice and участник.voice.channel:
                embed.add_field(name=f'',
                                value=f'**🔊️ Голосовой канал:** {voice_channel}', inline=False)
            if current_game:
                embed.add_field(name=f'', value=f'**🎮 Играет в:** ``{current_game}``', inline=False)
            embed.add_field(name=f'',
                            value=f'**🌍 Зарегистрирован:\n** <t:{int(registration_time.timestamp())}:F> (<t:{int(registration_time.timestamp())}:R>)',
                            inline=True)
            embed.add_field(name=f'',
                            value=f'**🌎 Присоединился:\n** <t:{int(join_time.timestamp())}:F> (<t:{int(join_time.timestamp())}:R>)',
                            inline=True)
            embed.add_field(name='', value='', inline=False)
            embed.add_field(name=f'', value=f'**🖊️ Количество сообщений:\n** ``{message_count}``', inline=True)
            embed.add_field(name=f'',
                            value=f'**🎤 Всего в голосовом канале:\n** ``{time_in_voice // 60} {format_minutes(time_in_voice // 60)}``',
                            inline=True)
            embed.add_field(name='', value='', inline=False)
            embed.add_field(name=f'', value=f'**💸 Баланс:** ``{balance}``◊', inline=True)
            embed.add_field(name=f'', value=f'**💼 Количество сделок:** ``{number_of_deal}``', inline=True)
            embed.add_field(name=f'', value=f'-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-', inline=False)
            embed.add_field(name=f'', value=f'**⚠️ Предупреждений:\n** ``{warns_count}``', inline=True)
            embed.add_field(name=f'', value=f'**🔒 Бан:\n** ``{ban}``', inline=True)
            embed.add_field(name='', value='', inline=False)
            embed.add_field(name=f'', value=f'**🙊 Мут:\n** ``{mute}``', inline=True)
            embed.add_field(name=f'', value=f'**🕒 Временных ролей:\n** ``{number_of_roles}``', inline=True)

            if temporary_roles:
                for role_info in temporary_roles:
                    role_id = role_info.get('role_ids')
                    expires_at = role_info.get('expires_at')
                    role = inter.guild.get_role(role_id)
                    if role:
                        embed.add_field(
                            name=f'',
                            value=f'{role.mention} - истекает: <t:{int(expires_at)}:R>',
                            inline=False
                        )
            embed.set_footer(text=f'ID: {участник.id}')

            await inter.edit_original_response(embed=embed)
        except Exception as e:
            print(f"Error editing response: {e}")
            await inter.response.send_message(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(InfoCog(bot))
    print("InfoCog is ready")