import time
from asyncio import tasks
import disnake
from disnake.ext import commands, tasks
from datetime import datetime, timedelta
from pymongo import MongoClient
from disnake import TextInputStyle

current_datetime = datetime.today()

cluster = MongoClient(
    "mongodb+srv://Skeletron:1337@cluster0.knkajvi.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
collusers = cluster.server.users
collservers = cluster.server.servers
collbans = cluster.server.bans


class ActionCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.участник = '1'

    class BanModal(disnake.ui.Modal):
        def __init__(self):
            components = [
                disnake.ui.TextInput(
                    label="Длительность",
                    placeholder="15d",
                    custom_id="ban_duration",
                    style=disnake.TextInputStyle.short,
                ),
                disnake.ui.TextInput(
                    label="Причина",
                    placeholder="Причина не указана.",
                    custom_id="ban_reason",
                    style=disnake.TextInputStyle.paragraph,
                ),
            ]
            super().__init__(title="Выдача бана", components=components)

        async def callback(self, inter: disnake.ModalInteraction):
            участник = self.участник
            def convert_to_seconds(time_str):
                try:
                    value = int(time_str[:-1])  # Получаем числовое значение без последнего символа
                except ValueError:
                    raise ValueError("fxck")

                unit = time_str[-1]

                if unit == 'д' or unit == 'd':
                    return value * 24 * 60 * 60  # Конвертируем дни в секунды
                elif unit == 'ч' or unit == 'h':
                    return value * 60 * 60  # Конвертируем часы в секунды
                elif unit == 'м' or unit == 'm':
                    return value * 60  # Конвертируем минуты в секунды
                elif unit == 'с' or unit == 's':
                    return value  # Секунды остаются без изменений
                else:
                    raise ValueError("fxck")

            if inter.response.is_done():
                return
            try:
                await inter.response.defer()
            except disnake.NotFound:
                return
            value = convert_to_seconds(inter.text_values['ban_duration'])
            причина = inter.text_values['ban_reason']
            if value == 'fxck':
                await inter.send('Произошла ошибка в конвертации.', ephemeral=True)
                return
            role = inter.guild.get_role(1229075137374978119)
            channel = inter.guild.get_channel(1042818334644768871)
            current_timestamp = int(datetime.now().timestamp() + value)
            cur = int(datetime.now().timestamp())

            print(f'{cur} | {current_timestamp} | {value}')

            query = {'id': участник.id, 'guild_id': inter.guild.id}
            update = {'$set': {'ban': 'True', 'Timestamp': current_timestamp,
                               'reason': причина}}  # Что обновляем метод $set т.е. устанавливаем значение

            collbans.update_one(query, update)

            if участник.voice is not None and участник.voice.channel is not None:
                await участник.move_to(None)

            await участник.add_roles(role, reason=причина)

            embed = disnake.Embed(title="ShadowDragons",
                                  url="https://discord.com/invite/KE3psXf",
                                  description="**Модерация**", color=0xff0000)
            embed.set_author(name=f"Участник был заблокирован!")
            embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/d/df/Ukraine_road_sign_3.21.gif")
            embed.add_field(name="Нарушитель:", value=f"{участник.mention}", inline=True)
            embed.add_field(name="Модератор:", value=f"{inter.author.mention}", inline=True)
            embed.add_field(name="Причина:", value=причина, inline=False)
            embed.add_field(name="Истекает через:", value=f"<t:{current_timestamp}:R>", inline=False)
            embed.set_footer(text=f"ID участника: {участник.id} ' • ' {current_datetime}")
            await inter.send(embed=embed)

            embed = disnake.Embed(title="ShadowDragons", url="https://discord.com/invite/KE3psXf",
                                  description="**Модерация**", color=0xff0000)
            embed.set_author(name=f"Вы были заблокированы!")
            embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/d/df/Ukraine_road_sign_3.21.gif")
            embed.add_field(name="", value=f"Вы были забанены на сервере {inter.guild.name}!",
                            inline=False)
            embed.add_field(name="Модератор:", value=f"{inter.author.mention}", inline=False)
            embed.add_field(name="Причина:", value=причина, inline=False)
            embed.add_field(name="Истекает через:", value=f"<t:{current_timestamp}:R>", inline=False)
            embed.set_footer(
                text="Пожалуйста, будьте внимательны!")
            message = await участник.send(embed=embed)

            channel = await self.bot.fetch_channel(944562833901899827)  # Ищем канал по id #логи

            embed = disnake.Embed(title="ShadowDragons", url="https://discord.com/invite/KE3psXf",
                                  description="**Модерация**", color=0xff0000)
            embed.add_field(name="", value=f"Участник {участник.name} ({участник.mention}) был забанен!",
                            inline=False)
            embed.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/d/df/Ukraine_road_sign_3.21.gif")
            embed.add_field(name="Модератор:", value=f"*{inter.author.name}* ({inter.author.mention})", inline=True)
            embed.add_field(name="Канал:", value=f"{inter.channel.mention}", inline=True)
            embed.add_field(name="Время:", value=f"{inter.text_values['ban_duration']} (<t:{current_timestamp}:R>)",
                            inline=True)
            embed.add_field(name="Причина:", value=причина, inline=True)
            embed.set_footer(text=f"ID участника: {участник.id} \' • \' {current_datetime}")
            await channel.send(embed=embed)

    class WarnModal(disnake.ui.Modal):
        def __init__(self):
            components = [
                disnake.ui.TextInput(
                    label="Количество",
                    placeholder="1",
                    custom_id="warn_duration",
                    style=disnake.TextInputStyle.short,
                ),
                disnake.ui.TextInput(
                    label="Причина",
                    placeholder="Причина не указана.",
                    custom_id="warn_reason",
                    style=disnake.TextInputStyle.paragraph,
                ),
            ]
            super().__init__(title="Выдача предупреждений", components=components)

        async def callback(self, inter: disnake.ModalInteraction):
            duration = inter.text_values["ban_duration"]
            reason = inter.text_values["ban_reason"]
            await inter.response.send_message(f'{duration}, {reason}')

    @commands.slash_command(name='action', description='Позволяет взаимодействовать с пользователем.')
    async def action(self, inter: disnake.ApplicationCommandInteraction, участник: disnake.Member):
        date_obj = datetime.fromisoformat(str(участник.created_at))
        self.участник = участник
        # Форматирование даты и времени в нужный формат
        formatted_date = date_obj.strftime("%d.%m.%Y %H:%M:%S")
        embed = disnake.Embed()
        embed.add_field(name='**Информация об участнике:**', value=f'Юзернейм: {участник.name}\n'
                                                                   f'ID участника: {участник.id}\n'
                                                                   f'Дата создания: {formatted_date}', inline=False)
        embed.set_footer(text=участник.name, icon_url=участник.avatar.url)
        await inter.response.send_message(embed=embed, components=[
            disnake.ui.Button(label='Мут', style=disnake.ButtonStyle.success, custom_id='mute'),
            disnake.ui.Button(label='Пред', style=disnake.ButtonStyle.gray, custom_id='warn'),
            disnake.ui.Button(label='Бан', style=disnake.ButtonStyle.danger, custom_id='Ban'),
        ], ephemeral=True)

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        if inter.component.custom_id not in ["mute", "warn", "Ban"]:
            print('close')
            return
        if inter.component.custom_id == 'Ban':
            print('ban')
            await inter.response.send_modal(modal=self.BanModal())
        if inter.component.custom_id == 'warn':
            await inter.response.send_modal(modal=self.WarnModal())


def setup(bot):
    bot.add_cog(ActionCog(bot))
    print("ActionCog is ready")
