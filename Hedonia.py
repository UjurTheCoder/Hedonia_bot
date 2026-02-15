import discord
from discord.ext import commands
import json
import asyncio
from datetime import timedelta
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

WARN_FILE = "warns.json"
LOG_CHANNEL_NAME = "mod-log"
VOICE_CHANNEL_ID = 1472291241634037931  # kendi ses kanalın

# ===== WARN SYSTEM =====
def load_warns():
    try:
        with open(WARN_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_warns(data):
    with open(WARN_FILE, "w") as f:
        json.dump(data, f, indent=4)

warns = load_warns()

async def log(ctx, message):
    channel = discord.utils.get(ctx.guild.text_channels, name=LOG_CHANNEL_NAME)
    if channel:
        await channel.send(message)

# ===== READY + VOICE (TEK SEFER) =====
@bot.event
async def on_ready():
    print(f"{bot.user} aktif!")

    channel = bot.get_channel(VOICE_CHANNEL_ID)
    if not channel:
        print("Ses kanalı bulunamadı")
        return

    vc = channel.guild.voice_client
    if vc and vc.is_connected():
        print("Zaten seste")
        return

    try:
        await channel.connect()
        print("Ses kanalına bağlandı")
    except Exception as e:
        print("Ses hatası:", e)

# ===== WARN =====
@bot.command()
@commands.has_permissions(manage_messages=True)
async def warn(ctx, member: discord.Member, *, reason="Sebep yok"):
    gid = str(ctx.guild.id)
    uid = str(member.id)

    warns.setdefault(gid, {})
    warns[gid].setdefault(uid, [])
    warns[gid][uid].append(reason)
    save_warns(warns)

    count = len(warns[gid][uid])
    await ctx.send(f"{member} uyarıldı ({count} warn)")
    await log(ctx, f"{member} warn aldı: {reason}")

    if count == 3:
        await member.timeout(discord.utils.utcnow() + timedelta(minutes=10))
        await ctx.send(f"{member} 10 dk timeout aldı")

    if count == 5:
        await member.kick(reason="5 warn")
        await ctx.send(f"{member} kicklendi (5 warn)")

# ===== WARN LIST =====
@bot.command()
async def warnings(ctx, member: discord.Member):
    gid = str(ctx.guild.id)
    uid = str(member.id)

    if gid in warns and uid in warns[gid]:
        text = "\n".join(f"{i+1}. {r}" for i, r in enumerate(warns[gid][uid]))
        await ctx.send(f"{member} warnları:\n{text}")
    else:
        await ctx.send("Warn yok")

# ===== MUTE =====
@bot.command()
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, minutes: int):
    await member.timeout(discord.utils.utcnow() + timedelta(minutes=minutes))
    await ctx.send(f"{member} {minutes} dk mute")
    await log(ctx, f"{member} mute aldı")

@bot.command()
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member):
    await member.timeout(None)
    await ctx.send(f"{member} unmute edildi")
    await log(ctx, f"{member} unmute")

# ===== ROLE =====
@bot.command()
@commands.has_permissions(manage_roles=True)
async def role(ctx, member: discord.Member, role: discord.Role):
    await member.add_roles(role)
    await ctx.send(f"{member} rol aldı: {role}")
    await log(ctx, f"{member} rol aldı {role}")

# ===== CLEAR =====
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount)
    msg = await ctx.send(f"{amount} mesaj silindi")
    await asyncio.sleep(3)
    await msg.delete()

# ===== ANTISPAM (BASİT & GÜVENLİ) =====
spam = {}

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    uid = message.author.id
    spam.setdefault(uid, 0)
    spam[uid] += 1

    if spam[uid] > 5:
        await message.author.timeout(discord.utils.utcnow() + timedelta(minutes=1))
        spam[uid] = 0
        await message.channel.send(f"{message.author} spam yaptı, timeout!")

    await bot.process_commands(message)

# ===== RUN =====
bot.run(os.getenv("TOKEN"))
