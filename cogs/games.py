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

emoji = "<:rumbick:1271089081601753118>"

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
            if figure in ['К', 'Н', 'Б']:
                bet = inter.text_values['bet']
                await inter.response.defer(with_message=True)  # Defer response to avoid multiple responses
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

                embed = disnake.Embed(title='Камень-Ножницы-Бумага', color=0xff00fa)
                embed.set_thumbnail(
                    url='https://media0.giphy.com/media/JoDQSE8d1tB2tsPAAg/200w.gif?cid=6c09b952xijiedj0le1rvko2nmee3rri4fzrvchqb4q7as94&ep=v1_gifs_search&rid=200w.gif&ct=g')
                embed.set_author(name=inter.author.display_name, icon_url=inter.author.avatar.url)
                embed.set_footer(text=f'Rock-Paper-Scissors', icon_url=inter.guild.icon.url)
                embed.add_field(name='Информация об игре', value=f'Ставка: {bet}', inline=True)

                # Функция для обработки нажатий на кнопки
                async def button_callback(interaction: disnake.MessageInteraction, choice: str):
                    balance_interaction = collusers.find_one({'id': interaction.author.id})['balance']
                    if author.id == interaction.author.id:
                        error_message = f"{decline} `{interaction.author.display_name}`, Вы не можете играть сами с собой."
                        embed = create_error_embed(error_message)
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return
                    if collusers.find_one({'id': interaction.author.id})['balance'] < cost:
                        err = format_rumbick(cost - balance_interaction)
                        error_message = f"{decline} `{interaction.author.display_name}`, Вам не хватает {err}."
                        embed = create_error_embed(error_message)
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return
                    collusers.find_one_and_update({'id': interaction.author.id}, {'$inc': {'balance': -cost}})

                # Функция для обработки нажатий на кнопки
                async def button_callback(interaction: disnake.MessageInteraction, choice: str, embed: disnake.Embed):
                    balance_interaction = collusers.find_one({'id': interaction.author.id})['balance']
                    if author.id == interaction.author.id:
                        error_message = f"{decline} `{interaction.author.display_name}`, Вы не можете играть сами с собой."
                        embed = create_error_embed(error_message)
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return
                    if collusers.find_one({'id': interaction.author.id})['balance'] < cost:
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

                    # Создание кнопок для выбора
                    button_rock = disnake.ui.Button(label="🗿 Камень", style=disnake.ButtonStyle.primary)
                    button_paper = disnake.ui.Button(label="📃 Бумага", style=disnake.ButtonStyle.primary)
                    button_scissors = disnake.ui.Button(label="✂️ Ножницы", style=disnake.ButtonStyle.primary)

                    # Привязка обработчиков к кнопкам
                    button_rock.callback = lambda i: button_callback(i, "Камень")
                    button_paper.callback = lambda i: button_callback(i, "Бумага")
                    button_scissors.callback = lambda i: button_callback(i, "Ножницы")

                    # Создаем view и добавляем кнопки
                    view = disnake.ui.View(timeout=None)
                    view.add_item(button_rock)
                    view.add_item(button_paper)
                    view.add_item(button_scissors)

                    await message.edit(embed=embed, view=view, content=None)

            else:
                error_message = f"{decline} `{inter.author.display_name}`, Вы выбрали несуществующий ход."
                embed = create_error_embed(error_message)
                await inter.response.send_message(embed=embed, ephemeral=True)

    class FigureEnum(disnake.enums.Enum):
        Камень = "Камень"
        Ножницы = "Ножницы"
        Бумага = "Бумага"

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

        modal = disnake.ui.Modal(
            title="Камень-Ножницы-Бумага",
            custom_id="knb",
            components=[components, betz]
        )

        await inter.response.send_modal(modal=modal)


def setup(bot):
    bot.add_cog(GamesCog(bot))
    print("GamesCog is ready")