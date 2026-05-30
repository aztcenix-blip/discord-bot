print("VERSION ADDMONEY TEST")

from flask import Flask
from threading import Thread
import os
import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
import random

# ===== Flask =====
app = Flask('')

@app.route('/')
def home():
    return "BOT is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# ===== Intent設定 =====
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ===== SQLite接続 =====
conn = sqlite3.connect("money.db")
cursor = conn.cursor()

# ===== テーブル作成 =====
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    money INTEGER
)
""")

conn.commit()

# ===== ユーザー作成 =====
def create_user(user_id):
    cursor.execute(
        "SELECT * FROM users WHERE user_id = ?",
        (str(user_id),)
    )

    user = cursor.fetchone()

    if user is None:
        cursor.execute(
            "INSERT INTO users (user_id, money) VALUES (?, ?)",
            (str(user_id), 0)
        )

        conn.commit()

# ===== BOT起動 =====
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)}個のコマンドを同期")
        for cmd in synced:
            print(f"- {cmd.name}")
    except Exception as e:
        print(f"同期エラー: {e}")

    print(f"{bot.user} 起動！")
# ===== 所持金確認 =====
@bot.tree.command(name="balance", description="所持金確認")
async def balance(interaction: discord.Interaction):

    create_user(interaction.user.id)

    cursor.execute(
        "SELECT money FROM users WHERE user_id = ?",
        (str(interaction.user.id),)
    )

    money = cursor.fetchone()[0]

    await interaction.response.send_message(
        f"{interaction.user.mention} の所持金: {money}RC"
    )

# ===== お金を稼ぐ =====
@bot.tree.command(name="work", description="お金を稼ぐ")
async def work(interaction: discord.Interaction):

    create_user(interaction.user.id)

    earn = random.randint(100, 500)

    cursor.execute(
        "UPDATE users SET money = money + ? WHERE user_id = ?",
        (earn, str(interaction.user.id))
    )

    conn.commit()

    await interaction.response.send_message(
        f"{interaction.user.mention} は {earn}RC 稼いだ！"
    )

# ===== 初期資金 =====
@bot.tree.command(name="starter", description="初期資金を受け取る")
async def starter(interaction: discord.Interaction):

    create_user(interaction.user.id)

    cursor.execute(
        "SELECT money FROM users WHERE user_id = ?",
        (str(interaction.user.id),)
    )

    money = cursor.fetchone()[0]

    if money > 0:
        await interaction.response.send_message(
            "すでに初期資金を受け取っています！"
        )
        return

    cursor.execute(
        "UPDATE users SET money = 50000 WHERE user_id = ?",
        (str(interaction.user.id),)
    )

    conn.commit()

    await interaction.response.send_message(
        f"{interaction.user.mention} は 50000RC を受け取った！"
    )

# ===== 送金 =====
# ===== 管理者専用お金追加 =====
@bot.tree.command(name="addmoney", description="管理者専用: お金を追加")
@app_commands.describe(
    member="追加する相手",
    amount="追加する金額"
)
async def addmoney(
    interaction: discord.Interaction,
    member: discord.Member,
    amount: int
):

    OWNER_ID = 855686564449615912

    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message(
            "このコマンドは使用できません。",
            ephemeral=True
        )
        return

    if amount <= 0:
        await interaction.response.send_message(
            "1以上の金額を入力してください。"
        )
        return

    create_user(member.id)

    cursor.execute(
        "UPDATE users SET money = money + ? WHERE user_id = ?",
        (amount, str(member.id))
    )

    conn.commit()

    await interaction.response.send_message(
        f"{member.mention} に {amount}RC追加しました。"
    )
@bot.tree.command(name="pay", description="送金")
@app_commands.describe(
    member="送る相手",
    amount="送る金額"
)
async def pay(
    interaction: discord.Interaction,
    member: discord.Member,
    amount: int
):

    create_user(interaction.user.id)
    create_user(member.id)

    cursor.execute(
        "SELECT money FROM users WHERE user_id = ?",
        (str(interaction.user.id),)
    )

    sender_money = cursor.fetchone()[0]

    if sender_money < amount:
        await interaction.response.send_message(
            "お金が足りません！"
        )
        return

    if amount <= 0:
        await interaction.response.send_message(
            "1以上の数字を入力してください！"
        )
        return

    # 送る側
    cursor.execute(
        "UPDATE users SET money = money - ? WHERE user_id = ?",
        (amount, str(interaction.user.id))
    )

    # 受け取る側
    cursor.execute(
        "UPDATE users SET money = money + ? WHERE user_id = ?",
        (amount, str(member.id))
    )

    conn.commit()

    await interaction.response.send_message(
        f"{interaction.user.mention} → {member.mention} に {amount}RC送金！"
    )

# ===== 起動 =====
keep_alive()

bot.run(os.getenv("DISCORD_TOKEN"))
