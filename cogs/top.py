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

    class TopView(disnake.ui.View):
        def __init__(self, cog, top_type: TopEnum, page=1):
            super().__init__(timeout=60)
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
                        emoji = "<a:time:1277018784900845672>"
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
                                            value=f"Время в войсе: {days} д. {hours} ч. {minutes} м. {emoji}",
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
                        emoji = "<a:time:1277018784900845672>"
                        if message_count < 1:
                            for child in self.children:
                                if isinstance(child, disnake.ui.Button) and child.custom_id == "next":
                                    child.disabled = True
                            await interaction.edit_original_message(view=self)

                        if member and not message_count == 0:
                            embed.add_field(name=f"{position_emoji} ``#{idx}``. {member.display_name}",
                                            value=f"Количество сообщений: {message_count}",
                                            inline=False)
                        elif not message_count == 0:
                            embed.add_field(name=f"``#{idx}``. ~~Неизвестный участник (ID: {user_id})~~",
                                            value=f"Количество сообщений: {message_count}",
                                            inline=False)
            elif self.top_type == 'Сделки':
                top_users = self.cog.get_top_users_deals(skip, self.items_per_page)
                embed = disnake.Embed(title="🏆 Топ участников по сделкам", color=0xffff00,
                                      timestamp=datetime.now())
                embed.set_thumbnail(url='https://i.imgur.com/64ibjZo.gif')
                if top_users:
                    for idx, (user_id, deals) in enumerate(top_users, start=skip + 1):
                        member = interaction.guild.get_member(user_id)
                        position_emoji = self.cog.position_emoji(idx)
                        emoji = "<a:time:1277018784900845672>"
                        if deals == 0:
                            for child in self.children:
                                if isinstance(child, disnake.ui.Button) and child.custom_id == "next":
                                    child.disabled = True
                            await interaction.edit_original_message(view=self)
                        if member and not deals == 0:
                            embed.add_field(name=f"{position_emoji} ``#{idx}``. {member.display_name}",
                                            value=f"Количество сделок: {deals}",
                                            inline=False)
                        elif not deals == 0:
                            embed.add_field(name=f"``#{idx}``. ~~Неизвестный участник (ID: {user_id})~~",
                                            value=f"Количество сделок: {deals}",
                                            inline=False)
                else:
                    disnake.Embed(description='Не нашлось')
            self.original_message = await interaction.edit_original_message(embed=embed, view=self)

        async def previous_page(self, interaction: disnake.MessageInteraction):
            await interaction.response.defer()  # Изменение здесь
            print(self.page)
            if self.page == 1:
                for child in self.children:
                    if isinstance(child, disnake.ui.Button) and child.custom_id == "previous":
                        child.disabled = True
                    return
                self.page += 1
            if self.page > 1:
                self.page -= 1
                await self.update_embed(interaction)

        async def next_page(self, interaction: disnake.MessageInteraction):
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
