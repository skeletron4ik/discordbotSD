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
from ai.promo import create_rumbicks
from ai.process_role import process_role

collusers = cluster.server.users
collservers = cluster.server.servers
# ID роли Diamond
DIAMOND_ROLE_ID = 1044314368717897868

class GrantDiamondCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name='roleforall', description="Выдать роль Diamond всем на 7 дней")
    @commands.has_permissions(administrator=True)
    async def grant_diamond(self, inter: disnake.ApplicationCommandInteraction):
        guild = inter.guild
        diamond_role = disnake.utils.get(guild.roles, id=DIAMOND_ROLE_ID)

        if diamond_role is None:
            await inter.response.send_message(
                "Роль Diamond не найдена. Пожалуйста, проверьте ID роли.", ephemeral=True
            )
            return

        success_count = 0
        error_count = 0
        log_channel_id = 944562833901899827  # ID канала для логов
        log_channel = await self.bot.fetch_channel(log_channel_id)

        # Устанавливаем срок действия роли
        new_expiry = int((datetime.now() + timedelta(days=7)).timestamp())

        for member in guild.members:
            if member.bot:
                continue

            try:
                user_data = collusers.find_one({'id': member.id})

                if user_data:
                    role_info = next(
                        (role for role in user_data.get("role_ids", []) if role["role_ids"] == DIAMOND_ROLE_ID),
                        None
                    )

                    if role_info:
                        current_expiry = role_info.get("expires_at", 0)
                        remaining_time = max(0, current_expiry - int(datetime.now().timestamp()))
                        new_expiry = int(datetime.now().timestamp()) + remaining_time + 604800  # 7 дней

                        collusers.update_one(
                            {"id": member.id, "role_ids.role_ids": DIAMOND_ROLE_ID},
                            {"$set": {"role_ids.$.expires_at": new_expiry}}
                        )
                    else:
                        collusers.update_one(
                            {"id": member.id},
                            {"$push": {"role_ids": {"role_ids": DIAMOND_ROLE_ID, "expires_at": new_expiry}}},
                            upsert=True
                        )

                await member.add_roles(diamond_role)
                success_count += 1
            except Exception as e:
                error_count += 1
                print(f"Ошибка при выдаче роли участнику {member.name}: {e}")

        embed = disnake.Embed(
            title="Результаты выдачи роли Diamond",
            description=f"Успешно выдано: {success_count}\nОшибки: {error_count}",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        await inter.response.send_message(embed=embed, ephemeral=True)

        # Логируем результаты
        if log_channel:
            await log_channel.send(embed=embed)

# Добавляем команду в бота
def setup(bot):
    bot.add_cog(GrantDiamondCommand(bot))
    print("Roleforall is ready")
