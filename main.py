from dotenv import load_dotenv
import os
import discord
from discord.ext import commands
import hashlib  # For deterministic hashing
from datetime import datetime

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TOKEN')

if not TOKEN:
    raise ValueError("TOKEN environment variable is not set.")

# Define intents
intents = discord.Intents.default()
intents.message_content = True

# Initialize bot with commands
class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Sync slash commands
        await self.tree.sync()
        print("Slash commands synced!")

bot = MyBot()

# Mean daily motions of planets (degrees per day)
PLANETARY_MOTIONS = {
    "Sun": 1.0,
    "Moon": 13.2,
    "Mercury": 1.2,
    "Venus": 1.1,
    "Mars": 0.5,
    "Jupiter": 0.08,
    "Saturn": 0.03,
}

# Reference positions on January 1, 2000 (in degrees, simplified)
REFERENCE_POSITIONS = {
    "Sun": 280.46,
    "Moon": 218.32,
    "Mercury": 252.25,
    "Venus": 181.79,
    "Mars": 353.06,
    "Jupiter": 34.35,
    "Saturn": 50.08,
}

def days_since_epoch(date_of_birth):
    """Calculate days since January 1, 2000."""
    epoch = datetime(2000, 1, 1)
    dob = datetime.strptime(date_of_birth, "%Y-%m-%d")
    return (dob - epoch).days

def calculate_planet_position(planet, days):
    """Calculate the position of a planet based on days since epoch."""
    base_position = REFERENCE_POSITIONS[planet]
    daily_motion = PLANETARY_MOTIONS[planet]
    position = base_position + (daily_motion * days)
    return position % 360  # Keep within 0-360 degrees

def generate_simplified_chart(date_of_birth):
    """Generate simplified planetary positions for the given date of birth."""
    days = days_since_epoch(date_of_birth)
    chart = {}
    for planet in ["Sun", "Moon", "Venus", "Mars", "Saturn"]:  # Focused planets
        chart[planet] = calculate_planet_position(planet, days)
    return chart

def calculate_synastry_relation(angle1, angle2):
    """Determine synastry relation between two angles."""
    diff = abs(angle1 - angle2) % 360
    if diff > 180:
        diff = 360 - diff  # Normalize to 0-180 degrees
    # Interpret the aspect into synastry relation
    if abs(diff - 0) <= 6 or abs(diff - 180) <= 6:  # Conjunction or Opposition
        return "Attraction"
    elif abs(diff - 90) <= 6:  # Square
        return "Tension"
    elif abs(diff - 60) <= 6 or abs(diff - 120) <= 6:  # Sextile or Trine
        return "Neutral"
    else:
        return "Neutral"

def analyze_simplified_synastry(chart1, chart2):
    """Analyze synastry between two simplified charts."""
    attraction_count = 0
    tension_count = 0
    neutral_count = 0
    
    for planet1, position1 in chart1.items():
        for planet2, position2 in chart2.items():
            relation = calculate_synastry_relation(position1, position2)
            if relation == "Attraction":
                attraction_count += 1
            elif relation == "Tension":
                tension_count += 1
            else:
                neutral_count += 1
    
    # Determine the dominant relation
    if attraction_count > tension_count and attraction_count > neutral_count:
        return "Attraction"
    elif tension_count > attraction_count and tension_count > neutral_count:
        return "Tension"
    else:
        return "Neutral"

def get_synastry_description(result):
    """Generate a description based on the synastry result."""
    if result == "Attraction":
        return ("The synastry analysis shows a strong connection between the two users. "
                "This indicates a harmonious and positive relationship, where both individuals "
                "complement each other well, possibly sharing similar interests or emotional bonds.")
    elif result == "Tension":
        return ("The synastry analysis reveals potential challenges or conflicts between the two users. "
                "There may be disagreements, differing personalities, or unresolved issues that create tension.")
    else:
        return ("The synastry analysis suggests a neutral relationship. There may not be strong positive or negative "
                "connections between the two users. It’s likely that both individuals co-exist peacefully without "
                "intense emotional or intellectual interaction.")

# Function to calculate affection percentage deterministically (for the "ship" aspect)
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

# Slash command for shipping
@bot.tree.command(name="ship", description="Ship two users and see their affection percentage!")
async def ship(interaction: discord.Interaction, user1: discord.Member, user2: discord.Member):
    affection, meaning = calculate_affection(user1, user2)
    await interaction.response.send_message(
        f"💘 Shipping {user1.mention} and {user2.mention}...\n"
        f"**Affection: {affection}%**\n**Result: {meaning}**"
    )

# Slash command for astrological synastry
@bot.tree.command(name="astrological-synastry", description="Analyze astrological synastry between two users based on their birthdates!")
async def astrological_synastry(interaction: discord.Interaction, user1: discord.Member, dob1: str, user2: discord.Member, dob2: str):
    # Try to convert the date of birth into a datetime object
    try:
        dob1_parsed = datetime.strptime(dob1, "%Y-%m-%d")
        dob2_parsed = datetime.strptime(dob2, "%Y-%m-%d")
    except ValueError:
        await interaction.response.send_message("Please provide the date of birth in the correct format (YYYY-MM-DD).")
        return

    # Generate simplified charts for both users
    user1_chart = generate_simplified_chart(dob1)
    user2_chart = generate_simplified_chart(dob2)
    
    # Perform simplified synastry analysis
    synastry_result = analyze_simplified_synastry(user1_chart, user2_chart)
    
    # Get the description based on the synastry result
    synastry_description = get_synastry_description(synastry_result)
    
    # Calculate affection
    affection, meaning = calculate_affection(user1, user2)
    
    # Output the final astrological synastry result with affection
    await interaction.response.send_message(
        f"🌟 **Astrological Synastry Result** 🌟\n"
        f"💫 **Shipping {user1.mention} and {user2.mention}...**\n\n"
        f"**Synastry Result: {synastry_result}**\n"
        f"**Description:** {synastry_description}\n\n"
        f"❤️ **Affection: {affection}%**\n"
        f"**Affection Meaning: {meaning}**"
    )
@bot.event
async def on_message(message):
    # Ignore bot's own messages
    if message.author == bot.user:
        return

    # Check for --ship command
    if message.content.startswith('--ship'):
        # Split command and check mentions
        mentions = message.mentions
        
        if len(mentions) == 1:
            # If only one user is mentioned, ship the sender with that user
            user1, user2 = message.author, mentions[0]
        elif len(mentions) == 2:
            # If two users are mentioned, ship them together
            user1, user2 = mentions[0], mentions[1]
        else:
            # If the number of mentions is not 1 or 2, ask the user for correct input
            await message.channel.send("Please mention one or two users to ship, like `--ship @user1` or `--ship @user1 @user2`.")
            return

        affection, meaning = calculate_affection(user1, user2)

        # Send response for the ship
        await message.channel.send(
            f"💘 Shipping {user1.mention} and {user2.mention}...\n"
            f"**Affection: {affection}%**\n**Result: {meaning}**"
        )

    # Make sure to process commands after the on_message event
    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f'Bot logged in as {bot.user}')

# Run the bot
bot.run(TOKEN)
