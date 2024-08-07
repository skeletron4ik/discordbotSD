import disnake
from disnake.ext import commands

# Создаем список промокодов для проверки
PROMO_CODES = {
    "ROLE2024": {"type": "role", "role_id": 519925714309349377},
    "COINS100": {"type": "coins", "amount": 100},
}

# Словарь для хранения баланса монеток пользователей
user_balances = {}


class Promo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Функция для выдачи роли
    async def give_role(self, inter, role_id):
        role = disnake.utils.get(inter.guild.roles, id=role_id)
        if role:
            await inter.author.add_roles(role)
            await inter.send(f'Вам была выдана роль: {role.name}')
        else:
            await inter.send(f'Роль с ID {role_id} не найдена на сервере.')

    # Функция для начисления монеток
    def add_coins(self, user_id, amount):
        if user_id in user_balances:
            user_balances[user_id] += amount
        else:
            user_balances[user_id] = amount

    @commands.slash_command(name="promo", description="Активирует промокод")
    async def promo(self, inter: disnake.ApplicationCommandInteraction, code: str):
        promo_info = PROMO_CODES.get(code.upper())

        if promo_info:
            if promo_info["type"] == "role":
                role_id = promo_info.get("role_id")
                if role_id:
                    await self.give_role(inter, role_id)
                else:
                    await inter.send("В промокоде не указан ID роли.")
            elif promo_info["type"] == "coins":
                amount = promo_info.get("amount")
                if amount:
                    self.add_coins(inter.author.id, amount)
                    await inter.send(f'Вам было начислено {amount} монеток. Ваш текущий баланс: {user_balances[inter.author.id]} монеток.')
                else:
                    await inter.send("В промокоде не указано количество монеток.")
        else:
            await inter.send("Промокод недействителен.")

def setup(bot):
    bot.add_cog(Promo(bot))
    print("PromoCog is ready")

