import disnake
from disnake.ext import commands
from datetime import datetime
from main import cluster

collusers = cluster.server.users
collservers = cluster.server.servers


class TopEnum(disnake.enums.Enum):
    Румбики = "Румбики"
    Войс = "Войс"
    Сообщения = 'Сообщения'
    Сделки = 'Сделки'
    Репутация = 'Репутация'


class TopCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_top_users(self, skip=0, limit=10):
        top_records = collusers.find().sort('balance', -1).skip(skip).limit(limit)
        return [(record['id'], record['balance']) for record in top_records]

    def get_top_users_voice(self, skip=0, limit=10):
        top_records = collusers.find().sort('time_in_voice', -1).skip(skip).limit(limit)
        return [(record['id'], record['time_in_voice']) for record in top_records]

    def get_top_users_message_count(self, skip=0, limit=10):
        top_records = collusers.find().sort('message_count', -1).skip(skip).limit(limit)
        return [(record['id'], record['message_count']) for record in top_records]

    def get_top_users_deals(self, skip=0, limit=10):
        top_records = collusers.find().sort('number_of_deal', -1).skip(skip).limit(limit)
        return [(record['id'], record['number_of_deal']) for record in top_records]

    def get_top_users_reputation(self, skip=0, limit=10):
        top_records = collusers.find().sort('reputation', -1).skip(skip).limit(limit)
        return [(record['id'], record['reputation']) for record in top_records]

    def seconds_to_dhm(self, seconds):
        days = seconds // 86400  # 86400 секунд в одном дне
        hours = (seconds % 86400) // 3600  # 3600 секунд в одном часе
        minutes = (seconds % 3600) // 60  # 60 секунд в одной минуте
        days = round(days, 0)
        hours = round(hours, 0)
        minutes = round(minutes, 0)

        return days, hours, minutes

    def position_emoji(self, idx):
        if idx == 1:
            return "🥇"
        elif idx == 2:
            return "🥈"
        elif idx == 3:
            return "🥉"
        else:
            return ""

    def get_reputation_title(self, reputation):
        if 0 <= reputation < 20:
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
            return "Неизвестный"  # Default title for other values

    class TopView(disnake.ui.View):
        def __init__(self, cog, top_type: TopEnum, page=1):
            super().__init__(timeout=None)
            self.cog = cog
            self.top_type = top_type
            self.page = page
            self.items_per_page = 10  # Количество записей на страницу

            previous_button = disnake.ui.Button(label="⬅️", style=disnake.ButtonStyle.primary, custom_id='previous',
                                                disabled=True)
            previous_button.callback = self.previous_page
            self.add_item(previous_button)

            next_button = disnake.ui.Button(label="➡️", style=disnake.ButtonStyle.primary, custom_id='next')
            next_button.callback = self.next_page
            self.add_item(next_button)

            self.original_message = None

        async def update_embed(self, interaction):
            skip = (self.page - 1) * self.items_per_page
            if self.page != 1:
                for child in self.children:
                    if isinstance(child, disnake.ui.Button) and child.custom_id == "previous":
                        child.disabled = False

            if self.top_type == 'Румбики':
                top_users = self.cog.get_top_users(skip, self.items_per_page)
                embed = disnake.Embed(title="🏆 Топ участников по румбикам", color=0xffff00, timestamp=datetime.now())
                embed.set_thumbnail(url='https://i.imgur.com/64ibjZo.gif')
                if top_users:
                    for idx, (user_id, balance) in enumerate(top_users, start=skip + 1):
                        member = interaction.guild.get_member(user_id)
                        position_emoji = self.cog.position_emoji(idx)
                        emoji = "<a:rumbick_gif:1276856664842047518>"
                        if balance == 0:
                            for child in self.children:
                                if isinstance(child, disnake.ui.Button) and child.custom_id == "next":
                                    child.disabled = True
                            await interaction.edit_original_message(view=self)

                        if member and not balance == 0:
                            balance = round(balance, 2)
                            embed.add_field(name=f"{position_emoji} ``#{idx}``. {member.display_name}",
                                            value=f"Баланс: {balance}{emoji}", inline=False)
                        elif not balance == 0:
                            balance = round(balance, 2)
                            embed.add_field(name=f"``#{idx}``. ~~Неизвестный участник (ID: {user_id})~~",
                                            value=f"Баланс: {balance}{emoji}", inline=False)

            elif self.top_type == 'Войс':
                top_users = self.cog.get_top_users_voice(skip, self.items_per_page)
                embed = disnake.Embed(title="🏆 Топ участников по времени в войсе", color=0xffff00,
                                      timestamp=datetime.now())
                embed.set_thumbnail(url='https://i.imgur.com/64ibjZo.gif')
                if top_users:
                    for idx, (user_id, time_in_voice) in enumerate(top_users, start=skip + 1):
                        member = interaction.guild.get_member(user_id)
                        position_emoji = self.cog.position_emoji(idx)
                        emoji = "🎤"
                        if time_in_voice <= 60:
                            for child in self.children:
                                if isinstance(child, disnake.ui.Button) and child.custom_id == "next":
                                    child.disabled = True
                            await interaction.edit_original_message(view=self)

                        if member and not time_in_voice == 0:
                            days, hours, minutes = self.cog.seconds_to_dhm(time_in_voice)
                            embed.add_field(name=f"{position_emoji} ``#{idx}``. {member.display_name}",
                                            value=f"Время в войсе: {days} д. {hours} ч. {minutes} м. {emoji}",
                                            inline=False)
                        elif not time_in_voice == 0:
                            days, hours, minutes = self.cog.seconds_to_dhm(time_in_voice)
                            embed.add_field(name=f"``#{idx}``. ~~Неизвестный участник (ID: {user_id})~~",
                                            value=f"Время в войсе: ``{days} д. {hours} ч. {minutes} м.`` {emoji}",
                                            inline=False)

            elif self.top_type == 'Сообщения':
                top_users = self.cog.get_top_users_message_count(skip, self.items_per_page)
                embed = disnake.Embed(title="🏆 Топ участников по сообщениям", color=0xffff00,
                                      timestamp=datetime.now())
                embed.set_thumbnail(url='https://i.imgur.com/64ibjZo.gif')
                if top_users:
                    for idx, (user_id, message_count) in enumerate(top_users, start=skip + 1):
                        member = interaction.guild.get_member(user_id)
                        position_emoji = self.cog.position_emoji(idx)
                        emoji = "💬"
                        if message_count < 1:
                            for child in self.children:
                                if isinstance(child, disnake.ui.Button) and child.custom_id == "next":
                                    child.disabled = True
                            await interaction.edit_original_message(view=self)

                        if member and not message_count == 0:
                            embed.add_field(name=f"{position_emoji} ``#{idx}``. {member.display_name}",
                                            value=f"Сообщения: **{message_count}** {emoji}", inline=False)
                        elif not message_count == 0:
                            embed.add_field(name=f"``#{idx}``. ~~Неизвестный участник (ID: {user_id})~~",
                                            value=f"Сообщения: **{message_count}** {emoji}", inline=False)

            elif self.top_type == 'Сделки':
                top_users = self.cog.get_top_users_deals(skip, self.items_per_page)
                embed = disnake.Embed(title="🏆 Топ участников по сделкам", color=0xffff00, timestamp=datetime.now())
                embed.set_thumbnail(url='https://i.imgur.com/64ibjZo.gif')
                if top_users:
                    for idx, (user_id, number_of_deal) in enumerate(top_users, start=skip + 1):
                        member = interaction.guild.get_member(user_id)
                        position_emoji = self.cog.position_emoji(idx)
                        emoji = "💼"
                        if number_of_deal < 1:
                            for child in self.children:
                                if isinstance(child, disnake.ui.Button) and child.custom_id == "next":
                                    child.disabled = True
                            await interaction.edit_original_message(view=self)

                        if member and not number_of_deal == 0:
                            embed.add_field(name=f"{position_emoji} ``#{idx}``. {member.display_name}",
                                            value=f"Сделки: **{number_of_deal}** {emoji}", inline=False)
                        elif not number_of_deal == 0:
                            embed.add_field(name=f"``#{idx}``. ~~Неизвестный участник (ID: {user_id})~~",
                                            value=f"Сделки: **{number_of_deal}** {emoji}", inline=False)

            elif self.top_type == 'Репутация':
                top_users = self.cog.get_top_users_reputation(skip, self.items_per_page)
                embed = disnake.Embed(title="🏆 Топ участников по репутации", color=0xffff00, timestamp=datetime.now())
                embed.set_thumbnail(url='https://i.imgur.com/64ibjZo.gif')
                if top_users:
                    for idx, (user_id, reputation) in enumerate(top_users, start=skip + 1):
                        print(reputation)
                        member = interaction.guild.get_member(user_id)
                        position_emoji = self.cog.position_emoji(idx)
                        if reputation >= 0:
                            emoji = "<:rep_up:1278690709855010856>"
                        else:
                            emoji = "<:rep_down:1278690717652357201>"

                        if reputation == 0:
                            for child in self.children:
                                if isinstance(child, disnake.ui.Button) and child.custom_id == "next":
                                    child.disabled = True
                            await interaction.edit_original_message(view=self)

                        if member and not reputation == 0:
                            title = self.cog.get_reputation_title(reputation)
                            embed.add_field(name=f"{position_emoji} ``#{idx}``. {member.display_name}",
                                            value=f"Репутация: **{reputation}** {emoji} - ``{title}``", inline=False)
                        elif not reputation == 0:
                            title = self.cog.get_reputation_title(reputation)
                            embed.add_field(name=f"``#{idx}``. ~~Неизвестный участник (ID: {user_id})~~",
                                            value=f"Репутация: **{reputation}** {emoji} - ``{title}``", inline=False)

            await interaction.edit_original_message(embed=embed, view=self)

        async def previous_page(self, interaction: disnake.Interaction):
            await interaction.response.defer()  # Изменение здесь
            self.page -= 1
            if self.page <= 1:
                self.page = 1
                for child in self.children:
                    if isinstance(child, disnake.ui.Button) and child.custom_id == "previous":
                        child.disabled = True
            for child in self.children:
                if isinstance(child, disnake.ui.Button) and child.custom_id == "next":
                    child.disabled = False
            await self.update_embed(interaction)

        async def next_page(self, interaction: disnake.Interaction):
            await interaction.response.defer()  # Изменение здесь
            self.page += 1
            await self.update_embed(interaction)

    @commands.slash_command(name='top', description='Топ пользователи')
    async def top(self, inter: disnake.ApplicationCommandInteraction,
                  тип: TopEnum = commands.Param(description="Выберите тип топа")):
        if disnake.InteractionResponse:
            await inter.response.defer(ephemeral=True)
        view = self.TopView(self, тип)
        await view.update_embed(inter)


def setup(bot):
    bot.add_cog(TopCog(bot))
    print('TopCog is ready')
