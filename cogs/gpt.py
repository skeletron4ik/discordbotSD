import asyncio
import re
import time
from asyncio import tasks
import disnake
from disnake.ext import commands, tasks
from datetime import datetime, timedelta
from pymongo import MongoClient
import g4f
import curl_cffi
import nest_asyncio
from g4f.Provider import Bing
from g4f.Provider import Raycast
from g4f.client import Client
from mtranslate import translate




class GPTCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.inter = disnake.ApplicationCommandInteraction



    @commands.Cog.listener()
    async def on_message(self, message: disnake.Message):
        messages = message.content
        if self.bot.user.mentioned_in(message):
            print('bot')

            response = g4f.ChatCompletion.create(
                model='gpt-3.5-turbo',
                messages=[{"role": "user", "content": messages}],
                stream=True,
                language='ru',
            )

            messag = await message.channel.send(message.author.mention + ', ' + 'Идет генерация...')
            parts = []
            for mess in response:
                parts.append(mess)
            result = ''.join(parts)

            result = translate(result, 'ru')
            try:
                await messag.edit(message.author.mention + ', ' + result)
            except:
                with open('result.txt', 'w') as file:
                    file.write(result)
                    await messag.edit(message.author.mention + ', Ответ в файле!', file=disnake.File('result.txt'))



def setup(bot):
    bot.add_cog(GPTCog(bot))
    print("GPTCog is ready")