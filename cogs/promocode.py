import time
from asyncio import tasks
import disnake
from disnake.ext import commands, tasks
from datetime import datetime, timedelta
from pymongo import MongoClient
from main import rules, get_rule_info  # Список правил
from main import cluster
from ai.process_role import process_role
import random
import string
from .warn import convert_to_seconds, format_duration
from disnake.ui import Button, View

collpromos = cluster.server.promos
collusers = cluster.server.users
collservers = cluster.server.servers

def generate_random_code():
    """Генерирует случайный промокод в формате SD-XXXX-XXXX-XXXX."""
    parts = [
        'SD',  # Первые два символа
        ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)),
        ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)),
        ''.join(random.choices(string.ascii_uppercase + string.digits, k=4)),
    ]
    return '-'.join(parts)

class Promo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name='promocode', description='Взаимодействие с промокодами')
    async def promo(self, inter):
        pass

    @promo.sub_command(name='create-role', description='Создать промокод на роль')
    async def create_role(
            self, inter, роль: disnake.Role, количество: int, длительность: str = None, код: str = None
    ):
        код = код or generate_random_code()  # Генерация промокода, если он не задан
        expires_at = None

        if длительность:
            try:
                expires_at = int(time.time()) + convert_to_seconds(длительность)
            except ValueError as e:
                await inter.response.send_message(f"Ошибка в формате времени: {e}", ephemeral=True)
                return

        # Получаем текущий ID и увеличиваем его
        promo_data = collpromos.find_one_and_update(
            {'_id': inter.guild.id},
            {'$inc': {'counter': 1}},
            upsert=True,
            return_document=True
        )
        promo_id = promo_data.get('counter', 1)

        # Создаем промокод
        collpromos.update_one(
            {'_id': inter.guild.id},
            {'$set': {
                f'promos.{код}': {
                    'id': promo_id,
                    'role_id': роль.id,
                    'type': 'role',
                    'activations': количество,
                    'expires_at': expires_at,
                    'create_id': inter.author.id,
                    'users': []
                }
            }},
            upsert=True
        )

        expiry_message = (
            f", срок действия истекает <t:{expires_at}:R>" if expires_at else ", бессрочный"
        )
        await inter.response.send_message(f'Промокод создан: ``{код}`` с ID: {promo_id}{expiry_message}')

    @promo.sub_command(name='create-rumbicks', description='Создать промокод на румбики')
    async def create_rumbicks(
            self, inter, количество_румбиков: int, количество_активаций: int, длительность: str = None, код: str = None
    ):
        код = код or generate_random_code()  # Генерация промокода, если он не задан
        expires_at = None

        if длительность:
            try:
                expires_at = int(time.time()) + convert_to_seconds(длительность)
            except ValueError as e:
                await inter.response.send_message(f"Ошибка в формате времени: {e}", ephemeral=True)
                return

        # Получаем текущий ID и увеличиваем его
        promo_data = collpromos.find_one_and_update(
            {'_id': inter.guild.id},
            {'$inc': {'counter': 1}},
            upsert=True,
            return_document=True
        )
        promo_id = promo_data.get('counter', 1)

        # Создаем промокод
        collpromos.update_one(
            {'_id': inter.guild.id},
            {'$set': {
                f'promos.{код}': {
                    'id': promo_id,
                    'rumbicks': количество_румбиков,
                    'type': 'rumbicks',
                    'activations': количество_активаций,
                    'expires_at': expires_at,
                    'create_id': inter.author.id,
                    'users': []
                }
            }},
            upsert=True
        )

        expiry_message = (
            f", срок действия истекает <t:{expires_at}:R>" if expires_at else ", бессрочный"
        )
        await inter.response.send_message(f'Промокод создан: ``{код}`` с ID: {promo_id}{expiry_message}')

    @promo.sub_command(name='create-keys', description='Создать промокод на ключи')
    async def create_keys(
            self, inter, количество_ключей: int, количество_активаций: int, длительность: str = None, код: str = None
    ):
        код = код or generate_random_code()  # Генерация промокода, если он не задан
        expires_at = None

        if длительность:
            try:
                expires_at = int(time.time()) + convert_to_seconds(длительность)
            except ValueError as e:
                await inter.response.send_message(f"Ошибка в формате времени: {e}", ephemeral=True)
                return

        # Получаем текущий ID и увеличиваем его
        promo_data = collpromos.find_one_and_update(
            {'_id': inter.guild.id},
            {'$inc': {'counter': 1}},
            upsert=True,
            return_document=True
        )
        promo_id = promo_data.get('counter', 1)

        # Создаем промокод
        collpromos.update_one(
            {'_id': inter.guild.id},
            {'$set': {
                f'promos.{код}': {
                    'id': promo_id,
                    'keys': количество_ключей,
                    'type': 'keys',
                    'activations': количество_активаций,
                    'expires_at': expires_at,
                    'create_id': inter.author.id,
                    'users': []
                }
            }},
            upsert=True
        )

        expiry_message = (
            f", срок действия истекает <t:{expires_at}:R>" if expires_at else ", бессрочный"
        )
        await inter.response.send_message(f'Промокод создан: ``{код}`` с ID: {promo_id}{expiry_message}')
        return код

    @promo.sub_command(name='use', description='Использовать промокод')
    async def use(self, inter, код: str):
        await inter.response.defer(ephemeral=True)
        promo_data = collpromos.find_one(
            {'_id': inter.guild.id, f'promos.{код}': {'$exists': True}}
        )

        if not promo_data:
            await inter.edit_original_response('Кода не существует')
            return

        promo = promo_data['promos'][код]

        # Проверяем срок действия
        if promo.get('expires_at') and promo['expires_at'] < int(time.time()):
            collpromos.update_one(
                {'_id': inter.guild.id},
                {'$unset': {f'promos.{код}': 1}}
            )
            await inter.edit_original_response('Срок действия промокода истёк, он удалён.')
            return

        # Проверяем, активирован ли промокод пользователем
        if inter.author.id in [user['id'] for user in promo['users']]:
            await inter.edit_original_response('Вы уже активировали этот промокод.')
            return

        # Обработка по типу промокода
        if promo['type'] == 'rumbicks':
            collusers.update_one(
                {'id': inter.author.id},
                {'$inc': {'balance': promo['rumbicks']}}
            )
            response = f'Вы получили {promo["rumbicks"]} румбиков.'
        elif promo['type'] == 'keys':
            collusers.update_one(
                {'id': inter.author.id},
                {'$inc': {'keys': promo['keys']}}
            )
            response = f'Вы получили {promo["keys"]} ключей.'
        elif promo['type'] == 'role':
            role = inter.guild.get_role(promo['role_id'])
            await inter.author.add_roles(role)
            response = f'Вам выдана роль {role.name}.'
        else:
            response = 'Неизвестный тип промокода.'

        # Обновляем данные промокода
        collpromos.update_one(
            {'_id': inter.guild.id},
            {
                '$push': {f'promos.{код}.users': {'id': inter.author.id}},
                '$inc': {f'promos.{код}.activations': -1}
            }
        )

        # Удаляем промокод, если активации закончились
        if promo['activations'] - 1 <= 0:
            collpromos.update_one(
                {'_id': inter.guild.id},
                {'$unset': {f'promos.{код}': 1}}
            )

        await inter.edit_original_response(response)

    @promo.sub_command(name="list", description="Список промокодов")
    async def list_promos(self, inter):
        # Получаем все промокоды
        result = collpromos.find_one({'_id': inter.guild.id})
        if not result:
            await inter.response.send_message("Нет активных промокодов.")
            return

        promos = result.get('promos', {})
        promo_list = []
        current_time = int(time.time())  # Текущее время в секундах

        # Перевод типов на русский и сбор информации о промокодах
        for код, данные in promos.items():
            promo_id = данные.get('id', '—')
            creator_id = данные.get('create_id', '—')
            creator = inter.guild.get_member(creator_id)
            creator_mention = creator.mention if creator else f"Неизвестный пользователь (ID: {creator_id})"
            promo_type = данные.get('type', 'Неизвестно').strip()
            activations = данные.get('activations', 0)
            expires_at = данные.get('expires_at')
            expires_text = f"<t:{int(expires_at)}:R>" if expires_at else "Бессрочно"

            # Проверка на истечение срока действия
            if expires_at and current_time > expires_at:
                # Удаление просроченного промокода из базы
                collpromos.update_one(
                    {'_id': inter.guild.id},
                    {'$unset': {f'promos.{код}': 1}}
                )
                continue  # Переходим к следующему промокоду

            # Перевод типа на русский
            if promo_type == 'rumbicks':
                promo_type_ru = "Румбики"
                capacity = f"{данные.get('rumbicks', 0)} румбиков"
            elif promo_type == 'keys':
                promo_type_ru = "Ключи"
                capacity = f"{данные.get('keys', 0)} ключей"
            elif promo_type == 'role':
                promo_type_ru = "Роль"
                role_id = данные.get('role_id')
                role = inter.guild.get_role(role_id)
                role_name = role.name if role else 'Неизвестная роль'
                duration = данные.get('on_time', 0)
                capacity = f"Роль: {role_name} на {duration} минут"
            else:
                promo_type_ru = "Неизвестный тип"
                capacity = "Неизвестно"

            # Получение списка пользователей, которые активировали промокод
            users = данные.get('users', [])
            activated_by = (
                ", ".join(
                    inter.guild.get_member(user['id']).mention if inter.guild.get_member(
                        user['id']) else f"Неизвестный (ID: {user['id']})"
                    for user in users
                )
                if users
                else "Никто"
            )

            promo_list.append({
                'код': код,
                'promo_id': promo_id,
                'promo_type': promo_type_ru,
                'activations': activations,
                'creator_mention': creator_mention,
                'expires_text': expires_text,
                'capacity': capacity,
                'activated_by': activated_by
            })

        # Если нет активных промокодов
        if not promo_list:
            await inter.response.send_message("Нет активных промокодов.")
            return

        # Формируем вывод в одном эмбеде
        embed = disnake.Embed(title="Список промокодов")
        for promo in promo_list[:5]:  # Выводим первые 5 промокодов
            embed.add_field(
                name=f"Промокод: {promo['код']} (ID: {promo['promo_id']})",
                value=f"**Тип:** {promo['promo_type']}\n"
                      f"**Вместимость:** {promo['capacity']}\n"
                      f"**Создатель:** {promo['creator_mention']}\n"
                      f"**Активирован:** {promo['activated_by']}\n"
                      f"**Окончание действия:** {promo['expires_text']}\n"
                      f"**Оставшиеся активации:** {promo['activations']}",
                inline=False
            )

        # Если промокодов больше 5, добавляем кнопки для переключения страниц
        if len(promo_list) > 5:
            current_page = 1
            total_pages = (len(promo_list) // 5) + (1 if len(promo_list) % 5 != 0 else 0)

            view = View()

            # Кнопки для переключения страниц
            async def update_page(interaction: disnake.MessageInteraction):
                nonlocal current_page

                if interaction.component.custom_id == "next_page" and current_page < total_pages:
                    current_page += 1
                elif interaction.component.custom_id == "prev_page" and current_page > 1:
                    current_page -= 1

                embed = disnake.Embed(title="Список промокодов")
                start_index = (current_page - 1) * 5
                end_index = start_index + 5
                for promo in promo_list[start_index:end_index]:
                    embed.add_field(
                        name=f"Промокод: {promo['код']} (ID: {promo['promo_id']})",
                        value=f"**Тип:** {promo['promo_type']}\n"
                              f"**Вместимость:** {promo['capacity']}\n"
                              f"**Создатель:** {promo['creator_mention']}\n"
                              f"**Активирован:** {promo['activated_by']}\n"
                              f"**Окончание действия:** {promo['expires_text']}\n"
                              f"**Оставшиеся активации:** {promo['activations']}",
                        inline=False
                    )

                await interaction.response.edit_message(embed=embed, view=view)

            next_button = Button(label="Вперед →", custom_id="next_page")
            prev_button = Button(label="← Назад", custom_id="prev_page")

            next_button.callback = update_page
            prev_button.callback = update_page

            view.add_item(prev_button)
            view.add_item(next_button)

            await inter.response.send_message(embed=embed, view=view)
        else:
            await inter.response.send_message(embed=embed)

    @promo.sub_command(name="delete", description="Удалить промокод по ID или коду")
    async def delete_promocode(self, inter, promo_id: str = None, promo_code: str = None):
        if not promo_id and not promo_code:
            await inter.response.send_message("Укажите ID или код промокода для удаления.")
            return

        result = collpromos.find_one({'_id': inter.guild.id})
        if not result:
            await inter.response.send_message("Нет активных промокодов.")
            return

        promos = result.get('promos', {})
        promo_to_delete = None

        # Удаление по ID
        if promo_id:
            for code, data in promos.items():
                if str(data.get('id')) == promo_id:  # Преобразуем ID в строку, если это необходимо
                    promo_to_delete = code
                    break

        # Удаление по коду
        if promo_code and promo_to_delete is None:
            if promo_code in promos:
                promo_to_delete = promo_code

        if promo_to_delete:
            # Удаление промокода
            collpromos.update_one(
                {'_id': inter.guild.id},
                {'$unset': {f'promos.{promo_to_delete}': 1}}
            )
            await inter.response.send_message(f"Промокод с кодом `{promo_to_delete}` был удален.")
        else:
            await inter.response.send_message("Промокод с таким ID или кодом не найден.")
def setup(bot):
    bot.add_cog(Promo(bot))
    print("PromoCog is ready")
