import discord
from discord.ext import commands
import yt_dlp
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent

bot = commands.Bot(command_prefix="!", intents=intents)

# The queue to store the song URLs
song_queue = []

# Connect to voice channel
async def connect_to_voice_channel(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        voice_channel = await channel.connect()
        return voice_channel
    else:
        await ctx.send("You need to join a voice channel first.")
        return None

# Play the next song in the queue
async def play_next(ctx, voice_channel):
    if song_queue:
        song_title, song_url = song_queue.pop(0)  # Get the first song from the queue
        await ctx.send(f"Now Playing: {song_title} 🎵")
        await play_song(ctx, voice_channel, song_url)
    else:
        await ctx.send("Song queue empty!")

# Play a song
async def play_song(ctx, voice_channel, song_url):
    voice_channel.play(discord.FFmpegPCMAudio(song_url))  # Play the song
    voice_channel.source = discord.PCMVolumeTransformer(voice_channel.source)
    voice_channel.source.volume = 0.5

    # Wait for the song to finish and then play the next one
    while voice_channel.is_playing():
        await asyncio.sleep(1)
    await play_next(ctx, voice_channel)

async def search_youtube(query):
    ydl_opts = {
        'format': 'bestaudio/best',  # Download the best audio format
        'noplaylist': True,          # Don't download a playlist, just the first result
        'quiet': True,               # Suppress output
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
        song_url = info['url']  # URL of the song
        song_title = info['title']  # Title of the song
        return song_title, song_url  # Return both title and URL

# Add a song to the queue
@bot.command()
async def play(ctx, *, song_query):
    # Check if the bot is connected to a voice channel
    if ctx.voice_client is None:
        voice_channel = await connect_to_voice_channel(ctx)
        if voice_channel is None:
            return  # Exit if there's no voice channel to join
    
    # Call the updated search_youtube function to get the song title and URL
    song_title, song_url = await search_youtube(song_query)
    
    # If the bot is not already playing, start playing the song, else append to queue
    if not ctx.voice_client.is_playing():
        await ctx.send(f"Now Playing: {song_title} 🎵")
        await play_song(ctx, ctx.voice_client, song_url)
    else:
        # Send a message to the channel with the song name
        await ctx.send(f"Added to queue: {song_title} 🎵")
        song_queue.append((song_title, song_url))

# Queue command to show the current queue
@bot.command()
async def queue(ctx):
    if len(song_queue) > 0:
        queue_message = "Current Song Queue:\n"
        for idx, (title, url) in enumerate(song_queue, start=1):
            queue_message += f"{idx}. {title} - {url}\n"
        await ctx.send(queue_message)
    else:
        await ctx.send("The queue is empty.")

# Skip command to skip the current song
@bot.command()
async def skip(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()  # Stop the current song
        await ctx.send("Song skipped.")
        
        voice_channel = ctx.voice_client
        await play_next(ctx, voice_channel)  # Play the next song
    else:
        await ctx.send("No song is currently playing.")

bot.run(TOKEN)

