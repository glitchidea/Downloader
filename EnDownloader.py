#!/usr/bin/env python3

import yt_dlp
import os
import json
import re
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
import stat

# Configuration file path
CONFIG_FILE = 'config.json' # path to config

# Default download path
DEFAULT_DOWNLOAD_PATH = os.path.join(os.path.expanduser("~"), "Downloads")

# Load settings or return default values
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            config = json.load(file)
            # Decode Unicode characters when loaded from JSON
            config['DOWNLOAD_PATH'] = bytes(config['DOWNLOAD_PATH'], 'utf-8').decode('unicode_escape')
            # Also expand ~ character
            config['DOWNLOAD_PATH'] = os.path.expanduser(config['DOWNLOAD_PATH'])
            return config
    else:
        return {'CLIENT_ID': '', 'CLIENT_SECRET': '', 'DOWNLOAD_PATH': DEFAULT_DOWNLOAD_PATH}

# Save settings
def save_config(config):
    # Expand the path while saving
    config['DOWNLOAD_PATH'] = os.path.expanduser(config['DOWNLOAD_PATH'])
    # Properly encode Unicode characters when writing to JSON
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file, indent=4, ensure_ascii=False)

# Establish Spotify API connection
def get_spotify_connection(client_id, client_secret):
    try:
        return spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))
    except spotipy.SpotifyException as e:
        print(f"Error connecting to Spotify API: {e}")
        return None

# Video/Audio downloader
def choose_download_type():
    while True:
        download_type = input("Select the type you want to download (video / audio) or 'q' to quit: ").strip().lower()
        if download_type in ['video', 'v']:
            return 'video'
        elif download_type in ['audio', 'a']:
            return 'audio'
        elif download_type == 'q':
            return 'q'
        else:
            print("Invalid option. Please enter 'video', 'audio', or 'q'.")

def choose_video_quality():
    while True:
        print("Video quality options:")
        print("1. 144p")
        print("2. 240p")
        print("3. 360p")
        print("4. 480p")
        print("5. 720p")
        print("6. 1080p")
        print("7. 4K")
        choice = input("Enter the number of the quality option you want to download (1-7) or 'q' to quit: ").strip().lower()
        if choice == '1':
            return 'bestvideo[height<=144]+bestaudio/best'
        elif choice == '2':
            return 'bestvideo[height<=240]+bestaudio/best'
        elif choice == '3':
            return 'bestvideo[height<=360]+bestaudio/best'
        elif choice == '4':
            return 'bestvideo[height<=480]+bestaudio/best'
        elif choice == '5':
            return 'bestvideo[height<=720]+bestaudio/best'
        elif choice == '6':
            return 'bestvideo[height<=1080]+bestaudio/best'
        elif choice == '7':
            return 'bestvideo[height<=2160]+bestaudio/best'
        elif choice == 'q':
            return None
        else:
            print("Invalid option. Please enter a valid option number or 'q'.")

def choose_audio_quality():
    while True:
        print("Audio quality options:")
        print("1. Best audio quality (320kbps)")
        print("2. Better audio quality (192kbps)")
        print("3. Good audio quality (128kbps)")
        choice = input("Enter the number of the audio quality option you want to download (1-3) or 'q' to quit: ").strip().lower()
        if choice == '1':
            return 'bestaudio/best'
        elif choice == '2':
            return 'bestaudio/best'
        elif choice == '3':
            return 'bestaudio/best'
        elif choice == 'q':
            return None
        else:
            print("Invalid option. Please enter a valid option number or 'q'.")

def download_media(url, quality, output_format):
    output_path = 'downloads'
    os.makedirs(output_path, exist_ok=True)

    ydl_opts = {
        'format': quality,
        'outtmpl': f'{output_path}/%(title)s.%(ext)s',
        'merge_output_format': output_format,
        'progress_hooks': [progress_hook],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except yt_dlp.DownloadError as e:
        print(f"An error occurred while downloading media: {e}")

def progress_hook(d):
    if d['status'] == 'finished':
        print('Download complete.')
    elif d['status'] == 'downloading':
        print(f'Downloading... Downloaded: {d["_percent_str"]} of {d["_total_bytes_str"]}')

# Get tracks from Spotify playlist
def get_playlist_tracks(sp, playlist_id):
    results = sp.playlist_tracks(playlist_id)
    tracks = results['items']
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    return tracks

# Sanitize file names from invalid characters
def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', filename)

# Download song from YouTube
def search_youtube_and_download(query, output_path):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_path,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f'ytsearch:{query}'])

# Download a single track
def download_single_track(sp):
    while True:
        track_name = input("Enter the song name (type 'q' to quit): ")
        if track_name.lower() == 'q':
            return
        artist_name = input("Enter the artist name (type 'q' to quit): ")
        if artist_name.lower() == 'q':
            return
        query = f"{track_name} {artist_name}"
        filename = f"{sanitize_filename(track_name)}-{sanitize_filename(artist_name)}.mp3"
        download_path = os.path.join(config['DOWNLOAD_PATH'], filename)
        print(f"Downloading: {query} as {filename}")
        search_youtube_and_download(query, download_path)
        print(f"Download complete: {filename}")

# Download playlist
def download_playlist(sp):
    while True:
        playlist_id = input("Enter the Spotify playlist ID (type 'q' to quit): ")
        if playlist_id.lower() == 'q':
            return
        tracks = get_playlist_tracks(sp, playlist_id)
        for track in tracks:
            track_name = track['track']['name']
            artist_name = track['track']['artists'][0]['name']
            query = f"{track_name} {artist_name}"
            filename = f"{sanitize_filename(track_name)}-{sanitize_filename(artist_name)}.mp3"
            download_path = os.path.join(config['DOWNLOAD_PATH'], filename)
            print(f"Downloading: {query} as {filename}")
            search_youtube_and_download(query, download_path)
            print(f"Download complete: {filename}")

# Update settings
def update_settings():
    global config
    print("\n--- Update Settings ---")
    
    client_id = input(f"Enter Spotify Client ID (current: {config['CLIENT_ID']}): ")
    if client_id:
        config['CLIENT_ID'] = client_id
    
    client_secret = input(f"Enter Spotify Client Secret (current: {config['CLIENT_SECRET']}): ")
    if client_secret:
        config['CLIENT_SECRET'] = client_secret
    
    download_path = input(f"Enter download path (current: {config['DOWNLOAD_PATH']}): ")
    if download_path:
        config['DOWNLOAD_PATH'] = download_path
    else:
        config['DOWNLOAD_PATH'] = DEFAULT_DOWNLOAD_PATH
    
    save_config(config)
    print("Settings updated successfully.")

# DOWNLOAD LIKED SONGS
def get_spotify_connection_liked():
    scope = "user-library-read"  # Required permission for user-specific data
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=config['CLIENT_ID'],
                                                  client_secret=config['CLIENT_SECRET'],
                                                  redirect_uri="http://localhost:8888/callback",
                                                  scope=scope))
    return sp

# Get liked songs
def get_liked_songs_liked(sp):
    results = sp.current_user_saved_tracks(limit=50)
    tracks = results['items']
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    return tracks

def download_liked_songs(sp):
    tracks = get_liked_songs_liked(sp)
    for track in tracks:
        track_name = track['track']['name']
        artist_name = track['track']['artists'][0]['name']
        query = f"{track_name} {artist_name}"
        filename = f"{sanitize_filename(track_name)}-{sanitize_filename(artist_name)}.mp3"
        download_path = os.path.join(config['DOWNLOAD_PATH'], filename)
        print(f"Downloading: {query} as {filename}")
        search_youtube_and_download(query, download_path)
        print(f"Download complete: {filename}")

# Permissions

def ensure_permissions(file_path):
    """ Checks file permissions and sets if necessary. """
    if not os.path.exists(file_path):
        print(f"{file_path} not found, creating...")
        open(file_path, 'w').close()  # Create the file

    # Check and fix file permissions
    permissions = os.stat(file_path).st_mode
    if not (permissions & stat.S_IWUSR):
        print(f"No write permission for {file_path}, setting...")
        os.chmod(file_path, permissions | stat.S_IWUSR)
    print(f"{file_path} permissions updated: {oct(os.stat(file_path).st_mode)}")

def create_cache_file(cache_path=".cache"):
    """ Creates the token cache file and sets permissions. """
    if not os.path.exists(cache_path):
        print(f"{cache_path} not found, creating...")
        open(cache_path, 'w').close()  # Create the file

    # Check and fix file permissions
    permissions = os.stat(cache_path).st_mode
    if not (permissions & stat.S_IWUSR):
        print(f"No write permission for {cache_path}, setting...")
        os.chmod(cache_path, permissions | stat.S_IWUSR)
    print(f"{cache_path} permissions updated: {oct(os.stat(cache_path).st_mode)}")

# Main menu
def main_menu():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n--- Main Menu ---")
        print("1. Video/Audio Downloader")
        print("2. Spotify Downloader")
        print("3. Download Liked Songs from Spotify")
        print("4. Update Settings")
        print("Q. Exit")

        choice = input("Choose an option: ").strip().upper()

        try:
            if choice == '1':
                download_type = choose_download_type()
                if not download_type:
                    print("Exiting the program.")
                    exit()

                if download_type == 'video':
                    quality = choose_video_quality()
                    if not quality:
                        print("Exiting the program.")
                        exit()

                    output_format = input("Select download format (e.g., mp4, mkv, webm): ").strip()
                    video_url = input("Enter the URL of the video or audio you want to download: ").strip()
                    download_media(video_url, quality, output_format)

                elif download_type == 'audio':
                    quality = choose_audio_quality()
                    if not quality:
                        print("Exiting the program.")
                        exit()

                    output_format = 'mp3'
                    video_url = input("Enter the URL of the video or audio you want to download: ").strip()
                    download_media(video_url, quality, output_format)

            elif choice == '2':
                if not config['CLIENT_ID'] or not config['CLIENT_SECRET']:
                    print("Please set the API credentials first.")
                    update_settings()
                else:
                    sp = get_spotify_connection(config['CLIENT_ID'], config['CLIENT_SECRET'])
                    if sp:
                        action = input("1. Download Single Track\n2. Download Playlist\nOption: ").strip()
                        if action == '1':
                            download_single_track(sp)
                        elif action == '2':
                            download_playlist(sp)
                        else:
                            print("Invalid selection.")

            elif choice == '3':
                sp = get_spotify_connection_liked()
                if sp:
                    download_liked_songs(sp)

            elif choice == '4':
                update_settings()
            elif choice == 'Q':
                print("Exiting...")
                break
            else:
                print("Invalid selection, please try again.")
        except Exception as e:
            print(f"An error occurred: {e}")

# Main execution
if __name__ == '__main__':
    config = load_config()
    main_menu()
