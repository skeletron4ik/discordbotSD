import disnake
from disnake import Permissions
from pymongo import MongoClient, errors, collection
from disnake.ext import commands, tasks
from datetime import datetime, timedelta, timezone
import os
import asyncio
import time
import random
import math
import re

from setuptools.command.egg_info import overwrite_arg

from main import cluster, bot
from main import rules, get_rule_info, check_roles, ROLE_CATEGORIES
from ai.promo import create_rumbicks
from ai.process_role import process_role
from disnake.ui import Button, View, Select

collusers = cluster.server.users
collservers = cluster.server.servers
collpromos = cluster.server.promos
collreports = cluster.server.reports


class ReportCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.rules = rules

    def get_rule_info(self, причина):
        if причина in self.rules:
            reason = self.rules[str(причина)]
            return reason
        else:
            reason = причина
            return reason

    class AcceptVerdictModal(disnake.ui.Modal):
        def __init__(self, report_id: int, suspect: disnake.Member, sender: disnake.Member, cog):
            self.report_id = report_id
            self.suspect = suspect
            self.sender = sender
            self.cog = cog
            super().__init__(
                title="Принятие жалобы",
                custom_id="accept",
                components=[
                    disnake.ui.TextInput(
                        label="Вердикт",
                        custom_id="verdict",
                        style=disnake.TextInputStyle.paragraph,
                        required=True,
                        value="Жалоба принята.",
                        max_length=300,
                        placeholder="Введите ваш вердикт для участника."
                    )
                ]
            )

        async def callback(self, inter: disnake.ModalInteraction):
            verdict = inter.text_values["verdict"]

            # Обновление в базе данных
            collreports.update_one(
                {'_id': inter.guild.id, f'reports.{self.suspect.id}_{self.report_id}.id': self.report_id},
                {'$set': {
                    f'reports.{self.suspect.id}_{self.report_id}.status': 'accepted',
                    f'reports.{self.suspect.id}_{self.report_id}.moder_id': inter.author.id,
                    f'reports.{self.suspect.id}_{self.report_id}.close_reason': verdict,
                    f'reports.{self.suspect.id}_{self.report_id}.close_timestamp': int(datetime.now().timestamp())
                }}
            )

            # Отправка вердикта отправителю жалобы в ЛС
            try:
                embed = disnake.Embed(
                    title="Жалоба принята!",
                    description=(
                        f"Ваша жалоба на участника {self.suspect.mention} была **принята** модератором {inter.author.mention}, нарушитель **наказан**.\n"
                        f"**Вердикт:** ```{verdict}```"
                    ),
                    color=0x00ff00,
                    timestamp=datetime.now()
                )
                embed.set_thumbnail(url='https://www.emojiall.com/images/240/telegram/2705.gif')
                embed.set_footer(text=f"Репорт: #{self.report_id}")
                await self.sender.send(embed=embed)
            except disnake.Forbidden:
                embed = disnake.Embed(title='Вы успешно приняли жалобу!', description=f'Вы успешно обработали жалобу, однако уведомление отправителю не было доставлено из-за настроек конфиденциальности, которые запрещают получение таких сообщений.\n Не забудьте выдать наказание нарушителю!', color=0x00ffff)
                embed.set_footer(text=f'Репорт: #{self.report_id}')
                embed.set_thumbnail(url='https://www.emojiall.com/images/240/telegram/2705.gif')
                await inter.response.send_message(embed=embed, ephemeral=True)
                return
            embed = disnake.Embed(title='Вы успешно приняли жалобу!',
                                  description=f'Вы успешно обработали жалобу, отправитель был уведомлён об этом.\n Не забудьте выдать наказание нарушителю!',
                                  color=0x00ff00)
            embed.set_footer(text=f'Репорт: #{self.report_id}')
            embed.set_thumbnail(url='https://www.emojiall.com/images/240/telegram/2705.gif')
            await inter.response.send_message(embed=embed, ephemeral=True)

            # Удаляем кнопки после обработки жалобы
            message = inter.message
            await message.edit(view=None)  # Удаляем View (с кнопками)
            # Обновление сообщения с репортом в модераторском канале
            report_message = await inter.channel.fetch_message(inter.message.id)
            embed = report_message.embeds[0]
            embed.title = "Жалоба принята!"
            embed.add_field(name='', value='-=-=-=-=-=-=-=-=-=-=-=-=-=-')
            embed.add_field(name="", value=f"Жалоба была принята модератором {inter.author.mention},\n **Вердикт:**```{verdict}```", inline=False)
            embed.set_thumbnail(url='https://www.emojiall.com/images/240/telegram/2705.gif')
            embed.color = 0x00ff00  # Изменение цвета на зелёный
            await report_message.channel.send(embed=embed)
            thread = inter.message.thread
            forum = inter.guild.get_channel(1336377188173484052)
            opened = forum.get_tag(1336380883917213791)
            closed = forum.get_tag(1336380395113152583)
            await thread.edit(applied_tags=[closed], locked=True)

    class RejectVerdictModal(disnake.ui.Modal):
        def __init__(self, report_id: int, suspect: disnake.Member, sender: disnake.Member, cog):
            self.report_id = report_id
            self.suspect = suspect
            self.sender = sender  # Отправитель жалобы
            self.cog = cog
            super().__init__(
                title="Отклонение жалобы",
                custom_id="reject",
                components=[
                    disnake.ui.TextInput(
                        label="Вердикт",
                        custom_id="verdict",
                        style=disnake.TextInputStyle.paragraph,
                        required=True,
                        value="Жалоба отклонена.",
                        max_length=300,
                        placeholder="Введите ваш вердикт для участника."
                    )
                ]
            )

        async def callback(self, inter: disnake.ModalInteraction):
            verdict = inter.text_values["verdict"]

            # Обновление в базе данных
            collreports.update_one(
                {'_id': inter.guild.id, f'reports.{self.suspect.id}_{self.report_id}.id': self.report_id},
                {'$set': {
                    f'reports.{self.suspect.id}_{self.report_id}.status': 'rejected',
                    f'reports.{self.suspect.id}_{self.report_id}.moder_id': inter.author.id,
                    f'reports.{self.suspect.id}_{self.report_id}.close_reason': verdict,
                    f'reports.{self.suspect.id}_{self.report_id}.close_timestamp': int(datetime.now().timestamp())
                }}
            )

            # Отправка вердикта отправителю жалобы в ЛС
            try:
                embed = disnake.Embed(
                    title="Жалоба отклонена!",
                    description=(
                        f"Ваша жалоба на участника {self.suspect.mention} была **отклонена** модератором {inter.author.mention}.\n"
                        f"**Вердикт:** ```{verdict}```"
                    ),
                    color=0xff0000,
                    timestamp=datetime.now()
                )
                embed.set_thumbnail(url='https://media2.giphy.com/media/AkGPEj9G5tfKO3QW0r/200.gif')
                embed.set_footer(text=f"Репорт: #{self.report_id}")
                await self.sender.send(embed=embed)
            except disnake.Forbidden:
                embed = disnake.Embed(title='Вы успешно отклонили жалобу!',
                                      description=f'Вы успешно обработали жалобу, однако уведомление отправителю не было доставлено из-за настроек конфиденциальности, которые запрещают получение таких сообщений.',
                                      color=0x00ffff)
                embed.set_footer(text=f'Репорт: #{self.report_id}')
                embed.set_thumbnail(url='https://media2.giphy.com/media/AkGPEj9G5tfKO3QW0r/200.gif')
                await inter.response.send_message(embed=embed, ephemeral=True)
                return
            embed = disnake.Embed(title='Вы успешно отклонили жалобу!',
                                  description=f'Вы успешно обработали жалобу, отправитель был уведомлён об этом.\n',
                                  color=0x00ff00)
            embed.set_footer(text=f'Репорт: #{self.report_id}')
            embed.set_thumbnail(url='https://www.emojiall.com/images/240/telegram/2705.gif')
            await inter.response.send_message(embed=embed, ephemeral=True)

            # Удаляем кнопки после обработки жалобы
            message = inter.message
            await message.edit(view=None)  # Удаляем View (с кнопками)
            # Обновление сообщения с репортом в модераторском канале
            report_message = await inter.channel.fetch_message(inter.message.id)
            embed = report_message.embeds[0]
            embed.title = "Жалоба принята!"
            embed.add_field(name="Вердикт", value=verdict, inline=False)
            embed.add_field(name="Модератор", value=inter.author.mention, inline=False)
            embed.color = disnake.Color.red()  # Изменение цвета на красный
            await report_message.channel.send(embed=embed)
            thread = inter.message.thread
            forum = inter.guild.get_channel(1336377188173484052)
            opened = forum.get_tag(1336380883917213791)
            closed = forum.get_tag(1336380395113152583)
            await thread.edit(applied_tags=[closed], locked=True)

    class ReportView(disnake.ui.View):
        def __init__(self, cog, report_id: int, suspect: disnake.Member, sender: disnake.Member):
            super().__init__(timeout=None)
            self.cog = cog
            self.report_id = report_id
            self.suspect = suspect
            self.sender = sender  # Отправитель жалобы

        @disnake.ui.button(label="✔️ Принять", style=disnake.ButtonStyle.green, custom_id="accept_report")
        async def accept_report(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
            modal = self.cog.AcceptVerdictModal(self.report_id, self.suspect, self.sender, self.cog)
            await inter.response.send_modal(modal)

        @disnake.ui.button(label="❌ Отклонить", style=disnake.ButtonStyle.red, custom_id="reject_report")
        async def reject_report(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
            modal = self.cog.RejectVerdictModal(self.report_id, self.suspect, self.sender, self.cog)
            await inter.response.send_modal(modal)

    class ReportModal(disnake.ui.Modal):
        def __init__(self, cog, inter: disnake.ApplicationCommandInteraction, suspect: disnake.Member):
            self.cog = cog
            self.inter = inter
            self.suspect = suspect
            super().__init__(
                title="Жалоба на участника/модератора",
                custom_id="report_modal",
                components=[
                    disnake.ui.TextInput(
                        label="Причина",
                        custom_id="reason",
                        style=disnake.TextInputStyle.short,
                        required=True,
                        min_length=3,
                        max_length=50,
                        placeholder="Укажите номер причины (например: 2.2) или свою."
                    ),
                    disnake.ui.TextInput(
                        label="Доказательства",
                        custom_id="proof",
                        style=disnake.TextInputStyle.paragraph,
                        required=False,
                        max_length=250,
                        placeholder="Если жалоба связана с недавними нарушениями в чате, оставьте это поле пустым."
                    ),
                    disnake.ui.TextInput(
                        label="Дополнительная информация",
                        custom_id="additional_info",
                        style=disnake.TextInputStyle.paragraph,
                        required=False,
                        max_length=500,
                        placeholder="Описание ситуации (необязательно)."
                    )
                ]
            )

        async def callback(self, inter: disnake.ModalInteraction):
            причина = inter.text_values["reason"]
            доказательства = inter.text_values["proof"]
            дополнительная_информация = inter.text_values.get("additional_info")

            await inter.response.defer(ephemeral=True)

            # Отправка жалобы в канал модерации
            report_channel_id = 1336377188173484052
            report_channel = self.cog.bot.get_channel(report_channel_id)
            if not report_channel:
                await inter.response.send_message(
                    "Канал для жалоб не найден. Обратитесь к администратору.", ephemeral=True
                )
                return

            reason = self.cog.get_rule_info(причина)
            report_data = collreports.find_one_and_update(
                {'_id': inter.guild.id},
                {'$inc': {'counter': 1}},
                upsert=True,
                return_document=True
            )
            report_id = report_data.get('counter', 1)

            # Условие для сбора последних сообщений участника
            messages = []
            if not доказательства:  # Если поле доказательств пустое
                one_day_ago = datetime.now(timezone.utc) - timedelta(days=1)  # Время суток назад с учётом временной зоны
                for channel in inter.guild.text_channels:  # Перебираем текстовые каналы
                    async for msg in channel.history(limit=100):  # Загружаем до 100 сообщений из каждого канала
                        if msg.author.id == self.suspect.id and msg.created_at >= one_day_ago:  # Проверяем ID автора и время сообщения
                            messages.append({
                                'content': msg.content,
                                'jump_url': msg.jump_url,  # Добавляем ссылку на сообщение
                                'timestamp': msg.created_at.timestamp()  # Сохраняем дату как timestamp
                            })
                        if len(messages) >= 20:  # Останавливаем сбор после 20 сообщений
                            break
                    if len(messages) >= 20:
                        break

            # Список ролей категории staff
            staff_roles = [518505773022838797, 580790278697254913, 702593498901381184, 1229337640839413813]

            # Проверка, имеет ли участник роль из категории staff
            is_staff = any(role.id in staff_roles for role in self.suspect.roles)

            # Определение типа жалобы
            report_type = 'staff' if is_staff else 'member'
            moder_role = inter.guild.get_role(518505773022838797) if is_staff else inter.guild.get_role(580790278697254913)
            moder_role2 = inter.guild.get_role(518505773022838797) if is_staff else inter.guild.get_role(702593498901381184)

            # Сохранение жалобы в базе данных
            collreports.update_one(
                {'_id': inter.guild.id},
                {'$set': {
                    f'reports.{self.suspect.id}_{report_id}': {
                        'id': report_id,
                        'status': 'open',
                        'type': report_type,
                        'suspect_id': self.suspect.id,
                        'sender_id': inter.author.id,
                        'date_timestamp': int(datetime.now().timestamp()),
                        'reason': reason,
                        'proof': доказательства,
                        'info': дополнительная_информация,
                        'moder_id': None,
                        'close_reason': None,
                        'close_timestamp': None,
                        'messages': messages
                    }
                }},
                upsert=True
            )
            await inter.followup.send("Вы успешно отправили жалобу", ephemeral=True)

            # Формирование Embed
            embed = disnake.Embed(
                title="Новая жалоба!",
                color=0x00ffff,
                timestamp=datetime.now()
            )
            embed.set_thumbnail(url='https://cdn.pixabay.com/animation/2023/06/13/15/13/15-13-39-266_512.gif')
            embed.add_field(name="Нарушитель:", value=self.suspect.mention, inline=True)
            embed.add_field(name="Отправитель:", value=inter.author.mention, inline=True)
            embed.add_field(name="Причина:", value=reason, inline=False)
            embed.add_field(name="Доказательства:", value=доказательства or "Не предоставлены", inline=False)

            if дополнительная_информация:
                embed.add_field(name="Дополнительная информация:", value=дополнительная_информация, inline=False)

            if not доказательства and messages:
                messages.reverse()
                message_texts = [
                    f"[<t:{int(msg['timestamp'])}:T>] [{self.suspect.display_name}]({msg['jump_url']}): {msg['content']}"
                    for msg in messages
                ]
                all_messages = "\n".join(message_texts)

                for i in range(0, len(all_messages), 1024):
                    embed.add_field(
                        name="Последние сообщения участника:" if i == 0 else "",
                        value=all_messages[i:i + 1024],
                        inline=False
                    )

            embed.set_footer(text=f"Репорт: #{report_id}", icon_url=inter.guild.icon.url)
            view = self.cog.ReportView(self.cog, report_id, self.suspect, inter.author)
            forum = inter.guild.get_channel(1336377188173484052)
            tag = forum.get_tag(1336380883917213791)
            if is_staff:
                type = forum.get_tag(1336380503640637551)
            else:
                type = forum.get_tag(1336380451954102432)
            if is_staff:
                thread = await forum.create_thread(name=f'Репорт №: {report_id}', applied_tags=[tag, type], view=view, reason=f'Репорт №: {report_id}', embed=embed, content=moder_role.mention)
            else:
                thread = await forum.create_thread(name=f'Репорт №: {report_id}', applied_tags=[tag, type], view=view,
                                          reason=f'Репорт №: {report_id}', embed=embed, content=f'{moder_role.mention}, {moder_role2.mention}')
    @commands.slash_command(name='report', description='Взаимодействие с репортами', contexts=disnake.InteractionContextTypes(guild=True, bot_dm=False, private_channel=False))
    @commands.cooldown(rate=1, per=15, type=commands.BucketType.user)
    async def report(self, inter):
        pass
    @report.sub_command(name='user', description="Отправить жалобу на участника")
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.user)
    async def report_user(self, inter: disnake.ApplicationCommandInteraction, участник: disnake.Member):
        modal = self.ReportModal(self, inter, участник)
        if участник == inter.author:
            await inter.response.send_message('Нельзя отправить жалобу на себя.', ephemeral=True)
            return
        await inter.response.send_modal(modal)

    @report.sub_command(name="list", description="Список репортов")
    @commands.cooldown(rate=1, per=15, type=commands.BucketType.user)
    @check_roles("admin")
    async def list_reports(self, inter):
        # Получаем все репорты
        result = collreports.find_one({'_id': inter.guild.id})
        if not result or not result.get('reports'):
            await inter.response.send_message("Нет активных репортов.")
            return

        reports = result['reports']

        # Функция для фильтрации и формирования списка репортов
        def filter_and_sort_reports(filter_status=None):
            filtered_reports = []
            for report_key, данные in reports.items():
                report_id = данные.get('id', '—')
                status = данные.get('status', '—')
                report_type = данные.get('type', '—').strip()
                suspect_id = данные.get('suspect_id', '—')
                sender_id = данные.get('sender_id', '—')
                date_timestamp = данные.get('date_timestamp', '—')
                moder_id = данные.get('moder_id')
                close_timestamp = данные.get('close_timestamp')
                close_reason = данные.get('close_reason')
                reason = данные.get('reason')

                # Проверяем статус для фильтрации
                if filter_status and status != filter_status:
                    continue

                # Получаем участников и ссылки на них
                suspect = inter.guild.get_member(suspect_id)
                suspect_mention = suspect.mention if suspect else f"Неизвестный пользователь (ID: {suspect_id})"
                sender = inter.guild.get_member(sender_id)
                sender_mention = sender.mention if sender else f"Неизвестный пользователь (ID: {sender_id})"
                moderator = inter.guild.get_member(moder_id) if moder_id else None
                moderator_mention = moderator.mention if moderator else "—"

                # Формируем текст и эмодзи для статуса
                if status == 'accepted':
                    status_text = f"Принял {moderator_mention} в <t:{int(close_timestamp)}:f>\n **Вердикт:** ``{close_reason}``"
                    emoji = "🟢"
                elif status == 'rejected':
                    status_text = f"Отклонил {moderator_mention} в <t:{int(close_timestamp)}:f>\n **Вердикт:** ``{close_reason}``"
                    emoji = "🔴"
                else:
                    status_text = "Открыт"
                    emoji = "🟦"

                # Добавляем в список
                filtered_reports.append({
                    'id': f"{emoji} Репорт: #{report_id}",
                    'status': status_text,
                    'type': report_type,
                    'suspect': suspect_mention,
                    'sender': sender_mention,
                    'date': f"<t:{int(date_timestamp)}:f>",
                    'reason': reason,
                    'timestamp': date_timestamp
                })

            # Сортируем репорты в обратном порядке
            return sorted(filtered_reports, key=lambda x: x['timestamp'], reverse=True)

        # Функция для создания эмбеда
        def create_embed(filtered_reports, page, total_pages):
            embed = disnake.Embed(title="Список репортов", color=0xff0000, timestamp=datetime.now())
            embed.set_thumbnail(url='https://cdn.pixabay.com/animation/2023/06/13/15/13/15-13-39-266_512.gif')
            embed.set_footer(text=f"Страница {page}/{total_pages}", icon_url=inter.guild.icon.url)

            start_index = (page - 1) * 5
            end_index = start_index + 5
            for report in filtered_reports[start_index:end_index]:
                embed.add_field(
                    name=f"{report['id']}\n",
                    value=f"**Тип:** {report['type']}\n"
                          f"**Нарушитель:** {report['suspect']}\n"
                          f"**Отправитель:** {report['sender']}\n"
                          f"**Дата:** {report['date']}\n"
                          f"**Причина:** {report['reason']}\n"
                          f"**Статус:** {report['status']}\n",
                    inline=False
                )
            return embed

        # Начальный фильтр (показываем все)
        current_filter = None
        report_list = filter_and_sort_reports(current_filter)
        current_page = 1
        total_pages = (len(report_list) // 5) + (1 if len(report_list) % 5 != 0 else 0)

        # Создаем выпадающий список
        select = Select(
            placeholder="Выберите тип репортов",
            options=[
                disnake.SelectOption(label="Все", value="all", emoji="📋"),
                disnake.SelectOption(label="Открытые", value="open", emoji="🟦"),
                disnake.SelectOption(label="Принятые", value="accepted", emoji="🟢"),
                disnake.SelectOption(label="Отклонённые", value="rejected", emoji="🔴"),
            ]
        )

        # Callback для изменения фильтра
        async def select_callback(interaction: disnake.MessageInteraction):
            nonlocal current_filter, report_list, current_page, total_pages

            selected_value = interaction.data['values'][0]
            current_filter = None if selected_value == "all" else selected_value
            report_list = filter_and_sort_reports(current_filter)
            current_page = 1
            total_pages = (len(report_list) // 5) + (1 if len(report_list) % 5 != 0 else 0)

            embed = create_embed(report_list, current_page, total_pages)
            await interaction.response.edit_message(embed=embed, view=view)

        select.callback = select_callback

        # Кнопки для переключения страниц
        async def update_page(interaction: disnake.MessageInteraction):
            nonlocal current_page

            if interaction.component.custom_id == "next_page" and current_page < total_pages:
                current_page += 1
            elif interaction.component.custom_id == "prev_page" and current_page > 1:
                current_page -= 1

            embed = create_embed(report_list, current_page, total_pages)
            await interaction.response.edit_message(embed=embed, view=view)

        next_button = Button(label="Вперед ➡️", custom_id="next_page", style=disnake.ButtonStyle.secondary)
        prev_button = Button(label="⬅️ Назад", custom_id="prev_page", style=disnake.ButtonStyle.secondary)

        next_button.callback = update_page
        prev_button.callback = update_page

        # Добавляем элементы в View
        view = View()
        view.add_item(select)
        if len(report_list) > 5:
            view.add_item(prev_button)
            view.add_item(next_button)

        # Отправляем сообщение
        embed = create_embed(report_list, current_page, total_pages)
        await inter.response.send_message(embed=embed, view=view, ephemeral=True)


def setup(bot):
    bot.add_cog(ReportCog(bot))
    print("ReportCog is ready")
