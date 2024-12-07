require('dotenv').config(); // Load environment variables
const { Client, GatewayIntentBits, EmbedBuilder, AttachmentBuilder } = require('discord.js');
const { createCanvas, loadImage } = require('canvas');
const crypto = require('crypto');
const axios = require('axios');
const fs = require('fs'); // For saving prefixes persistently

// Default prefix
const defaultPrefix = '--';

// Load prefixes from file
let prefixes = {};
try {
    prefixes = JSON.parse(fs.readFileSync('prefixes.json', 'utf8'));
} catch (err) {
    console.log('No existing prefixes found. Using default.');
}

// Save prefixes to file
function savePrefixes() {
    fs.writeFileSync('prefixes.json', JSON.stringify(prefixes, null, 2));
}

// Zodiac compatibility chart
const compatibilityChart = {
    Aries: { Leo: 90, Sagittarius: 85, Gemini: 80 },
    Taurus: { Virgo: 88, Capricorn: 85, Cancer: 80 },
    Gemini: { Libra: 90, Aquarius: 85, Aries: 80 },
    Cancer: { Scorpio: 90, Pisces: 85, Taurus: 80 },
    Leo: { Aries: 90, Sagittarius: 85, Gemini: 80 },
    Virgo: { Taurus: 88, Capricorn: 85, Pisces: 80 },
    Libra: { Gemini: 90, Aquarius: 85, Leo: 80 },
    Scorpio: { Cancer: 90, Pisces: 85, Virgo: 80 },
    Sagittarius: { Aries: 90, Leo: 85, Aquarius: 80 },
    Capricorn: { Taurus: 88, Virgo: 85, Scorpio: 80 },
    Aquarius: { Gemini: 90, Libra: 85, Sagittarius: 80 },
    Pisces: { Cancer: 90, Scorpio: 85, Taurus: 80, Virgo: 80 }
};

// Zodiac sign calculator based on date of birth (DOB)
function getZodiacSign(day, month) {
    const signs = [
        "Capricorn", "Aquarius", "Pisces", "Aries", "Taurus", "Gemini",
        "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius"
    ];
    const dates = [20, 19, 20, 20, 21, 21, 22, 22, 22, 23, 22, 21];
    return day > dates[month - 1] ? signs[month] : signs[month - 1];
}

// Create a new client instance
const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent
    ]
});

// Helper function: Calculate affection percentage and result meaning
function calculateAffection(user1, user2) {
    const combined = `${user1.username.toLowerCase()}_${user2.username.toLowerCase()}`;
    const hash = crypto.createHash('sha256').update(combined).digest('hex');
    const affection = parseInt(hash, 16) % 101; // Normalize to 0-100

    let meaning;
    if (affection === 100) meaning = 'Soulmates! ❤️';
    else if (affection >= 80) meaning = 'Perfect Match! 💕';
    else if (affection === 69) meaning = '( ¬ᴗ¬)';
    else if (affection >= 60) meaning = 'Great Chemistry! 😊';
    else if (affection >= 40) meaning = 'Good Friends! 🤝';
    else if (affection >= 20) meaning = 'Just Acquaintances. 🤔';
    else if (affection > 0) meaning = 'Not Really Compatible. 😕';
    else meaning = 'Arch Nemesis! ⚔️';

    return { affection, meaning };
}

// Helper function: Create a shipping image
async function generateShipImage(user1, user2, affection) {
    try {
        const avatar1URL = user1.displayAvatarURL({ extension: 'png', size: 256 });
        const avatar2URL = user2.displayAvatarURL({ extension: 'png', size: 256 });

        const [avatar1Response, avatar2Response] = await Promise.all([
            axios.get(avatar1URL, { responseType: 'arraybuffer' }),
            axios.get(avatar2URL, { responseType: 'arraybuffer' })
        ]);

        const avatar1 = await loadImage(Buffer.from(avatar1Response.data));
        const avatar2 = await loadImage(Buffer.from(avatar2Response.data));
        const heart = await loadImage(affection >= 50 ? 'heart.png' : 'broken_heart.png');

        const canvas = createCanvas(500, 200);
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        ctx.save();
        ctx.beginPath();
        ctx.arc(100, 100, 75, 0, Math.PI * 2, true);
        ctx.closePath();
        ctx.clip();
        ctx.drawImage(avatar1, 25, 25, 150, 150);
        ctx.restore();

        ctx.save();
        ctx.beginPath();
        ctx.arc(400, 100, 75, 0, Math.PI * 2, true);
        ctx.closePath();
        ctx.clip();
        ctx.drawImage(avatar2, 325, 25, 150, 150);
        ctx.restore();

        ctx.drawImage(heart, (canvas.width - 75) / 2, (canvas.height - 75) / 2, 75, 75);

        return canvas.toBuffer();
    } catch (error) {
        console.error('Error generating shipping image:', error);
        throw new Error('Failed to generate shipping image.');
    }
}

// Slash command handler
client.on('interactionCreate', async interaction => {
    if (!interaction.isCommand()) return;

    if (interaction.commandName === 'ship') {
        const user1 = interaction.options.getUser('user1');
        const user2 = interaction.options.getUser('user2');
        const { affection, meaning } = calculateAffection(user1, user2);

        const imageBuffer = await generateShipImage(user1, user2, affection);
        const attachment = new AttachmentBuilder(imageBuffer, { name: 'ship.png' });

        const embed = new EmbedBuilder()
            .setTitle('💘 Shipping Results')
            .setColor('#9B59B6')
            .addFields(
                { name: 'Affection', value: `${affection}%`, inline: true },
                { name: 'Result', value: meaning, inline: true }
            )
            .setImage('attachment://ship.png');

        await interaction.reply({ embeds: [embed], files: [attachment] });
    } 
    
    else if (interaction.commandName === 'prefix') {
        const newPrefix = interaction.options.getString('new_prefix');
        prefixes[interaction.guildId] = newPrefix;
        savePrefixes();
        await interaction.reply(`Prefix updated to: \`${newPrefix}\``);
    }
});

// Message command handler
client.on('messageCreate', async message => {
    if (message.author.bot) return;

    const prefix = prefixes[message.guild.id] || defaultPrefix;

    if (!message.content.startsWith(prefix)) return;

    const args = message.content.slice(prefix.length).trim().split(/ +/);
    const command = args.shift().toLowerCase();

    if (command === 'ship') {
        const mentions = message.mentions.users;
        if (mentions.size < 1 || mentions.size > 2) {
            await message.reply(`Please mention one or two users to ship, like \`${prefix}ship @user1\` or \`${prefix}ship @user1 @user2\`.`);
            return;
        }
        
        const [user1, user2] = mentions.size === 1 ? [message.author, mentions.first()] : [...mentions.values()];        
        const { affection, meaning } = calculateAffection(user1, user2);

        const imageBuffer = await generateShipImage(user1, user2, affection);
        const attachment = new AttachmentBuilder(imageBuffer, { name: 'ship.png' });

        const embed = new EmbedBuilder()
            .setTitle('💘 Shipping Results')
            .setColor('#9B59B6')
            .addFields(
                { name: 'Affection', value: `${affection}%`, inline: true },
                { name: 'Result', value: meaning, inline: true }
            )
            .setImage('attachment://ship.png');

        await message.reply({ embeds: [embed], files: [attachment] });
    }

    if (message.content.startsWith('--kundli')) {
        const mentions = message.mentions.users;
        if (mentions.size < 2) {
            await message.reply('Please mention two users to match their Kundli (e.g., `--kundli @user1 @user2`).');
            return;
        }

        const [user1, user2] = mentions.size === 1 ? [message.author, mentions.first()] : [...mentions.values()];

        // Ask for birthdates of the users
        await message.reply(`Please provide the date of birth (DD/MM/YYYY) of ${user1.username}.`);
        
        // Wait for the first user's DOB
        const user1DOB = await getDOB(message, user1);
        if (!user1DOB) return;

        await message.reply(`Please provide the date of birth (DD/MM/YYYY) of ${user2.username}.`);
        
        // Wait for the second user's DOB
        const user2DOB = await getDOB(message, user2);
        if (!user2DOB) return;

        // Parse the DOBs and calculate zodiac signs
        const [user1Day, user1Month] = user1DOB.split('/').map(Number);
        const [user2Day, user2Month] = user2DOB.split('/').map(Number);

        const user1Zodiac = getZodiacSign(user1Day, user1Month);
        const user2Zodiac = getZodiacSign(user2Day, user2Month);

        // Get the compatibility percentage
        const compatibility = compatibilityChart[user1Zodiac]?.[user2Zodiac] || 50; // Default to 50% if no match

        // Create a reply with zodiac signs and compatibility
        const embed = new EmbedBuilder()
            .setTitle('🌟 Kundli Match Results 🌟')
            .setColor('#ffcc00')
            .addFields(
                { name: `${user1.username}'s Zodiac`, value: user1Zodiac, inline: true },
                { name: `${user2.username}'s Zodiac`, value: user2Zodiac, inline: true },
                { name: 'Compatibility', value: `${compatibility}%`, inline: false }
            )
            .setDescription(`${user1.username} and ${user2.username}'s zodiac compatibility is **${compatibility}%**!`);

        await message.reply({ embeds: [embed] });
    }
});

// Helper function to prompt user for DOB and validate
async function getDOB(message, user) {
    const filter = response => response.author.id === message.author.id;

    // Wait for a response for the DOB
    const collected = await message.channel.awaitMessages({
        filter,
        max: 1,
        time: 30000,
        errors: ['time']
    }).catch(() => {
        message.reply(`You took too long to respond with ${user.username}'s DOB. Please try again.`);
        return null;
    });

    const dob = collected.first().content;
    if (!dob.match(/^\d{2}\/\d{2}\/\d{4}$/)) {
        message.reply(`Invalid DOB format! Please provide in the format DD/MM/YYYY.`);
        return null;
    }
    return dob;
}

// Error handling: Log errors and prevent the bot from stopping
const logErrorToFile = (error) => {
    const logMessage = `${new Date().toISOString()} - ERROR: ${error.stack || error.message}\n`;
    fs.appendFileSync('error_logs.txt', logMessage);
};

// Handle uncaught exceptions (synchronous errors)
process.on('uncaughtException', (err, origin) => {
    console.error(`Uncaught Exception: ${err.message}`);
    logErrorToFile(err);
});

// Handle unhandled promise rejections (asynchronous errors)
process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled Promise Rejection at:', promise, 'reason:', reason);
    logErrorToFile(reason);
});

// Discord.js error logging
client.on('error', (error) => {
    console.error('Discord.js error:', error);
    logErrorToFile(error);
});


// Login to Discord
client.login(process.env.TOKEN);
