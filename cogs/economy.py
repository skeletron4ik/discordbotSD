import disnake
from pymongo import MongoClient, errors, collection
from disnake.ext import commands, tasks
from datetime import datetime, timedelta
import os
import asyncio
import time
import random
import math

cluster = MongoClient(
    "mongodb+srv://Skeletron:1337@cluster0.knkajvi.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
collusers = cluster.server.users

collservers = cluster.server.servers

cooldowns = {}

voice_timestamps = {}

mute_timestamps = {}

total_time = {}


def format_duration(value):
    if value == 1:
        return "1 румбик"
    elif 2 <= value <= 4:
        return f"`{value}` румбика"
    else:
        return f"`{value}` румбиков"


class EconomyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_booster.start()

    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        if message.author.bot:
            return
        now = datetime.now()
        user_id = message.author.id
        if len(message.content) > 3:

            if user_id in cooldowns:
                last_used = cooldowns[user_id]
                if now - last_used < timedelta(minutes=1):
                    time_left = timedelta(minutes=1) - (now - last_used)
                    return

            money_to_give = random.uniform(0.1, 1)
            money_to_give = round(money_to_give, 2)
            multiplier = collservers.find_one({'_id': message.author.guild.id})['multiplier']
            collusers.find_one_and_update({'id': message.author.id}, {'$inc': {'balance': money_to_give * multiplier}})
            collusers.find_one_and_update({'id': message.author.id}, {'$inc': {'message_count': 1}})

            cooldowns[user_id] = now
            print(money_to_give)

    @commands.slash_command(name='balance', description='Показывает баланс игрока', aliases=['баланс'])
    async def balance(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member = None):
        await inter.response.defer()
        if member is None:
            member = inter.author
        embed = disnake.Embed(title=f'Информация о пользователе `{member.display_name}`', color=0x4169E1)

        if member is None:
            embed.timestamp = datetime.now()
            member = inter.author
            balance = collusers.find_one({"id": member.id})['balance']
            num_of_deals = collusers.find_one({'id': member.id})['number_of_deal']
            balance = round(balance, 2)
            balance = format_duration(balance)

            embed.add_field(name='Баланс:', value=f'{balance}', inline=True)
            embed.add_field(name='Количество сделок: ', value=f'`{num_of_deals}`', inline=True)
            embed.set_footer(text=f'ID: {member.id}', icon_url=member.avatar.url)
            await inter.edit_original_response(embed=embed)
        else:
            embed.timestamp = datetime.now()
            balance = collusers.find_one({"id": member.id})['balance']
            num_of_deals = collusers.find_one({'id': member.id})['number_of_deal']
            balance = round(balance, 2)
            balance = format_duration(balance)

            embed.add_field(name='Баланс:', value=f'{balance}', inline=True)
            embed.add_field(name='Количество сделок: ', value=f'`{num_of_deals}`', inline=True)
            embed.set_footer(text=f'ID: {member.id}', icon_url=member.avatar.url)
            await inter.edit_original_response(embed=embed)

    @commands.slash_command(name='transfer', description='Перевод румбиков участнику', aliases=['перевод', 'give'])
    async def transfer(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, количество: int):
        if disnake.InteractionResponse:
            await inter.response.defer()
        balance = collusers.find_one({"id": inter.author.id})['balance']

        if balance > количество:
            collusers.find_one_and_update({'id': inter.author.id}, {"$inc": {"balance": -количество}})
            collusers.find_one_and_update({'id': member.id}, {"$inc": {"balance": количество}})
            collusers.find_one_and_update({'id': member.id}, {'$inc': {'number_of_deal': 1}})
            collusers.update_many({'id': inter.author.id}, {'$inc': {'number_of_deal': 1}})

            количество = format_duration(количество)

            embed = disnake.Embed(title=f'Сделка `{inter.author.display_name}` и `{member.display_name}`',
                                  color=0x4169E1)
            embed.set_author(name=f'Отправитель: {inter.author.display_name}', icon_url=inter.author.avatar.url)
            embed.add_field(name=f'Отправитель', value=f'`{inter.author.display_name}`', inline=True)
            embed.add_field(name=f'Получатель:', value=f'`{member.display_name}`', inline=True)
            embed.add_field(name=f'Сумма сделки:', value=f'{количество}', inline=False)
            embed.set_footer(text=f'Получатель: {member.name}', icon_url=member.avatar.url)
            embed.timestamp = datetime.now()
            await inter.edit_original_response(embed=embed)

        else:
            unformatted = int(количество) - balance
            formatted = format_duration(unformatted)
            embed = disnake.Embed(title='Произошла ошибка', color=0x4169E1)
            embed.add_field(name=f'Отправитель', value=f'`{inter.author.display_name}`', inline=True)
            embed.add_field(name=f'Получатель:', value=f'`{member.display_name}`', inline=True)
            embed.add_field(name=f'Сумма сделки:', value=f'`{количество}`', inline=False)
            embed.add_field(name=f'Причина возникновения ошибки:', value=f'У отправителя не хватает {formatted}.',
                            inline=False)
            embed.set_footer(text=f'Использовал комманду: {inter.author.name}', icon_url=inter.author.avatar.url)
            embed.timestamp = datetime.now()
            await inter.edit_original_response(embed=embed)

    @commands.slash_command(name='givemoney')
    async def givemoney(self, inter: disnake.ApplicationCommandInteraction, участник: disnake.Member, количество: int):
        member = участник
        collusers.find_one_and_update({'id': member.id}, {'$inc': {'balance': количество}})

        await inter.response.send_message('сделано', ephemeral=True)

    @commands.slash_command(name='store', description='Магазин ролей и специальных возможностей',
                            aliases=['shop', 'магазин'])
    async def store(self, inter: disnake.ApplicationCommandInteraction):
        if inter.type == disnake.InteractionType.application_command:
            try:
                await inter.response.defer(ephemeral=True)
            except:
                return
        diamond = inter.guild.get_role(1044314368717897868)
        embed = disnake.Embed(title='**Магазин сервера**', color=0x4169E1)
        embed.add_field(name='**1. 💎 Diamond**',
                        value=f'Даёт эксклюзивные возможности. Подробнее с возможностями можно ознакомиться в канале https://discord.com/channels/489867322039992320/1069201052303380511\nЦена покупки: 399 ◊ | 699 ◊ | 949 ◊\nСодержит в себе: {diamond}',
                        inline=False)
        embed.add_field(name=f'**2. 🌠 Смена никнейма**',
                        value=f'Даёт возможность сменить свой отображаемый никнейм на сервере один раз.\nЦена покупки: 49 ◊\nСодержит в себе: Возможность смены отображаемого никнейма.',
                        inline=False)
        embed.add_field(name=f'**3. 🔹 Глобальный бустер румбиков x2**',
                        value=f'Активировать глобальный бустер румбиков на один день.\nЦена покупки: 799 ◊\nСодержит в себе: глобальный бустер румбиков x2/',
                        inline=False)

        options = [
            disnake.SelectOption(label="💎Diamond", description="Даёт эксклюзивные возможности", value="1"),
            disnake.SelectOption(label="🌠 Возможность сменить никнейм",
                                 description="При покупке Вы получаете возможность один раз сменить никнейм",
                                 value="2"),
            disnake.SelectOption(label="🔹 Глобальный бустер румбиков x2",
                                 description="Активировать глобальный бустер румбиков", value="3"),
        ]

        # Создаем select menu
        select_menu = disnake.ui.Select(
            placeholder="Выбрать предмет для покупки..",
            min_values=1,
            max_values=1,
            options=options,
        )

        async def select_callback(interaction: disnake.MessageInteraction):
            global embed1
            if select_menu.values[0] == "1":
                embed1 = disnake.Embed(color=0x4169E1)
                embed1.add_field(name='**Выберите длительность Diamond**', value='', inline=False)
                embed1.add_field(name='**Стоимость**',
                                 value='* 💎 Diamond\n * 💎 Diamond (на 30 дней) - 399 ◊\n * 💎 Diamond (на 60 дней) - 699 ◊ -15%\n * 💎 Diamond (на 90 дней) - 949 ◊ -20%',
                                 inline=False)
                embed1.set_footer(text=f'ID пользователя: {inter.author.id}', icon_url=inter.author.avatar.url)

                components = [
                    disnake.ui.Button(label="💎 Diamond (на 30 дней)", style=disnake.ButtonStyle.primary,
                                      emoji=diamond.emoji, custom_id='30'),
                    disnake.ui.Button(label="💎 Diamond (на 60 дней)", style=disnake.ButtonStyle.primary,
                                      emoji=diamond.emoji, custom_id='60'),
                    disnake.ui.Button(label="💎 Diamond (на 90 дней)", style=disnake.ButtonStyle.primary,
                                      emoji=diamond.emoji, custom_id='90')
                ]

                # Обрабатываем нажатие кнопки
                async def button_callback(interaction: disnake.MessageInteraction):
                    if interaction.component.custom_id == '30':
                        if collusers.find_one({'id': inter.author.id})['balance'] < 399:
                            await interaction.send('У Вас не хватает румбиков', ephemeral=True)
                            return

                        collusers.find_one_and_update({'id': interaction.author.id}, {'$inc': {'balance': -399}})
                        embed = disnake.Embed(color=0x4169E1)
                        роль = diamond
                        await interaction.author.add_roles(роль)
                        expiry = datetime.now() + timedelta(seconds=2678400)
                        expiry = int(expiry.timestamp())
                        collusers.update_one(
                            {"id": interaction.author.id, "guild_id": interaction.author.guild.id},
                            {
                                "$push": {"role_ids": {"role_ids": роль.id, "expires_at": expiry}},
                                "$inc": {"number_of_roles": 1}
                            },
                            upsert=True
                        )

                        embed = disnake.Embed(color=0x00d5ff, timestamp=datetime.now())
                        embed.add_field(name="Роль выдана",
                                        value=f"Роль {роль.name} выдана {interaction.author.display_name} и закончится <t:{expiry}:R>.")
                        embed.set_thumbnail(
                            url="https://media0.giphy.com/media/udvEcwFgNFboJWcHIB/giphy.gif?cid=6c09b952rqyuahrevsqie1hpf23xpwj9wdnqeyturtonwmhn&ep=v1_internal_gif_by_id&rid=giphy.gif&ct=ts")
                        await interaction.response.send_message(embed=embed)

                        channel = await self.bot.fetch_channel(944562833901899827)

                        embed = disnake.Embed(title="", url="", description="", color=0x00d5ff,
                                              timestamp=datetime.now())
                        embed.add_field(name="",
                                        value=f"Участник **{interaction.author.name}** ({interaction.author.mention}) получил роль ``{роль.name}``",
                                        inline=False)
                        embed.set_thumbnail(
                            url="https://media0.giphy.com/media/udvEcwFgNFboJWcHIB/giphy.gif?cid=6c09b952rqyuahrevsqie1hpf23xpwj9wdnqeyturtonwmhn&ep=v1_internal_gif_by_id&rid=giphy.gif&ct=ts")
                        embed.add_field(name="Модератор:", value=f"**Магазин** ({inter.author.mention})",
                                        inline=True)
                        embed.add_field(name="Канал:", value=f"{inter.channel.mention}", inline=True)
                        embed.add_field(name="Длительность:",
                                        value=f"(<t:{expiry}:R>)",
                                        inline=True)
                        embed.set_footer(text=f"ID участника: {interaction.author.id}")
                        await channel.send(embed=embed)

                    elif interaction.component.custom_id == '60':
                        if collusers.find_one({'id': inter.author.id})['balance'] < 699:
                            await interaction.send('У Вас не хватает румбиков', ephemeral=True)
                            return
                        collusers.find_one_and_update({'id': interaction.author.id}, {'$inc': {'balance': -699}})
                        embed = disnake.Embed(color=0x4169E1)
                        роль = diamond
                        await interaction.author.add_roles(роль)
                        expiry = datetime.now() + timedelta(seconds=5097600)

                        expiry = int(expiry.timestamp())
                        collusers.update_one(
                            {"id": interaction.author.id, "guild_id": interaction.author.guild.id},
                            {
                                "$push": {"role_ids": {"role_ids": роль.id, "expires_at": expiry}},
                                "$inc": {"number_of_roles": 1}
                            },
                            upsert=True
                        )

                        embed = disnake.Embed(color=0x00d5ff, timestamp=datetime.now())
                        embed.add_field(name="Роль выдана",
                                        value=f"Роль {роль.name} выдана {interaction.author.display_name} и закончится <t:{expiry}:R>.")
                        embed.set_thumbnail(
                            url="https://media0.giphy.com/media/udvEcwFgNFboJWcHIB/giphy.gif?cid=6c09b952rqyuahrevsqie1hpf23xpwj9wdnqeyturtonwmhn&ep=v1_internal_gif_by_id&rid=giphy.gif&ct=ts")
                        await interaction.response.send_message(embed=embed, ephemeral=True)

                        channel = await self.bot.fetch_channel(944562833901899827)

                        embed = disnake.Embed(title="", url="", description="", color=0x00d5ff,
                                              timestamp=datetime.now())
                        embed.add_field(name="",
                                        value=f"Участник **{interaction.author.name}** ({interaction.author.mention}) получил роль ``{роль.name}``",
                                        inline=False)
                        embed.set_thumbnail(
                            url="https://media0.giphy.com/media/udvEcwFgNFboJWcHIB/giphy.gif?cid=6c09b952rqyuahrevsqie1hpf23xpwj9wdnqeyturtonwmhn&ep=v1_internal_gif_by_id&rid=giphy.gif&ct=ts")
                        embed.add_field(name="Модератор:", value=f"**Магазин** ({inter.author.mention})",
                                        inline=True)
                        embed.add_field(name="Канал:", value=f"{inter.channel.mention}", inline=True)
                        embed.add_field(name="Длительность:",
                                        value=f"(<t:{expiry}:R>)",
                                        inline=True)
                        embed.set_footer(text=f"ID участника: {interaction.author.id}")
                        await channel.send(embed=embed)

                    elif interaction.component.custom_id == '90':
                        if collusers.find_one({'id': inter.author.id})['balance'] < 699:
                            await interaction.send('У Вас не хватает румбиков', ephemeral=True)
                            return
                        collusers.find_one_and_update({'id': interaction.author.id}, {'$inc': {'balance': -949}})
                        embed = disnake.Embed(color=0x4169E1)
                        роль = diamond
                        await interaction.author.add_roles(роль)
                        expiry = datetime.now() + timedelta(seconds=7776000)

                        expiry = int(expiry.timestamp())
                        collusers.update_one(
                            {"id": interaction.author.id, "guild_id": interaction.author.guild.id},
                            {
                                "$push": {"role_ids": {"role_ids": роль.id, "expires_at": expiry}},
                                "$inc": {"number_of_roles": 1}
                            },
                            upsert=True
                        )

                        embed = disnake.Embed(color=0x00d5ff, timestamp=datetime.now())
                        embed.add_field(name="Роль выдана",
                                        value=f"Роль {роль.name} выдана {interaction.author.display_name} и закончится <t:{expiry}:R>.")
                        embed.set_thumbnail(
                            url="https://media0.giphy.com/media/udvEcwFgNFboJWcHIB/giphy.gif?cid=6c09b952rqyuahrevsqie1hpf23xpwj9wdnqeyturtonwmhn&ep=v1_internal_gif_by_id&rid=giphy.gif&ct=ts")
                        await interaction.response.send_message(embed=embed, ephemeral=True)

                        channel = await self.bot.fetch_channel(944562833901899827)

                        embed = disnake.Embed(title="", url="", description="", color=0x00d5ff,
                                              timestamp=datetime.now())
                        embed.add_field(name="",
                                        value=f"Участник **{interaction.author.name}** ({interaction.author.mention}) получил роль ``{роль.name}``",
                                        inline=False)
                        embed.set_thumbnail(
                            url="https://media0.giphy.com/media/udvEcwFgNFboJWcHIB/giphy.gif?cid=6c09b952rqyuahrevsqie1hpf23xpwj9wdnqeyturtonwmhn&ep=v1_internal_gif_by_id&rid=giphy.gif&ct=ts")
                        embed.add_field(name="Модератор:", value=f"**Магазин** ({inter.author.mention})",
                                        inline=True)
                        embed.add_field(name="Канал:", value=f"{inter.channel.mention}", inline=True)
                        embed.add_field(name="Длительность:",
                                        value=f"(<t:{expiry}:R>)",
                                        inline=True)
                        embed.set_footer(text=f"ID участника: {interaction.author.id}")
                        await channel.send(embed=embed)

                for button in components:
                    button.callback = button_callback

                view = disnake.ui.View(timeout=None)
                for button in components:
                    view.add_item(button)

                await interaction.response.send_message(embed=embed1, ephemeral=True, view=view)

            if select_menu.values[0] == "2":
                if collusers.find_one({'id': inter.author.id})['balance'] < 49:
                    await interaction.send('У Вас не хватает румбиков', ephemeral=True)
                collusers.find_one_and_update({'id': interaction.author.id}, {'$inc': {'balance': -49}})
                components = disnake.ui.TextInput(
                    label=f"Никнейм",
                    custom_id="nickname",
                    style=disnake.TextInputStyle.short,
                    placeholder="52 тонны узбеков",
                    required=True,
                    min_length=1,
                    max_length=32,
                )

                modal = disnake.ui.Modal(
                    title="Смена никнейма",
                    custom_id="my_modal",
                    components=[components]
                )
                await interaction.response.send_modal(modal=modal)

            if select_menu.values[0] == "3":
                if collusers.find_one({'id': interaction.author.id})['balance'] < 799:
                    await interaction.send('У Вас не хватает румбиков', ephemeral=True)
                multiplier = collservers.find_one({'_id': interaction.author.guild.id})['multiplier']
                collusers.find_one_and_update({'_id': interaction.author.id}, {'$inc': {'balance': -799}})
                timestamp = int(datetime.now().timestamp()) + 86400
                collservers.find_one_and_update({'_id': interaction.author.guild.id}, {'$inc': {'global_booster_timestamp': int(timestamp)}})
                collservers.find_one_and_update({'_id': interaction.author.guild.id},
                                              {'$inc': {'global_booster_multiplier': int(2)}})
                if multiplier != 1:
                    collservers.find_one_and_update({'_id': interaction.author.guild.id},
                                                  {'$inc': {'multiplier': 2}})
                else:
                    collservers.find_one_and_update({'_id': interaction.author.guild.id},
                                                    {'$set': {'multiplier': 2}})
                embed = disnake.Embed(title="", url="", description="", color=0x00d5ff, timestamp=datetime.now())
                embed.add_field(name='**Бустер румбиков успешно приобретён**', value=f'{interaction.author.mention}, Вы успешно приобрели бустер румбиков x2 на один день.', inline=False)
                await interaction.send(embed=embed, ephemeral=True)
                channel = interaction.author.guild.get_channel(489867322039992323)
                embed = disnake.Embed(title="", url="", description="", color=0x00d5ff, timestamp=datetime.now())
                embed.add_field(name=f'**Бустер румбиков 2x активирован**', value=f'Участник сервера `{interaction.author.display_name}` ({interaction.author.mention}), активировал глобальный бустер румбиков x2 на один день!\n'
                                                                                  f'Бустер закончится <t:{timestamp}:R>', inline=False)
                await channel.send(embed=embed)

        select_menu.callback = select_callback

        # Создаем view и добавляем в него select menu
        view = disnake.ui.View()
        view.add_item(select_menu)

        # Отправляем сообщение с view

        await inter.edit_original_response(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_modal_submit(self, interaction: disnake.ModalInteraction):
        if interaction.custom_id == "my_modal":
            nickname = interaction.text_values["nickname"]
            await interaction.author.edit(nick=nickname)
            await interaction.response.send_message('Никнейм изменён.', ephemeral=True)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return
        channel = member.guild.get_channel(944562833901899827)
        now = int(datetime.now().timestamp())

        if before.self_mute != after.self_mute:
            if after.self_mute:
                # Участник замутился
                mute_timestamps[member.id] = now
                print(f'{member} замутился в {now}')
            else:
                # Участник размутился
                if member.id in mute_timestamps:
                    muted_duration = now - mute_timestamps.pop(member.id)
                    if member.id in total_time:
                        total_time[member.id] += muted_duration
                    else:
                        total_time[member.id] = muted_duration
                    print(f'{member} размутился в {now}, мьют продолжался {muted_duration} секунд')

        # Участник зашел в голосовой канал
        if before.channel is None and after.channel is not None:
            voice_timestamps[member.id] = now
            print(f'{member} зашел в войс в {now}')

        # Участник вышел из голосового канала
        elif before.channel is not None and after.channel is None:
            join_time = voice_timestamps.pop(member.id, None)
            if join_time:
                leave_time = now
                duration = leave_time - join_time

                if member.id in mute_timestamps:
                    muted_duration = leave_time - mute_timestamps.pop(member.id)
                    duration -= muted_duration
                    print(f'{member} вышел из войса в {leave_time}, время мьюта {muted_duration}')

                if member.id in total_time:
                    total_time[member.id] += duration
                else:
                    total_time[member.id] = duration

                print(
                    f'{member} провел в голосовом канале {duration} секунд, общее время {total_time[member.id]} секунд')

                minutes = round(total_time[member.id] / 60, 2)
                rumbiks = round(total_time[member.id] / 60 * 0.1, 2)
                if rumbiks > 1:
                    multiplier = collservers.find_one({'_id': member.guild.id})['multiplier']
                    collusers.find_one_and_update({'id': member.id}, {'$inc': {'balance': rumbiks * multiplier}})
                embed = disnake.Embed(color=0xe70404)
                embed.add_field(name='**Голосовая активность**',
                                value=f'Участник: `{member.display_name}` ({member.mention})'
                                      f'\nВремя в войсе: с <t:{join_time}:T> до <t:{leave_time}:T>'
                                      f'\nМинус в войсе (без учёта мута): `{minutes}`'
                                      f'\nМинут в войсе: `{round(duration / 60, 2)}`'
                                      f'\nВыданные румбики: `{rumbiks}`')
                timestamp = datetime.now()
                embed.set_footer(text=member.name, icon_url=member.avatar.url)
                embed.set_author(name='Shadow Dragons Economy', icon_url=member.guild.icon.url)

                if channel:
                    await channel.send(embed=embed)
            else:
                print(f'{member} вышел из войса, но время входа не найдено.')

    class TopEnum(disnake.enums.Enum):
        Румбики = "Румбики"

    def get_top_users(self):
        top_records = collusers.find().sort('balance', -1).limit(10)
        return [(record['id'], record['balance']) for record in top_records]

    @commands.slash_command(name='top', description='Топ пользователи', aliases=['топ', 'лучшие'])
    async def top(self, inter: disnake.ApplicationCommandInteraction,
                  тип: TopEnum = commands.Param(description="Выберите тип топа")):
        if тип == 'Румбики':
            embed = disnake.Embed(title="Топ участников по румбикам", description="", color=0x4169E1)
            top_records = collusers.find().sort('balance', -1).limit(10)
            top_users = self.get_top_users()
            for idx, (user_id, balance) in enumerate(top_users, start=1):
                member = inter.guild.get_member(user_id)
                if member:
                    embed.add_field(name=f"{idx}. {member.display_name}", value=f"Баланс: {balance}", inline=False)
                else:
                    embed.add_field(name=f"{idx}. Неизвестный участник (ID: {user_id})", value=f"Баланс: {balance}",
                                    inline=False)

            await inter.response.send_message(embed=embed, ephemeral=True)

    def convert_to_seconds(self, time_str):
        try:
            value = int(time_str[:-1])
        except ValueError:
            raise ValueError(f"Invalid time format: {time_str}")

        unit = time_str[-1]
        if unit == 'д' or unit == 'd':
            return value * 24 * 60 * 60
        elif unit == 'ч' or unit == 'h':
            return value * 60 * 60
        elif unit == 'м' or unit == 'm':
            return value * 60
        elif unit == 'с' or unit == 's':
            return value
        else:
            raise ValueError(f"Invalid time unit: {time_str[-1]}")

    @tasks.loop(seconds=60)
    async def check_booster(self):
        timestamp_booster = collservers.find_one({'_id': 489867322039992320})['booster_timestamp']
        global_timestamp_booster = collservers.find_one({'_id': 489867322039992320})['global_booster_timestamp']
        global_booster_multiplier = global_timestamp_booster = collservers.find_one({'_id': 489867322039992320})['global_booster_multiplier']
        admin_booster_multiplier = global_timestamp_booster = collservers.find_one({'_id': 489867322039992320})['admin_booster_multiplier']
        timestamp_now = int(datetime.now().timestamp())

        if timestamp_booster != 0 and global_timestamp_booster == 0:
            if timestamp_booster < timestamp_now:
                collservers.find_one_and_update({'_id': 489867322039992320}, {'$set': {'booster_timestamp': 0}})
                collservers.find_one_and_update({'_id': 489867322039992320}, {'$set': {'multiplier': 1}})
                collservers.find_one_and_update({'_id': 489867322039992320}, {'$set': {'admin_booster_multiplier': 0}})
                print('!= ==')
        elif timestamp_booster == 0 and global_timestamp_booster != 0:
            if timestamp_now > global_timestamp_booster:
                collservers.find_one_and_update({'_id': 489867322039992320}, {'$set': {'multiplier': 1}})
                collservers.find_one_and_update({'_id': 489867322039992320}, {'$set': {'global_booster_timestamp': 0}})
                collservers.find_one_and_update({'_id': 489867322039992320}, {'$set': {'global_booster_multiplier': 0}})
                print('== !=')
        elif timestamp_booster != 0 and global_timestamp_booster != 0:
            if timestamp_now > global_timestamp_booster and timestamp_now > timestamp_booster:
                collservers.find_one_and_update({'_id': 489867322039992320}, {'$set': {'global_booster_timestamp': 0}})
                collservers.find_one_and_update({'_id': 489867322039992320}, {'$set': {'global_booster_multiplier': 0}})
                collservers.find_one_and_update({'_id': 489867322039992320}, {'$set': {'booster_timestamp': 0}})
                collservers.find_one_and_update({'_id': 489867322039992320}, {'$set': {'multiplier': 1}})
                collservers.find_one_and_update({'_id': 489867322039992320}, {'$set': {'admin_booster_multiplier': 0}})
                print('!= != 1')

            elif timestamp_now > global_timestamp_booster:
                collservers.find_one_and_update({'_id': 489867322039992320}, {'$inc': {'multiplier': int(-global_booster_multiplier)}})
                collservers.find_one_and_update({'_id': 489867322039992320}, {'$set': {'global_booster_timestamp': 0}})
                collservers.find_one_and_update({'_id': 489867322039992320}, {'$set': {'global_booster_multiplier': 0}})
                print('!= != 1')
            elif timestamp_now > timestamp_booster:
                collservers.find_one_and_update({'_id': 489867322039992320}, {'$set': {'booster_timestamp': 0}})
                collservers.find_one_and_update({'_id': 489867322039992320}, {'$inc': {'multiplier': int(-admin_booster_multiplier)}})
                collservers.find_one_and_update({'_id': 489867322039992320}, {'$set': {'admin_booster_multiplier': 0}})
                print('!= != 2')






    @commands.slash_command(name='booster', description='Включает бустер румбиков')
    async def booster(self, inter: disnake.ApplicationCommandInteraction, multiplier: int, expiry: str):
        try:
            expiry = self.convert_to_seconds(expiry)
        except:
            embed = disnake.Embed(color=0xe70404)
            embed.add_field(name='Произошла ошибка', value='Ошибка в конвертации в секунды')
        timestamp = int(datetime.now().timestamp()) + expiry
        if collservers.find_one({'_id': 489867322039992320})['global_booster_timestamp'] != 0:
            collservers.find_one_and_update({'_id': inter.author.guild.id}, {'$inc': {'multiplier': int(multiplier)}})
            collservers.find_one_and_update({'_id': inter.author.guild.id}, {'$set': {'booster_timestamp': int(timestamp)}})
            collservers.find_one_and_update({'_id': inter.author.guild.id}, {'$set': {'admin_booster_multiplier': int(multiplier)}})
        else:
            collservers.find_one_and_update({'_id': inter.author.guild.id}, {'$set': {'multiplier': int(multiplier)}})
            collservers.find_one_and_update({'_id': inter.author.guild.id}, {'$set': {'booster_timestamp': int(timestamp)}})
            collservers.find_one_and_update({'_id': inter.author.guild.id}, {'$set': {'admin_booster_multiplier': int(multiplier)}})

        embed = disnake.Embed(color=0x4169E1)
        embed.add_field(name='**Бустер активирован**', value=f'Множитель: {multiplier}\nДата окончания: <t:{timestamp}:R>')
        await inter.response.send_message(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(EconomyCog(bot))
    print("Economy is ready")