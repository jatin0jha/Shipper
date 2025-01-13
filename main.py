from dotenv import load_dotenv
import os
import discord
from discord.ext import commands
from PIL import Image, ImageDraw
from io import BytesIO
import hashlib
import requests
import random

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TOKEN')

if not TOKEN:
    raise ValueError("TOKEN environment variable is not set.")

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="--", intents=intents)

# Initialize leaderboard storage
leaderboard = {}  # Format: {("user1_id", "user2_id"): affection_percentage}

# Compatibility quotes
quotes = {
    "100": ["You two are destined to be together forever! ❤️"],
    "80-99": ["A match made in heaven! 💕", "You complement each other perfectly! 😍"],
    "60-79": ["There's great chemistry between you two! 😊", "A solid connection here! 💞"],
    "40-59": ["You'd make good friends! 🤝", "You might need to work on your bond. 🤔"],
    "20-39": ["It’s complicated. 😕", "Not the best match, but who knows? 🤷"],
    "0-19": ["This might be a disaster waiting to happen. 😬", "Polar opposites, perhaps? 😢"]
}

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

    # Add to leaderboard
    pair_key = tuple(sorted([user1.id, user2.id]))
    leaderboard[pair_key] = affection

    return affection, meaning

# Add compatibility quote based on affection percentage
def get_quote(affection):
    if affection == 100:
        return random.choice(quotes["100"])
    elif 80 <= affection < 100:
        return random.choice(quotes["80-99"])
    elif 60 <= affection < 80:
        return random.choice(quotes["60-79"])
    elif 40 <= affection < 60:
        return random.choice(quotes["40-59"])
    elif 20 <= affection < 40:
        return random.choice(quotes["20-39"])
    else:
        return random.choice(quotes["0-19"])

# Leaderboard command
@bot.command(name="lb")
async def leaderboard_command(ctx):
    if not leaderboard:
        await ctx.send("No ships have been recorded yet! Start shipping to create a leaderboard!")
        return

    # Sort leaderboard by affection percentage
    sorted_leaderboard = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
    top_pairs = sorted_leaderboard[:5]  # Show top 5 pairs

    description = ""
    for i, ((user1_id, user2_id), affection) in enumerate(top_pairs, 1):
        # Try fetching users via Discord API
        try:
            user1 = await bot.fetch_user(user1_id)
        except discord.NotFound:
            user1 = None

        try:
            user2 = await bot.fetch_user(user2_id)
        except discord.NotFound:
            user2 = None

        # If the user is None, handle gracefully
        user1_name = user1.mention if user1 else f"Unknown User ({user1_id})"
        user2_name = user2.mention if user2 else f"Unknown User ({user2_id})"

        description += f"**{i}.** {user1_name} ❤️ {user2_name} - **{affection}%**\n"

    embed = discord.Embed(
        title="💘 Shipping Leaderboard",
        description=description,
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)


# Random shipping command
@bot.command(name="random")
async def random_ship(ctx):
    members = [member for member in ctx.guild.members if not member.bot and member != ctx.author]
    if not members:
        await ctx.send("There aren't enough users to ship!")
        return

    random_user = random.choice(members)
    affection, meaning = calculate_affection(ctx.author, random_user)
    image_buffer = generate_ship_image(ctx.author, random_user, affection)

    embed = create_embed(ctx.author, random_user, affection, meaning)
    embed.add_field(name="Compatibility Quote", value=get_quote(affection), inline=False)

    image_buffer.seek(0)
    file = discord.File(image_buffer, filename="random_ship.png")
    embed.set_image(url="attachment://random_ship.png")

    await ctx.send(
        content=f"{ctx.author.mention} ❤️ {random_user.mention}",
        embed=embed,
        file=file
    )

# Helper function: Create a circular version of an image
def create_circular_image(image):
    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + image.size, fill=255)
    result = Image.new("RGBA", image.size, (255, 255, 255, 0))
    result.paste(image, (0, 0), mask)
    return result

from PIL import Image, ImageDraw, ImageSequence
import requests
from io import BytesIO

def generate_ship_image(user1, user2, affection):
    """Generate a shipping image for two users with custom backgrounds and save as a GIF."""
    # Default image URL for fallback avatars
    default_image_url = "https://raw.githubusercontent.com/jatin0jha/Shipper/refs/heads/main/discord%20pfp.png"
    
    # Try fetching user1's avatar
    try:
        response1 = requests.get(user1.avatar.url, timeout=5)
        response1.raise_for_status()
        avatar1 = Image.open(BytesIO(response1.content)).resize((150, 150))
    except Exception as e:
        print(f"Error fetching avatar for {user1.name}: {e}")
        response1 = requests.get(default_image_url)
        avatar1 = Image.open(BytesIO(response1.content)).resize((150, 150))

    # Try fetching user2's avatar
    try:
        response2 = requests.get(user2.avatar.url, timeout=5)
        response2.raise_for_status()
        avatar2 = Image.open(BytesIO(response2.content)).resize((150, 150))
    except Exception as e:
        print(f"Error fetching avatar for {user2.name}: {e}")
        response2 = requests.get(default_image_url)
        avatar2 = Image.open(BytesIO(response2.content)).resize((150, 150))

    # Create circular avatars
    avatar1 = create_circular_image(avatar1)
    avatar2 = create_circular_image(avatar2)

    # Set the heart image based on affection
    heart_path = "heart.png" if affection >= 50 else "broken_heart.png"
    heart = Image.open(heart_path).resize((75, 75))

    # Set background based on affection
    if affection == 100:
        background_url = "https://i.pinimg.com/originals/3c/7a/77/3c7a770da649c31628f60696962cefca.gif"
    elif affection == 0:
        background_url = "https://i.pinimg.com/originals/3d/f6/90/3df690c36bfb6b60c17cc69dc008906d.gif"
    else:
        background_url = "https://defa"  # Default background

    # Fetch background GIF
    try:
        response_bg = requests.get(background_url, timeout=5)
        response_bg.raise_for_status()
        background = Image.open(BytesIO(response_bg.content))
    except Exception as e:
        print(f"Error fetching background: {e}")
        # Fallback to default background if error occurs
        background = Image.open(BytesIO(requests.get(background_url).content))

    # Resize background to fit canvas
    canvas_width, canvas_height = 500, 200
    background = background.resize((canvas_width, canvas_height))

    # Create canvas
    canvas = Image.new("RGBA", (canvas_width, canvas_height), (255, 255, 255, 0))
    canvas.paste(background, (0, 0))

    # Position avatars and heart
    avatar1_x, avatar1_y = 50, 25
    avatar2_x, avatar2_y = 300, 25
    heart_x, heart_y = (canvas_width - heart.width) // 2, (canvas_height - heart.height) // 2

    canvas.paste(avatar1, (avatar1_x, avatar1_y), mask=avatar1)
    canvas.paste(heart, (heart_x, heart_y), mask=heart)
    canvas.paste(avatar2, (avatar2_x, avatar2_y), mask=avatar2)

    # Create GIF with one frame
    image_buffer = BytesIO()
    frames = [canvas]  # List of frames, just one in this case
    
    # Save as GIF
    canvas.save(image_buffer, format="GIF", save_all=True, append_images=frames, duration=500, loop=0)
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
    if message.author == bot.user:
        return

    if message.content.startswith("--ship"):
        mentions = message.mentions
        if len(mentions) == 1:
            user1, user2 = message.author, mentions[0]
        elif len(mentions) == 2:
            user1, user2 = mentions[0], mentions[1]
        else:
            await message.channel.send("Please mention one or two users to ship!")
            return

        affection, meaning = calculate_affection(user1, user2)
        image_buffer = generate_ship_image(user1, user2, affection)

        embed = create_embed(user1, user2, affection, meaning)
        embed.add_field(name="Compatibility Quote", value=get_quote(affection), inline=False)

        image_buffer.seek(0)
        file = discord.File(image_buffer, filename="ship.png")
        embed.set_image(url="attachment://ship.png")

        await message.channel.send(
            content=f"{user1.mention} ❤️ {user2.mention}",
            embed=embed,
            file=file
        )

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
