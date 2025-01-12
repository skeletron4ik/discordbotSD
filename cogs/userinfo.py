import time
from asyncio import tasks
import disnake
from disnake.ext import commands, tasks
from datetime import datetime, timedelta
from pymongo import MongoClient
from datetime import datetime
from main import cluster
from .economy import format_time

current_datetime = datetime.today()

collusers = cluster.server.users
collservers = cluster.server.servers
collbans = cluster.server.bans
collpromos = cluster.server.promos

emoji = "<a:rumbick:1271085088142262303>"
boost_emoji = "<a:rainbowboost:1326163578193186926>"
boost_emoji2 = "<a:nitroboost:1326162624412651560>"
staff_emoji = "<:staff:1326175548107522121>"
person_emoji = "<:Person:1326179415712862249>"
bot_emoji = "<:bot:1326180225557463062>"
join_emoji = "<:join:1326181092511846443>"
left_emoji = "<:left:1326181104205430875>"
members_emoji = "<:members:1326181866255945828>"
channel_category = "<:channel_category:1326247079319961702>"
channel_voice = "<:channel_voice:1326247045626986526>"
channel_text = "<:channel_text:1326247036449980477>"
channel_stage = "<:channel_stage:1326247026186387479>"
channels_and_roles = "<:Channels_And_Roles:1326247017923477595>"
card_emoji = "<:CreditCard:1326304327220068412>"
transfer_emoji = "<:transfer:1326304316578861128>"
booster_emoji = "<:booster_orange:1326304303463403650>"
animated_emoji = "<a:jeb_spinning:1326304287155945675>"
mute_emoji = "<:mute:1326306581280850043>"
unmute_emoji = "<:unmute:1326307153723654174>"
ban_emoji = "<:ban:1326307160262578266>"
unban_emoji = "<:unban:1326307177190785114>"
warn_emoji = "<:warn:1326308182196359218>"
case_emoji = "<a:case:1326308167570952214>"
omegabox_emoji = "<:omegabox:1326308842920874115>"
commands_emoji = "<:commands:1326642896979492955>"
moder_emoji = "<:moder:1326643451609092106>"
cash_emoji = "<a:cash:1326643889238577254>"
nitro_emoji = "<:Nitro:1326652354078048419>"
pinknitro_emoji = "<:Pink_nitro:1326652343965581344>"
rubynitro_emoji = "<:Nitro_Ruby:1326652333416910879>"
ticket_emoji = "<:MegaPig_Ticket:1327358377499688970>"
rep_up_emoji = "<:rep_up:1234218072433365102>"
rep_down_emoji = "<:rep_down:1234218095116288154>"
def check_value(inter):
    result = collusers.update_one(
        {"id": inter.author.id, "guild_id": inter.guild.id, "settings": {"$exists": False}},
        {"$set": {}}
    )
    collusers.update_one(
        {"id": inter.author.id, "guild_id": inter.guild.id, 'settings.reputation_notification': {"$exists": False}},
        {"$set": {"settings.reputation_notification": False}})


class InfoCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(name='user-info', description='Выводит основную информацию об участнике',
                            dm_permission=False)
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def user(self, inter: disnake.ApplicationCommandInteraction, участник: disnake.Member = None):
        if inter.type == disnake.InteractionType.application_command:
            try:
                await inter.response.defer(ephemeral=True)
            except Exception as e:
                print(f"Error deferring response: {e}")
                return

        if участник is None:
            участник = inter.author
            settings = True

        embed = disnake.Embed(title=f"Информация об участнике ``{участник.name}``:", url="",
                              description="", color=0x00b7ff, timestamp=datetime.now())
        embed.set_author(name=f"{участник.display_name}",
                         icon_url=f"https://media0.giphy.com/media/epyCv3K3uvRXw4LaPY/giphy.gif")
        embed.set_thumbnail(url=участник.avatar.url if участник.avatar else участник.default_avatar.url)

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
                reputation = user_data.get('reputation', 0)
                bumps = user_data.get('bumps', 0)
                opened_cases = user_data.get('opened_cases', 0)
                promocodes = user_data.get('promocodes', 0)
                keys = user_data.get('keys', 0)

                return warns_count, ban, mute, highest_role, registration_time, join_time, temporary_roles, number_of_roles, message_count, time_in_voice, balance, number_of_deal, reputation, bumps, opened_cases, promocodes, keys
            except Exception as e:
                print(f"Error getting user info: {e}")
                return ('Неизвестно', 'Неизвестно', 'Неизвестно', 'Неизвестно', 'Неизвестно', 'Неизвестно', 'Неизвестно', 'Неизвестно', 'Неизвестно', 'Неизвестно', 'Неизвестно', 'Неизвестно', 'Неизвестно', 'Неизвестно', 'Неизвестно', 'Неизвестно', "Неизвестно")

        warns_count, ban, mute, highest_role, registration_time, join_time, temporary_roles, number_of_roles, message_count, time_in_voice, balance, number_of_deal, reputation, bumps, opened_cases, promocodes, keys = get_user_info(
            участник)

        def get_reputation_title(reputation):
            if -9 <= reputation < 20:
                return "Нормальный"
            elif 20 <= reputation <= 49:
                return "Хороший"
            elif 50 <= reputation <= 99:
                return "Очень хороший"
            elif 100 <= reputation <= 159:
                return "Замечательный"
            elif 160 <= reputation <= 229:
                return "Прекрасный"
            elif 230 <= reputation <= 309:
                return "Уважаемый"
            elif 310 <= reputation <= 399:
                return "Потрясающий"
            elif reputation >= 400:
                return "Живая Легенда"
            elif -10 >= reputation >= -19:
                return "Сомнительный"
            elif -20 >= reputation >= -29:
                return "Плохой"
            elif -30 >= reputation >= -39:
                return "Очень плохой"
            elif -40 >= reputation >= -49:
                return "Ужасный"
            elif -50 >= reputation >= -59:
                return "Отвратительный"
            elif -60 >= reputation >= -79:
                return "Презираемый"
            elif -80 >= reputation >= -99:
                return "Изгой"
            elif reputation <= -100:
                return "Враг общества"
            else:
                return "Неизвестный"

        reputation_title = get_reputation_title(reputation)

        def format_time(seconds):
            days, seconds = divmod(seconds, 86400)
            hours, seconds = divmod(seconds, 3600)
            minutes, seconds = divmod(seconds, 60)

            time_components = []
            if days > 0:
                time_components.append(f'{int(days)} д')
            if hours > 0:
                time_components.append(f'{int(hours)} ч')
            if minutes > 0:
                time_components.append(f'{int(minutes)} мин')
            if seconds > 0 or not time_components:
                time_components.append(f'{int(seconds)} сек')

            return ', '.join(time_components)

        formatted_total_time = format_time(time_in_voice)

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
            disnake.Status.online: "<:ONLINE:1327360338861097041> ``В сети``",
            disnake.Status.offline: "<:ONLINE:1327360338861097041> Не в сети",
            disnake.Status.idle: "<:IDLE:1327360352144592966> ``Неактивен``",
            disnake.Status.dnd: "<:DO_NOT_DISTURB:1327360366249771028> ``Не беспокоить``"
        }
        status = status_dict.get(участник.status, "Неизвестно")
        voice_channel = участник.voice.channel.mention if участник.voice and участник.voice.channel else "Не в голосовом канале"
        current_game = None
        for activity in участник.activities:
            if isinstance(activity, disnake.Game):
                current_game = activity.name
                break

        check_value(inter)
        query = {"id": inter.author.id, "guild_id": inter.guild_id}

        projection = {'_id': 0, "settings.reputation_notification": 1}

        result = collusers.find_one(query, projection)
        result = result["settings"]["reputation_notification"]
        print(result)
        if result:
            options = [
                disnake.SelectOption(label=f"🟢 Оповещение об изменении репутации",
                                     description="Оповещение об изменении репутации. Статус: 🟢", value="1"),
            ]
        else:
            options = [
                disnake.SelectOption(label=f"🔴 Оповещение об из менении репутации",
                                     description="Оповещение об изменении репутации. Статус: 🔴", value="1"),
            ]

        # Создаем select menu
        select_menu = disnake.ui.Select(
            placeholder="Поменять настройки...",
            min_values=1,
            max_values=1,
            options=options,
        )

        async def select_callback(interaction: disnake.MessageInteraction):
            await interaction.response.defer(ephemeral=True)
            result2 = collusers.find_one(query, projection)
            result2 = result2["settings"]["reputation_notification"]
            if select_menu.values[0] == "1":
                if interaction.author.id != inter.author.id:
                    await interaction.followup.send('проверка на долбоеба не пройдена', ephemeral=True)
                if result2:
                    collusers.update_one(
                        {"id": interaction.author.id, "guild_id": interaction.guild.id},
                        {"$set": {"settings.reputation_notification": False}})
                    await interaction.followup.send('вы изменили настройку (выключено)', ephemeral=True)
                else:
                    collusers.update_one(
                        {"id": interaction.author.id, "guild_id": interaction.guild.id},
                        {"$set": {"settings.reputation_notification": True}})
                    await interaction.followup.send('вы изменили настройку (включено)', ephemeral=True)


                result1 = collusers.find_one(query, projection)
                result1 = result1["settings"]["reputation_notification"]

                if result1:
                    options1 = [
                        disnake.SelectOption(label=f"🟢 Оповещение об изменении репутации",
                                             description="Оповещение об изменении репутации. Статус: 🟢", value="1"),
                    ]
                else:
                    options1 = [
                        disnake.SelectOption(label=f"🔴 Оповещение об из менении репутации",
                                             description="Оповещение об изменении репутации. Статус: 🔴", value="1"),
                    ]

                # Создаем select menu
                select_menu1 = disnake.ui.Select(
                    placeholder="Поменять настройки...",
                    min_values=1,
                    max_values=1,
                    options=options1,
                )

                select_menu1.callback = select_callback

                # Создаем view и добавляем в него select menu
                view1 = disnake.ui.View()
                view1.add_item(select_menu1)

                await inter.edit_original_response(embed=embed, view=view1)

        try:
            embed.add_field(name=f'',
                            value=f'**Основная роль:** {highest_role.mention if highest_role else "``Неизвестно``"}',
                            inline=False)
            embed.add_field(name=f'', value=f'**👁️‍🗨️ Статус:** {status}', inline=False)
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
            if reputation >= 0:
                rep_emoji = "<:rep_up:1234218072433365102>"
            else:
                rep_emoji = "<:rep_down:1234218095116288154>"
            embed.add_field(name=f'', value=f'**⭐ Репутация:** ``{reputation}`` {rep_emoji} - ``{reputation_title}``',
                            inline=False)
            embed.add_field(name=f'', value=f'**🖊️ Сообщений:\n** ``{message_count}``', inline=True)
            embed.add_field(name=f'',
                            value=f'**🎤 Голосовая активность:\n** ``{formatted_total_time}``',
                            inline=True)
            embed.add_field(name='', value='', inline=False)
            embed.add_field(name=f'', value=f'**💸 Баланс:** ``{balance}``{emoji}', inline=True)
            embed.add_field(name=f'', value=f'**💼 Сделок:** ``{number_of_deal}``', inline=True)
            embed.add_field(name='', value='', inline=False)
            embed.add_field(name=f'', value=f'{ticket_emoji} **Промокодов:** ``{promocodes}``', inline=True)
            embed.add_field(name=f'', value=f'🆙 **Бампов:** ``{bumps}``', inline=True)
            embed.add_field(name='', value='', inline=False)
            embed.add_field(name=f'', value=f'🔑 **Ключей:** ``{keys}``', inline=True)
            embed.add_field(name=f'', value=f'{omegabox_emoji} **Открыто якщиков:** ``{opened_cases}``', inline=True)



            # Проверка перед выводом секции с предупреждениями, баном, мутом и временными ролями
            if warns_count != "Не имеется" or ban != "Не заблокирован" or mute != "Не замучен" or number_of_roles != "Не имеется":
                embed.add_field(name=f'', value=f'-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-',
                                inline=False)
            if warns_count != "Не имеется":
                embed.add_field(name=f'', value=f'**⚠️ Предупреждений:\n** ``{warns_count}``', inline=True)
            if ban != "Не заблокирован":
                embed.add_field(name=f'', value=f'**🔒 Бан:\n** ``{ban}``', inline=True)
            if mute != "Не замучен":
                embed.add_field(name=f'', value=f'**🙊 Мут:\n** ``{mute}``', inline=True)
            if number_of_roles != "Не имеется":
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

            if участник != True:
                select_menu.callback = select_callback

                # Создаем view и добавляем в него select menu
                view = disnake.ui.View()
                view.add_item(select_menu)

                await inter.edit_original_response(embed=embed, view=view)
            else:
                await inter.edit_original_response(embed=embed)
        except Exception as e:
            print(f"Error editing response: {e}")

            if участник is None:
                select_menu.callback = select_callback

                # Создаем view и добавляем в него select menu
                view = disnake.ui.View()
                view.add_item(select_menu)

                await inter.response.send_message(embed=embed, ephemeral=True, view=view)
            else:
                await inter.response.send_message(embed=embed, ephemeral=True)

    @commands.slash_command(name='server-info', description="Показать информацию о сервере")
    async def server_info(self, inter: disnake.ApplicationCommandInteraction):
        guild = inter.guild
        guild_id = guild.id
        emoji = "<a:rumbick:1271085088142262303>"
        # Сбор данных из базы
        server_data = collservers.find_one({"_id": guild_id})
        server_data_promos = collpromos.find_one({"_id": guild_id})
        if not server_data:
            await inter.response.send_message("Данные о сервере отсутствуют в базе.", ephemeral=True)
            return

        # Сбор данных о сервере
        owner = guild.owner
        total_members = guild.member_count
        bots = len([member for member in guild.members if member.bot])
        humans = total_members - bots
        roles = len(guild.roles)
        channels = len(guild.channels)
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        stage_channels = len(guild.stage_channels)
        categories = len(guild.categories)
        emojis = len(guild.emojis)
        static_emojis = len([emoji for emoji in guild.emojis if not emoji.animated])
        animated_emojis = len([emoji for emoji in guild.emojis if emoji.animated])
        boosts = guild.premium_subscription_count
        boost_tier = guild.premium_tier
        nitro_boosters = guild.premium_subscribers
        nitro_boosters_count = len(nitro_boosters)
        nitro_boosters_names = ", ".join([member.mention for member in nitro_boosters]) if nitro_boosters else "Нет бустеров"
        created_at_timestamp = int(guild.created_at.timestamp())
        stickers = len(guild.stickers)

        # Форматирование данных из базы
        multiplier = server_data.get("multiplier", 1)
        opened_cases = server_data.get("opened_cases", 0)
        messages = server_data.get("messages", 0)
        bumps = server_data.get("bumps", 0)
        time_in_voice = format_time(server_data.get("time_in_voice", 0))
        voice_rumbiks = round(server_data.get("voice_rumbiks", 0), 2)
        chat_rumbicks = round(server_data.get("chat_rumbicks", 0), 2)
        total_rumbicks = round(server_data.get("total_rumbicks", 0), 2)
        mutes = server_data.get("mutes", 0)
        unmutes = server_data.get("unmutes", 0)
        bans = server_data.get("bans", 0)
        unbans = server_data.get("unbans", 0)
        warns = server_data.get("warns", 0)
        cases = server_data.get("case", 0)
        unwarns = server_data.get("unwarns", 0)
        deals = server_data.get("deals", 0)
        transfers = server_data.get("transfers", 0)
        wasted_rumbiks = round(server_data.get("wasted_rumbiks", 0), 2)
        members_join = server_data.get("members_join", 0)
        members_leave = server_data.get("members_leave", 0)
        commands_use = server_data.get("commands_use", 0)
        activation_promos = server_data.get("activation_promos", 0)
        created_promos = server_data_promos.get("counter", 0)
        rep_down = server_data.get("rep_down", 0)
        rep_up = server_data.get("rep_up", 0)
        rep_count = server_data.get("reputation_count", 0)

        # Роли для Staff сервера
        staff_roles = {
            "Администратор": 518505773022838797,
            "Гл. Модер": 580790278697254913,
            "Модер": 702593498901381184,
            "Разработчик": 1229337640839413813,
        }

        staff_info = ""
        for role_name, role_id in staff_roles.items():
            role = guild.get_role(role_id)
            if role:
                members_with_role = [member.mention for member in role.members]
                members_list = ", ".join(members_with_role) if members_with_role else "Никого"
                staff_info += f"**{role.mention}:** {members_list}\n"
            else:
                staff_info += f"**{role_name}:** Роль не найдена\n"

        # Формирование Embed
        embed = disnake.Embed(
            title=f"Информация о сервере: {guild.name}",
            color=disnake.Color.blurple(),
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.set_footer(text=f"ID сервера: {guild.id}")
        embed.set_author(name=f"{guild.name}",
                         icon_url=f"https://media0.giphy.com/media/epyCv3K3uvRXw4LaPY/giphy.gif")

        embed.add_field(name="🌟 Основная информация:", value=(
            f"👑 **Владелец:** {owner.mention if owner else 'Неизвестно'}\n"
            f"📅 **Дата создания:** <t:{created_at_timestamp}:F>\n"
            f"{boost_emoji} **Уровень бустов:** {boost_tier}\n"
            f"{boost_emoji2} **Количество бустов:** {boosts}"
        ), inline=False)

        # Добавление информации о Staff
        embed.add_field(name=f"{staff_emoji} Staff сервера:", value=staff_info or "Нет информации", inline=False)

        embed.add_field(name="👥 Участники:", value=(
            f"{members_emoji} **Всего:** {total_members}\n"
            f"{person_emoji} **Люди:** {humans}\n"
            f"{bot_emoji} **Боты:** {bots}\n"
            f"{join_emoji} **Присоединились:** {members_join}\n"
            f"{left_emoji} **Покинули:** {members_leave}"
        ), inline=True)

        embed.add_field(name=f"{nitro_emoji} Nitro-бустеры:", value=(
            f"{pinknitro_emoji} **Количество:** {nitro_boosters_count}\n"
            f"{rubynitro_emoji} **Список:** {nitro_boosters_names}"
        ), inline=True)
        embed.add_field(name='', value='', inline=False)
        embed.add_field(name="💬 Каналы:", value=(
            f"{channels_and_roles} **Всего:** {channels}\n"
            f"{channel_text} **Текстовые:** {text_channels}\n"
            f"{channel_voice} **Голосовые:** {voice_channels}\n"
            f"{channel_stage} **Сценические:** {stage_channels}\n"
            f"{channel_category} **Категории:** {categories}"
        ), inline=True)
        embed.add_field(name="🎨 Персонализация:", value=(
            f"🤔 **Статичные эмодзи:** {static_emojis}\n"
            f"{animated_emoji} **Анимированные эмодзи:** {animated_emojis}\n"
            f"🤼 **Всего эмодзи:** {emojis}\n"
            f"🎭 **Всего ролей:** {roles}\n"
            f"🖼️ **Всего стикеров:** {stickers}"
        ), inline=True)

        embed.add_field(name='', value='', inline=False)
        # Статистика по румбикам
        embed.add_field(name=f"{emoji} Румбики:", value=(
            f"{booster_emoji} **Текущий множитель:** x{multiplier}\n"
            f"🎙️ **За голосовые:** {voice_rumbiks}\n"
            f"💬 **За текстовые:** {chat_rumbicks}\n"
            f"{cash_emoji} **Всего:** {total_rumbicks}\n"
            f"{card_emoji} **Потрачено:** {wasted_rumbiks}\n"
            f"🤝 ** Сделок совершено:** {deals}\n"
            f"{transfer_emoji} **Переводов совершено:** {transfers}"
        ), inline=True)

        # Статистика по мутам и банам
        embed.add_field(name=f"{moder_emoji} Модерация:", value=(
            f"{mute_emoji} **Муты:** {mutes}\n"
            f"{unmute_emoji} **Размуты:** {unmutes}\n"
            f"{ban_emoji} **Баны:** {bans}\n"
            f"{unban_emoji} **Разбаны:** {unbans}\n"
            f"{warn_emoji} **Предупреждения:** {warns}\n"
            f"{case_emoji} **Случаи:** {cases}\n"
            f"✅ **Снято предупреждений:** {unwarns}"
        ), inline=True)

        # Статистика по использованию команд
        embed.add_field(name="🛠️ Остальное:", value=f"{commands_emoji} **Команд использовано:** {commands_use}\n"
                                                               f"📝 **Всего сообщений:** {messages}\n"
                                                               f"🆙 **Всего Бампов:** {bumps}\n"
                                                               f"{omegabox_emoji} **Всего открыто ящиков:** {opened_cases}\n"
                                                               f"🎟️ **Создано промокодов:** {created_promos}\n"
                                                               f"{ticket_emoji} **Активировано промокодов:** {activation_promos}\n"
                                                               f"{rep_up_emoji} **Количество положительной репутации:** {rep_up}\n"
                                                               f"{rep_down_emoji} **Количество отрицательной репутации:** {rep_down}\n"
                                                               f"🌟 **Общее количество репутации:** {rep_count}\n"
                                                               f"🎤 **Общаяя голосовая статистика:** ``{time_in_voice}``",
                        inline=False)

        # Отправка Embed
        await inter.response.send_message(embed=embed, ephemeral=True)

    @commands.slash_command(name='ping', description="Показать информацию о сервере бота")
    async def ping(self, inter: disnake.ApplicationCommandInteraction):
        embed = disnake.Embed(
            title=f"Информация о сервере: {inter.guild.name}",
            color=disnake.Color.blurple(),
            timestamp=datetime.now()
        )
        embed.add_field(name='Пинг до сервера:', value=f'```{round(self.bot.latency *1000,2)} ms```')
        embed.set_thumbnail(url=inter.guild.icon.url if inter.guild.icon else None)
        embed.set_footer(text=f"ID сервера: {inter.guild.id}")
        embed.set_author(name=f"{inter.guild.name}",
                        icon_url=f"https://media0.giphy.com/media/epyCv3K3uvRXw4LaPY/giphy.gif")
        await inter.response.send_message('Pong!', embed=embed, ephemeral=True)
def setup(bot):
    bot.add_cog(InfoCog(bot))
    print("InfoCog is ready")