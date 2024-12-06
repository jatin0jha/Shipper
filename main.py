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
    # Combine the usernames and create a unique "relationship key"
    combined = f"{user1.name.lower()}_{user2.name.lower()}"
    
    # Create a hash of the combined string
    hash_object = hashlib.sha256(combined.encode('utf-8'))
    hash_value = int(hash_object.hexdigest(), 16)
    
    # Normalize the hash value to a percentage (0–100)
    affection = hash_value % 101  # 101 because it's exclusive of the upper bound
    
    # Determine meaning based on percentage
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
    # Load user profile pictures
    response1 = requests.get(user1.avatar.url)
    response2 = requests.get(user2.avatar.url)
    avatar1 = Image.open(BytesIO(response1.content)).resize((150, 150))
    avatar2 = Image.open(BytesIO(response2.content)).resize((150, 150))

    # Create circular avatars
    avatar1 = create_circular_image(avatar1)
    avatar2 = create_circular_image(avatar2)

    # Load heart or broken heart image based on affection percentage
    heart_path = "heart.png" if affection >= 50 else "broken_heart.png"
    heart = Image.open(heart_path).resize((75, 75))

    # Create a blank canvas
    canvas_width = 500
    canvas_height = 200
    canvas = Image.new("RGBA", (canvas_width, canvas_height), (255, 255, 255, 0))

    # Adjusted positions for avatars and heart
    avatar1_x, avatar1_y = 50, 25
    avatar2_x, avatar2_y = 300, 25
    heart_x, heart_y = (canvas_width - heart.width) // 2, (canvas_height - heart.height) // 2

    # Paste avatars and heart on the canvas
    canvas.paste(avatar1, (avatar1_x, avatar1_y), mask=avatar1)
    canvas.paste(heart, (heart_x, heart_y), mask=heart)
    canvas.paste(avatar2, (avatar2_x, avatar2_y), mask=avatar2)

    # Return the canvas
    image_buffer = BytesIO()
    canvas.save(image_buffer, format="PNG")
    image_buffer.seek(0)
    return image_buffer

# Slash command for shipping with image in embed
@bot.tree.command(name="ship", description="Ship two users and see their affection percentage!")
async def ship(interaction: discord.Interaction, user1: discord.Member, user2: discord.Member):
    affection, meaning = calculate_affection(user1, user2)
    image_buffer = generate_ship_image(user1, user2, affection)

    # Create an embed with affection details as fields
    embed = discord.Embed(
        title="💘 Shipping Results",
        color=discord.Color.purple()  # You can change the color as needed
    )
    
    embed.add_field(name="Affection", value=f"**{affection}%**", inline=True)
    embed.add_field(name="Result", value=f"**{meaning}**", inline=True)

    # Attach the image as an embed image
    image_buffer.seek(0)  # Reset buffer position to the start
    file = discord.File(image_buffer, filename="ship.png")  # Pass the file buffer to File

    # Set the image URL in the embed to the filename of the attached file
    embed.set_image(url="attachment://ship.png")

    # Send the embed with the image file attached
    await interaction.response.send_message(
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

        # Create an embed with affection details as fields (same as in the slash command)
        embed = discord.Embed(
            title="💘 Shipping Results",
            color=discord.Color.purple()  # You can change the color as needed
        )
        
        embed.add_field(name="Affection", value=f"**{affection}%**", inline=True)
        embed.add_field(name="Result", value=f"**{meaning}**", inline=True)

        # Attach the image as an embed image (same as in the slash command)
        image_buffer.seek(0)  # Reset buffer position to the start
        file = discord.File(image_buffer, filename="ship.png")  # Pass the file buffer to File

        # Set the image URL in the embed to the filename of the attached file
        embed.set_image(url="attachment://ship.png")

        # Send the embed with the image file attached
        await message.channel.send(
            embed=embed,
            file=file
        )

    # Process commands after handling messages
    await bot.process_commands(message)

# Event handler: Notify when bot is ready
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands!")
    except Exception as e:
        print(f"Error syncing commands: {e}")
    print(f"Bot is ready! Logged in as {bot.user}")

# Run the bot
bot.run(TOKEN)
