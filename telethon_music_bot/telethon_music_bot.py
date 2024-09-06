
from telethon import TelegramClient, events
from telethon.tl.functions.phone import CreateGroupCallRequest, JoinGroupCallRequest
import yt_dlp
import subprocess
import os
from config import API_ID, API_HASH, STRING_SESSION

# Initialize the Telethon client using the string session
client = TelegramClient("music_bot", API_ID, API_HASH, session=STRING_SESSION)

# Function to join a voice chat in a group
async def join_vc(event):
    try:
        chat_id = event.chat_id
        print(f"Joining voice chat for chat ID: {chat_id}")

        # Create or join the group voice chat
        await client(CreateGroupCallRequest(peer=chat_id))
        await event.reply("Bot has joined the voice chat!")
    
    except Exception as e:
        print(f"Error joining voice chat: {e}")
        await event.reply(f"Error joining voice chat: {str(e)}")

# Function to download and play a song from YouTube in the voice chat
async def play_song(event, song_name):
    chat_id = event.chat_id

    # Set up yt-dlp options to bypass CAPTCHA and download the song
    ydl_opts = {
        'format': 'bestaudio',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True,
        'noplaylist': True,
        'extract_flat': 'in_playlist',  # Bypass CAPTCHA for playlists
        'cookies': 'cookies.txt'  # Use cookies to bypass CAPTCHA
    }

    try:
        # Search for the song on YouTube and download it
        video_url = await search_youtube(song_name)
        if not video_url:
            await event.reply("Song not found on YouTube.")
            return

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            audio_file = ydl.prepare_filename(info).replace(".webm", ".mp3")

        # Play the downloaded audio file in the voice chat
        await play_in_voice_chat(chat_id, audio_file)

    except Exception as e:
        print(f"Error playing song: {e}")
        await event.reply(f"Error playing song: {str(e)}")

# Function to search YouTube using yt-dlp
async def search_youtube(query):
    ydl_opts = {
        'default_search': 'ytsearch',
        'quiet': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        if 'entries' in info and info['entries']:
            return info['entries'][0]['webpage_url']

    return None

# Function to stream the audio in the voice chat using FFmpeg
async def play_in_voice_chat(chat_id, audio_file):
    process = subprocess.Popen(
        ['ffmpeg', '-re', '-i', audio_file, '-f', 's16le', '-ac', '2', '-ar', '48000', '-'],
        stdout=subprocess.PIPE
    )

    try:
        # Stream the audio file to the voice chat
        print(f"Playing audio in voice chat for chat ID: {chat_id}")
        await client(JoinGroupCallRequest(chat_id, audio_file=process.stdout))

        # Wait until the audio stream is finished
        while True:
            output = process.stdout.read(1024)
            if not output:
                break

    finally:
        # Cleanup after playback
        os.remove(audio_file)

# Event handler for the "/join" command
@client.on(events.NewMessage(pattern='/join'))
async def handler_join_vc(event):
    await join_vc(event)

# Event handler for the "/play" command
@client.on(events.NewMessage(pattern='/play (.+)'))
async def handler_play_song(event):
    song_name = event.pattern_match.group(1)
    await play_song(event, song_name)

# Start the client
print("Starting bot...")
client.start()
client.run_until_disconnected()
