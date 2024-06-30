import time
from asyncio import tasks
import disnake
from disnake.ext import commands, tasks
from datetime import datetime, timedelta
from pymongo import MongoClient


class MuteCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(name='mute', description='Позволяет замутить участника.')
    async def mute(self, inter: disnake.ApplicationCommandInteraction, участник: disnake.Member, время: str,
                   причина='Не указана'):
        if inter.type == disnake.InteractionType.application_command:
            await inter.response.defer()

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

            seconds = convert_to_seconds(время)
            duration = timedelta(seconds=seconds)
            await участник.timeout(duration=duration)
            embed = disnake.Embed(color=0xe69010)
            embed.add_field(name='', value=f'Мут выдан участнику **{участник.name}**', inline=False)
            embed.add_field(name='**Подробная информация:**',
                            value=f'Модератор: {inter.author.name} ({inter.author.mention})\n'
                                  f'Участник: {участник.name} ({участник.mention})\n'
                                  f'Длительность: {время} ({seconds})\n'
                                  f'Причина: {причина}')
            await inter.guild.get_channel(944562833901899827).send(embed=embed)
            await inter.edit_original_message(embed=embed)

            embed = disnake.Embed(color=0xe69010)
            embed.add_field(name='', value=f'**Вам выдали мут**', inline=False)
            embed.add_field(name='**Подробная информация:**',
                            value=f'Модератор: {inter.author.name} ({inter.author.mention})\n'
                                  f'Участник: {участник.name} ({участник.mention})\n'
                                  f'Длительность: {время} ({seconds})\n'
                                  f'Причина: {причина}')
            await участник.send(embed=embed)


def setup(bot):
    bot.add_cog(MuteCog(bot))
    print("MuteCog is ready")
