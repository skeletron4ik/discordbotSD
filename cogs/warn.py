import time
from asyncio import tasks

import disnake
from disnake.ext import commands, tasks
from datetime import datetime
from pymongo import MongoClient

cluster = MongoClient(
    "mongodb+srv://Skeletron:1337@cluster0.knkajvi.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
collusers = cluster.server.users
collservers = cluster.server.servers


class WarnsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_warns.start()  # Запуск циклической задачи при инициализации

    @tasks.loop(seconds=30)  # Проверка каждые 30 секунд
    async def check_warns(self):
        # Получение текущего времени
        current_timestamp = int(datetime.now().timestamp())

        # Поиск пользователей с истекшим временем предупреждения
        expired_warns = collusers.find({"reasons.timestamp": {"$lte": current_timestamp}})

        for user in expired_warns:
            guild_id = user["guild_id"]
            guild = self.bot.get_guild(guild_id) or await self.bot.fetch_guild(guild_id)

            for reason in user["reasons"]:
                if reason["timestamp"] <= current_timestamp:
                    # Удаление истекших предупреждений из списка и обновление базы данных
                    collusers.update_one(
                        {"id": user["id"], "guild_id": user["guild_id"]},
                        {"$pull": {"reasons": {"timestamp": reason["timestamp"]}}},
                    )
                    collusers.update_one(
                        {"id": user["id"], "guild_id": user["guild_id"]},
                        {"$inc": {"warns": -1}}
                    )

                    embed = disnake.Embed()
                    embed.add_field(name="Модерация", value="Ваш варн успешно снят.", inline=True)

                    member = guild.get_member(user["id"]) or await guild.fetch_member(user["id"])
                    if member:
                        await member.send(embed=embed)

    @check_warns.before_loop
    async def before_check_warns(self):
        await self.bot.wait_until_ready()  # Ожидание готовности бота перед запуском цикла

    @commands.slash_command(name="warn", description="Выдает предупреждение.")
    async def warn(self, ctx, member: disnake.Member, amount: int, reason="Причина не указана."):
        timestamp = int(datetime.now().timestamp() + 2592000)
        print(timestamp)
        warn_info = {
            "reason": reason,
            "timestamp": timestamp
        }

        collservers.update_one(
            {"_id": ctx.guild.id},
            {"$inc": {"case": amount}},
            upsert=True
        )
        for i in range(amount):
            collusers.update_one(
                {"id": member.id, "guild_id": ctx.guild.id},
                {
                    "$inc": {"warns": 1},
                    "$push": {"reasons": warn_info}
                },
                upsert=True
            )

        warns_count = collusers.find_one({"id": member.id})["warns"]

        await ctx.send(
            f"{member.mention} получил предупреждение: {reason}\nЗакончится: <t:{timestamp}:R>\nКоличество предупреждений: {warns_count}")
        await member.send(f'{ctx.author.mention}')


def setup(bot):
    bot.add_cog(WarnsCog(bot))
    print("ready")
