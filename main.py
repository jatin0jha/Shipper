from dotenv import load_dotenv
import os
import discord
import hashlib  # For deterministic hashing

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TOKEN')

if not TOKEN:
    raise ValueError("TOKEN environment variable is not set.")

# Define intents
intents = discord.Intents.default()
intents.message_content = True

# Initialize the client
client = discord.Client(intents=intents)

# Function to calculate affection percentage deterministically
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

@client.event
async def on_ready():
    print(f'Bot logged in as {client.user}')

@client.event
async def on_message(message):
    # Ignore bot's own messages
    if message.author == client.user:
        return

    # Check for `--ship` command
    if message.content.startswith('--ship'):
        # Split command and check if it has two mentions
        mentions = message.mentions
        if len(mentions) != 2:
            await message.channel.send("Please mention two users to ship, like `--ship @user1 @user2`.")
            return

        user1, user2 = mentions[0], mentions[1]
        affection, meaning = calculate_affection(user1, user2)

        # Send response
        await message.channel.send(
            f"💘 Shipping {user1.mention} and {user2.mention}...\n"
            f"**Affection: {affection}%**\n**Result: {meaning}**"
        )

# Run the bot
client.run(TOKEN)
