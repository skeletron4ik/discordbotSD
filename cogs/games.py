import disnake
from pymongo import MongoClient, errors, collection
from disnake.ext import commands, tasks
from datetime import datetime, timedelta
import os
import asyncio
import time
import random
import math
import re
from main import cluster

collusers = cluster.server.users
collservers = cluster.server.servers

emoji = "<a:rumbick_gif:1276856664842047518>"

def format_rubick_text(value):
    if value == 1:
        return "1 румбик"
    elif 2 <= value <= 4:
        return f"`{value}` румбика"
    else:
        return f"`{value}` румбиков"
def format_rumbick(value):
    emoji = "<:rumbick:1271089081601753118>"
    return f"{value} {emoji}"

def create_error_embed(message: str) -> disnake.Embed:
    embed = disnake.Embed(color=0xff0000, timestamp=datetime.now())
    embed.add_field(name='Произошла ошибка', value=f'Ошибка: {message}')
    embed.set_thumbnail(url="https://cdn.pixabay.com/animation/2022/12/26/19/45/19-45-56-484__480.png")
    embed.set_footer(text='Ошибка')
    return embed

class GamesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_modal_submit(self, inter: disnake.ModalInteraction):
        if inter.custom_id == "knb":
            figure = inter.text_values['figurez']
            decline = disnake.utils.get(inter.author.guild.emojis, name='773229388573310996')
            challenge_user_id = inter.text_values.get('challenge_user_id')
            challenged_user = inter.guild.get_member(int(challenge_user_id)) if challenge_user_id else None

            if figure in ['К', 'Н', 'Б']:
                bet = inter.text_values['bet']
                await inter.response.defer(with_message=True)
                message = await inter.followup.send('В процессе..')

                balance = collusers.find_one({'id': inter.author.id})['balance']
                cost = int(bet)
                bet = format_rumbick(cost)
                author = inter.author

                if cost < 10:
                    error_message = f"{decline}  `{inter.author.display_name}`, Вы можете поставить менее **10** румбиков."
                    embed = create_error_embed(error_message)
                    await message.edit(content=None, embed=embed)
                    return

                if balance < cost:
                    err = format_rumbick(cost - balance)
                    error_message = f"{decline}  `{inter.author.display_name}`, Вам не хватает {err}."
                    embed = create_error_embed(error_message)
                    await message.edit(content=None, embed=embed)
                    return

                collusers.find_one_and_update({'id': inter.author.id}, {'$inc': {'balance': -cost}})

                embed = disnake.Embed(title='Камень-Ножницы-Бумага', color=0xff00fa, timestamp=datetime.now())
                embed.set_thumbnail(
                    url='https://media0.giphy.com/media/JoDQSE8d1tB2tsPAAg/200w.gif?cid=6c09b952xijiedj0le1rvko2nmee3rri4fzrvchqb4q7as94&ep=v1_gifs_search&rid=200w.gif&ct=g')
                embed.set_author(name=inter.author.display_name, icon_url=inter.author.avatar.url)
                embed.set_footer(text=f'Rock-Paper-Scissors', icon_url=inter.guild.icon.url)
                embed.add_field(name='', value=f'**Ставка:** {bet}', inline=True)

                if challenged_user:
                    embed.add_field(name='Вызов брошен:', value=f'Только для: {challenged_user.mention}', inline=False)
                else:
                    embed.add_field(name='Вызов брошен:', value='Для всех участников', inline=False)

                async def button_callback(interaction: disnake.MessageInteraction, choice: str, embed: disnake.Embed):
                    if challenged_user and interaction.author.id != challenged_user.id:
                        error_message = f"{decline} `{interaction.author.display_name}`, Вы не можете участвовать в этой игре."
                        embed = create_error_embed(error_message)
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return

                    if author.id == interaction.author.id:
                        error_message = f"{decline} `{interaction.author.display_name}`, Вы не можете играть сами с собой."
                        embed = create_error_embed(error_message)
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return

                    balance_interaction = collusers.find_one({'id': interaction.author.id})['balance']
                    if balance_interaction < cost:
                        err = format_rumbick(cost - balance_interaction)
                        error_message = f"{decline} `{interaction.author.display_name}`, Вам не хватает {err}."
                        embed = create_error_embed(error_message)
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return

                    collusers.find_one_and_update({'id': interaction.author.id}, {'$inc': {'balance': -cost}})

                    if choice == "Камень":  # Камень
                        if figure == 'К':
                            embed.add_field(name='**Итоги:**',
                                            value=f'Выбор у двух участников пал на камень, поэтому ничья.\n'
                                                  f'Ставки возвращаются участникам.', inline=False)
                            collusers.find_one_and_update({'id': interaction.author.id}, {'$inc': {'balance': cost}})
                            collusers.find_one_and_update({'id': author.id}, {'$inc': {'balance': cost}})
                        elif figure == 'Б':
                            embed.add_field(name='**Итоги:**',
                                            value=f'{author.mention} выбрал бумагу, а {interaction.author.mention} выбрал камень.\n'
                                                  f'{author.display_name} получает выигрыш.', inline=False)
                            collusers.find_one_and_update({'id': author.id}, {'$inc': {'balance': cost * 2}})
                        elif figure == 'Н':
                            embed.add_field(name='**Итоги:**',
                                            value=f'{interaction.author.mention} выбрал камень, а {author.mention} выбрал ножницы.\n'
                                                  f'{interaction.author.display_name} получает выигрыш.', inline=False)
                            collusers.find_one_and_update({'id': interaction.author.id},
                                                          {'$inc': {'balance': cost * 2}})

                    elif choice == "Бумага":  # Бумага
                        if figure == 'К':
                            embed.add_field(name='**Итоги:**',
                                            value=f'{author.mention} выбрал камень, а {interaction.author.mention} выбрал бумагу.\n'
                                                  f'{interaction.author.display_name} получает выигрыш.', inline=False)
                            collusers.find_one_and_update({'id': interaction.author.id},
                                                          {'$inc': {'balance': cost * 2}})
                        elif figure == 'Б':
                            embed.add_field(name='**Итоги:**',
                                            value=f'Выбор у двух участников пал на бумагу, поэтому ничья.\n'
                                                  f'Ставки возвращаются участникам.', inline=False)
                            collusers.find_one_and_update({'id': interaction.author.id}, {'$inc': {'balance': cost}})
                            collusers.find_one_and_update({'id': author.id}, {'$inc': {'balance': cost}})
                        elif figure == 'Н':
                            embed.add_field(name='**Итоги:**',
                                            value=f'{author.mention} выбрал ножницы, а {interaction.author.mention} выбрал бумагу.\n'
                                                  f'{author.display_name} получает выигрыш.', inline=False)
                            collusers.find_one_and_update({'id': author.id}, {'$inc': {'balance': cost * 2}})

                    elif choice == "Ножницы":  # Ножницы
                        if figure == 'К':
                            embed.add_field(name='**Итоги:**',
                                            value=f'{author.mention} выбрал камень, а {interaction.author.mention} выбрал ножницы.\n'
                                                  f'{author.display_name} получает выигрыш.', inline=False)
                            collusers.find_one_and_update({'id': author.id}, {'$inc': {'balance': cost * 2}})
                        elif figure == 'Б':
                            embed.add_field(name='**Итоги:**',
                                            value=f'{interaction.author.mention} выбрал ножницы, а {author.mention} выбрал бумагу.\n'
                                                  f'{interaction.author.display_name} получает выигрыш.', inline=False)
                            collusers.find_one_and_update({'id': interaction.author.id},
                                                          {'$inc': {'balance': cost * 2}})
                        elif figure == 'Н':
                            embed.add_field(name='**Итоги:**',
                                            value=f'Выбор у двух участников пал на ножницы, поэтому ничья.\n'
                                                  f'Ставки возвращаются участникам.', inline=False)
                            collusers.find_one_and_update({'id': interaction.author.id}, {'$inc': {'balance': cost}})
                            collusers.find_one_and_update({'id': author.id}, {'$inc': {'balance': cost}})


                    await inter.edit_original_response(embed=embed, view=None)

                button_rock = disnake.ui.Button(label="🗿 Камень", style=disnake.ButtonStyle.primary)
                button_paper = disnake.ui.Button(label="📃 Бумага", style=disnake.ButtonStyle.primary)
                button_scissors = disnake.ui.Button(label="✂️ Ножницы", style=disnake.ButtonStyle.primary)

                # Передаем embed при вызове button_callback
                button_rock.callback = lambda i: button_callback(i, "Камень", embed)
                button_paper.callback = lambda i: button_callback(i, "Бумага", embed)
                button_scissors.callback = lambda i: button_callback(i, "Ножницы", embed)

                # Create a view with a timeout of 5 minutes
                view = disnake.ui.View(timeout=300)
                view.add_item(button_rock)
                view.add_item(button_paper)
                view.add_item(button_scissors)

                async def on_timeout():
                    # Add a new field to the existing embed
                    embed.add_field(name="Игра отменена",
                                    value="Никто не принял вызов в течение 5 минут.\n **Ставка возвращена**.",
                                    inline=False)
                    view.clear_items()  # Remove all buttons
                    await message.edit(embed=embed, view=view)
                    collusers.find_one_and_update({'id': inter.author.id}, {'$inc': {'balance': cost}})

                view.on_timeout = on_timeout

                await message.edit(embed=embed, view=view, content=None)

            else:
                error_message = f"{decline} `{inter.author.display_name}`, Вы выбрали несуществующий ход."
                embed = create_error_embed(error_message)
                await inter.response.send_message(embed=embed, ephemeral=True)

    @commands.slash_command(name='rps', description='Популярная игра, камень-ножницы-бумага')
    async def rps(self, inter: disnake.ApplicationCommandInteraction):
        components = disnake.ui.TextInput(
            label=f"Выбери свой ход:",
            custom_id="figurez",
            style=disnake.TextInputStyle.short,
            placeholder="К - камень, Н - ножницы, Б - бумага",
            required=True,
            min_length=1,
            max_length=1,
        )

        betz = disnake.ui.TextInput(
            label=f"Ставка",
            custom_id="bet",
            style=disnake.TextInputStyle.short,
            placeholder="Введите к-во Румбиков для ставки",
            required=True,
            min_length=1,
            max_length=16,
        )

        challenge_user_input = disnake.ui.TextInput(
            label=f"Участник (необязательно)",
            custom_id="challenge_user_id",
            style=disnake.TextInputStyle.short,
            placeholder="Введите ID участника для вызова",
            required=False,
            min_length=0,
            max_length=32,
        )

        modal = disnake.ui.Modal(
            title="Камень-Ножницы-Бумага",
            custom_id="knb",
            components=[components, betz, challenge_user_input]
        )

        await inter.response.send_modal(modal=modal)
    @commands.slash_command(name='coinflip', description='Игра Орел или Решка')
    async def coinflip(self, inter: disnake.ApplicationCommandInteraction, ставка: int,
                       участник: disnake.Member = None):
        decline = disnake.utils.get(inter.author.guild.emojis, name='773229388573310996')

        # Проверка ставки
        if ставка < 10:
            error_message = f"{decline}  `{inter.author.display_name}`, Вы можете поставить не менее **10** румбиков."
            embed = self.create_error_embed(error_message)
            await inter.response.send_message(embed=embed, ephemeral=True)
            return

        balance = collusers.find_one({'id': inter.author.id})['balance']
        if balance < ставка:
            err = format_rumbick(ставка - balance)
            error_message = f"{decline}  `{inter.author.display_name}`, Вам не хватает {err}."
            embed = self.create_error_embed(error_message)
            await inter.response.send_message(embed=embed, ephemeral=True)
            return

        # Снимаем ставку у инициатора
        collusers.find_one_and_update({'id': inter.author.id}, {'$inc': {'balance': -ставка}})

        embed = disnake.Embed(title='Орел или Решка', color=0xff8800, timestamp=datetime.now())
        embed.set_author(name=inter.author.display_name, icon_url=inter.author.avatar.url)
        embed.set_thumbnail(
            url='https://cdn.dribbble.com/users/1493264/screenshots/5573460/coin-flip-dribbble.gif')  # Замените на актуальную ссылку на изображение
        embed.add_field(name='Ставка', value=f'{format_rumbick(ставка)}', inline=True)

        if участник:
            embed.add_field(name='Вызов брошен:', value=f'Только для: {участник.mention}', inline=False)
        else:
            embed.add_field(name='Вызов брошен:', value='Для всех участников', inline=False)
        embed.set_footer(text="Coinflip", icon_url=inter.guild.icon.url)

        # Кнопки для выбора
        async def button_callback(interaction: disnake.MessageInteraction, choice: str, embed: disnake.Embed):
            if участник and interaction.author.id != участник.id:
                error_message = f"{decline} `{interaction.author.display_name}`, Вы не можете участвовать в этой игре."
                embed = self.create_error_embed(error_message)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            if inter.author.id == interaction.author.id:
                error_message = f"{decline} `{interaction.author.display_name}`, Вы не можете играть сами с собой."
                embed = self.create_error_embed(error_message)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Проверяем баланс оппонента
            balance_opponent = collusers.find_one({'id': interaction.author.id})['balance']
            if balance_opponent < ставка:
                err = format_rumbick(ставка - balance_opponent)
                error_message = f"{decline} `{interaction.author.display_name}`, Вам не хватает {err}."
                embed = self.create_error_embed(error_message)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Снимаем ставку у оппонента
            collusers.find_one_and_update({'id': interaction.author.id}, {'$inc': {'balance': -ставка}})

            # Логика игры с шансом на ребро
            outcome = random.choices(['Орел', 'Решка', 'Ребро'], [0.45, 0.45, 0.10])[0]
            if outcome == 'Ребро':
                embed.add_field(name='Результат', value='Монета упала на ребро! Ставки возвращаются.', inline=False)
                # Возвращаем ставки
                collusers.find_one_and_update({'id': inter.author.id}, {'$inc': {'balance': ставка}})
                collusers.find_one_and_update({'id': interaction.author.id}, {'$inc': {'balance': ставка}})
            else:
                if choice == outcome:
                    if inter.author.id == interaction.author.id:  # Если выборы совпадают
                        embed.add_field(name='Результат', value=f'Выпала {outcome}.', inline=False)
                        embed.add_field(name='Выбор оппонента', value=f'{interaction.author.mention} выбрал {choice}.',
                                        inline=False)
                        embed.add_field(name='**Итоги:**',
                                        value='Ставки возвращаются, оба игрока выбрали одно и то же.', inline=False)
                        collusers.find_one_and_update({'id': inter.author.id}, {'$inc': {'balance': ставка}})
                        collusers.find_one_and_update({'id': interaction.author.id}, {'$inc': {'balance': ставка}})
                    else:  # Один из игроков выиграл
                        winner = interaction.author
                        loser = inter.author
                        embed.add_field(name='Результат', value=f'Выпала {outcome}.', inline=False)
                        embed.add_field(name='Выбор оппонента', value=f'{interaction.author.mention} выбрал {choice}.',
                                        inline=False)
                        embed.add_field(name='**Итоги:**',
                                        value=f'{winner.mention} выиграл!\n{loser.mention} проигрывает свою ставку.',
                                        inline=False)
                        collusers.find_one_and_update({'id': winner.id}, {'$inc': {'balance': ставка * 2}})
                else:
                    embed.add_field(name='Результат', value=f'Выпала {outcome}.', inline=False)
                    embed.add_field(name='Выбор оппонента', value=f'{interaction.author.mention} выбрал {choice}.',
                                    inline=False)
                    embed.add_field(name='**Итоги:**',
                                    value=f'{inter.author.mention} выиграл!\n{interaction.author.mention} проигрывает свою ставку.',
                                    inline=False)
                    collusers.find_one_and_update({'id': inter.author.id}, {'$inc': {'balance': ставка * 2}})

            await inter.edit_original_response(embed=embed, view=None)

        button_heads = disnake.ui.Button(label="Орел", style=disnake.ButtonStyle.primary)
        button_tails = disnake.ui.Button(label="Решка", style=disnake.ButtonStyle.primary)

        button_heads.callback = lambda i: button_callback(i, "Орел", embed)
        button_tails.callback = lambda i: button_callback(i, "Решка", embed)

        view = disnake.ui.View(timeout=300)
        view.add_item(button_heads)
        view.add_item(button_tails)

        async def on_timeout():
            embed.add_field(name="Игра отменена",
                            value="Никто не принял вызов в течение 5 минут.\n **Ставка возвращена**.",
                            inline=False)
            view.clear_items()
            await inter.edit_original_response(embed=embed, view=view)
            collusers.find_one_and_update({'id': inter.author.id}, {'$inc': {'balance': ставка}})

        view.on_timeout = on_timeout

        await inter.response.send_message(embed=embed, view=view)

    def create_error_embed(self, error_message):
        embed = disnake.Embed(title="Ошибка", description=error_message, color=0xff0000)
        return embed

def setup(bot):
    bot.add_cog(GamesCog(bot))
    print("GamesCog is ready")