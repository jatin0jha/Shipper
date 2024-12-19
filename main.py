from dotenv import load_dotenv
import os
import discord
from discord.ext import commands
from PIL import Image, ImageDraw
from io import BytesIO
import hashlib
import requests

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TOKEN')

if not TOKEN:
    raise ValueError("TOKEN environment variable is not set.")

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Helper function: Calculate affection percentage and result meaning
def calculate_affection(user1, user2):
    combined = f"{user1.name.lower()}_{user2.name.lower()}"
    hash_object = hashlib.sha256(combined.encode('utf-8'))
    hash_value = int(hash_object.hexdigest(), 16)
    affection = hash_value % 101

    if affection == 100:
        meaning = "Soulmates! ❤️"
    elif affection >= 80:
        meaning = "Perfect Match! 💕"
    elif affection == 69:
        meaning = "( ¬ᴗ¬)"
    elif affection >= 60:
        meaning = "Great Chemistry! 😊"
    elif affection >= 40:
        meaning = "Good Friends! 🤝"
    elif affection >= 20:
        meaning = "Just Acquaintances. 🤔"
    elif affection > 0:
        meaning = "Not Really Compatible. 😕"
    else:
        meaning = "Arch Nemesis! ⚔️"

    return affection, meaning

# Helper function: Create a circular version of an image
def create_circular_image(image):
    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + image.size, fill=255)
    result = Image.new("RGBA", image.size, (255, 255, 255, 0))
    result.paste(image, (0, 0), mask)
    return result

# Function to generate the shipping image
def generate_ship_image(user1, user2, affection):
    response1 = requests.get(user1.avatar.url)
    response2 = requests.get(user2.avatar.url)
    avatar1 = Image.open(BytesIO(response1.content)).resize((150, 150))
    avatar2 = Image.open(BytesIO(response2.content)).resize((150, 150))

    avatar1 = create_circular_image(avatar1)
    avatar2 = create_circular_image(avatar2)

    heart_path = "heart.png" if affection >= 50 else "broken_heart.png"
    heart = Image.open(heart_path).resize((75, 75))

    canvas_width = 500
    canvas_height = 200
    canvas = Image.new("RGBA", (canvas_width, canvas_height), (255, 255, 255, 0))

    avatar1_x, avatar1_y = 50, 25
    avatar2_x, avatar2_y = 300, 25
    heart_x, heart_y = (canvas_width - heart.width) // 2, (canvas_height - heart.height) // 2

    canvas.paste(avatar1, (avatar1_x, avatar1_y), mask=avatar1)
    canvas.paste(heart, (heart_x, heart_y), mask=heart)
    canvas.paste(avatar2, (avatar2_x, avatar2_y), mask=avatar2)

    image_buffer = BytesIO()
    canvas.save(image_buffer, format="PNG")
    image_buffer.seek(0)
    return image_buffer

# Embed creation for the slash command and `--ship` command
def create_embed(user1, user2, affection, meaning):
    embed = discord.Embed(
        title="💘 Shipping Results",
        description=f"Shipping `{user1.display_name}` and `{user2.display_name}`...\n"
                    f"**Affection: {affection}%**\n**Result: {meaning}**",
        color=discord.Color.purple()
    )
    return embed

# Slash command for shipping with image in embed
@bot.tree.command(name="ship", description="Ship two users and see their affection percentage!")
async def ship(interaction: discord.Interaction, user1: discord.Member, user2: discord.Member):
    affection, meaning = calculate_affection(user1, user2)
    image_buffer = generate_ship_image(user1, user2, affection)

    # Create an embed with the affection details
    embed = create_embed(user1, user2, affection, meaning)

    # Attach the image as an embed image
    image_buffer.seek(0)  # Reset buffer position to the start
    file = discord.File(image_buffer, filename="ship.png")  # Pass the file buffer to File

    # Set the image URL in the embed to the filename of the attached file
    embed.set_image(url="attachment://ship.png")

    # Send the plain message with mentions followed by the embed and image
    await interaction.response.send_message(
        content=f"{user1.mention} ❤️ {user2.mention}",
        embed=embed,
        file=file
    )

# Message event handler for `--ship` command
@bot.event
async def on_message(message):
    # Ignore bot's own messages
    if message.author == bot.user:
        return

    # Handle `--ship` command
    if message.content.startswith('--ship'):
        mentions = message.mentions
        if len(mentions) == 1:
            user1, user2 = message.author, mentions[0]
        elif len(mentions) == 2:
            user1, user2 = mentions[0], mentions[1]
        else:
            await message.channel.send("Please mention one or two users to ship, like `--ship @user1` or `--ship @user1 @user2`.")
            return

        affection, meaning = calculate_affection(user1, user2)
        image_buffer = generate_ship_image(user1, user2, affection)

        # Create an embed with the affection details
        embed = create_embed(user1, user2, affection, meaning)

        # Attach the image as an embed image (same as in the slash command)
        image_buffer.seek(0)  # Reset buffer position to the start
        file = discord.File(image_buffer, filename="ship.png")  # Pass the file buffer to File

        # Set the image URL in the embed to the filename of the attached file
        embed.set_image(url="attachment://ship.png")

        # Send the plain message with mentions followed by the embed and image
        await message.channel.send(
            content=f"{user1.mention} ❤️ {user2.mention}",
            embed=embed,
            file=file
        )

    # Process commands after handling messages
    await bot.process_commands(message)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands!")
    except Exception as e:
        print(f"Error syncing commands: {e}")
    print(f"Bot is ready! Logged in as {bot.user}")

bot.run(TOKEN)
