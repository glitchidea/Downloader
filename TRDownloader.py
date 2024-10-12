#!/usr/bin/env python3

import yt_dlp
import os
import json
import re
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
import stat




# Ayar dosyası yolu
CONFIG_FILE = 'config.json' #Dosya yolu

# Varsayılan indirme yolu
DEFAULT_DOWNLOAD_PATH = os.path.join(os.path.expanduser("~"), "Downloads")

# Ayarları oku veya varsayılan değerleri döndür
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            config = json.load(file)
            # JSON'dan yüklendiğinde yoldaki Unicode karakterlerini çöz
            config['DOWNLOAD_PATH'] = bytes(config['DOWNLOAD_PATH'], 'utf-8').decode('unicode_escape')
            # Ayrıca ~ karakterini genişlet
            config['DOWNLOAD_PATH'] = os.path.expanduser(config['DOWNLOAD_PATH'])
            return config
    else:
        return {'CLIENT_ID': '', 'CLIENT_SECRET': '', 'DOWNLOAD_PATH': DEFAULT_DOWNLOAD_PATH}

# Ayarları kaydet
def save_config(config):
    # Yolu genişletirken ve kaydederken ~ karakterini genişlet
    config['DOWNLOAD_PATH'] = os.path.expanduser(config['DOWNLOAD_PATH'])
    # JSON'a yazarken Unicode karakterleri düzgün şekilde kodla
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file, indent=4, ensure_ascii=False)

# Spotify API bağlantısını kur
def get_spotify_connection(client_id, client_secret):
    try:
        return spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))
    except spotipy.SpotifyException as e:
        print(f"Spotify API'ye bağlanırken bir hata oluştu: {e}")
        return None
# Video/Ses indirici
def choose_download_type():
    while True:
        download_type = input("İndirmek istediğiniz türü seçin (video / ses) veya 'q' ile çıkış yapın: ").strip().lower()
        if download_type in ['video', 'v']:
            return 'video'
        elif download_type in ['ses', 's']:
            return 'ses'
        elif download_type == 'q':
            return 'q'
        else:
            print("Geçersiz seçenek. Lütfen 'video', 'ses' veya 'q' girin.")

def choose_video_quality():
    while True:
        print("Video kalitesi seçenekleri:")
        print("1. 144p")
        print("2. 240p")
        print("3. 360p")
        print("4. 480p")
        print("5. 720p")
        print("6. 1080p")
        print("7. 4K")
        choice = input("İndirmek istediğiniz kalite seçeneğinin numarasını girin (1-7) veya 'q' ile çıkış yapın: ").strip().lower()
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
            print("Geçersiz seçenek. Lütfen geçerli bir seçenek numarası veya 'q' girin.")

def choose_audio_quality():
    while True:
        print("Ses kalitesi seçenekleri:")
        print("1. En iyi ses kalitesi (320kbps)")
        print("2. Daha iyi ses kalitesi (192kbps)")
        print("3. İyi ses kalitesi (128kbps)")
        choice = input("İndirmek istediğiniz ses kalitesi seçeneğinin numarasını girin (1-3) veya 'q' ile çıkış yapın: ").strip().lower()
        if choice == '1':
            return 'bestaudio/best'
        elif choice == '2':
            return 'bestaudio/best'
        elif choice == '3':
            return 'bestaudio/best'
        elif choice == 'q':
            return None
        else:
            print("Geçersiz seçenek. Lütfen geçerli bir seçenek numarası veya 'q' girin.")

def download_media(url, quality, output_format):
    output_path = 'indirilenler'
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
        print(f"Medya indirilirken bir hata oluştu: {e}")

def progress_hook(d):
    if d['status'] == 'finished':
        print('İndirme tamamlandı.')
    elif d['status'] == 'downloading':
        print(f'İndiriliyor... İndirilen: {d["_percent_str"]} of {d["_total_bytes_str"]}')

# Spotify çalma listesindeki şarkıları al
def get_playlist_tracks(sp, playlist_id):
    results = sp.playlist_tracks(playlist_id)
    tracks = results['items']
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    return tracks

# Dosya adlarını geçersiz karakterlerden temizle
def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', filename)

# Şarkıyı YouTube'dan indir
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

# Tek tek şarkı indirme
def download_single_track(sp):
    while True:
        track_name = input("Şarkı adını girin (çıkmak için 'q' yazın): ")
        if track_name.lower() == 'q':
            return
        artist_name = input("Sanatçı adını girin (çıkmak için 'q' yazın): ")
        if artist_name.lower() == 'q':
            return
        query = f"{track_name} {artist_name}"
        filename = f"{sanitize_filename(track_name)}-{sanitize_filename(artist_name)}.mp3"
        download_path = os.path.join(config['DOWNLOAD_PATH'], filename)
        print(f"İndiriliyor: {query} olarak {filename}")
        search_youtube_and_download(query, download_path)
        print(f"İndirme tamamlandı: {filename}")

# Çalma listesi indirme
def download_playlist(sp):
    while True:
        playlist_id = input("Spotify çalma listesi ID'sini girin (çıkmak için 'q' yazın): ")
        if playlist_id.lower() == 'q':
            return
        tracks = get_playlist_tracks(sp, playlist_id)
        for track in tracks:
            track_name = track['track']['name']
            artist_name = track['track']['artists'][0]['name']
            query = f"{track_name} {artist_name}"
            filename = f"{sanitize_filename(track_name)}-{sanitize_filename(artist_name)}.mp3"
            download_path = os.path.join(config['DOWNLOAD_PATH'], filename)
            print(f"İndiriliyor: {query} olarak {filename}")
            search_youtube_and_download(query, download_path)
            print(f"İndirme tamamlandı: {filename}")

# Ayarları güncelle
def update_settings():
    global config
    print("\n--- Ayarları Güncelle ---")
    
    client_id = input(f"Spotify Client ID'sini girin (mevcut: {config['CLIENT_ID']}): ")
    if client_id:
        config['CLIENT_ID'] = client_id
    
    client_secret = input(f"Spotify Client Secret'ı girin (mevcut: {config['CLIENT_SECRET']}): ")
    if client_secret:
        config['CLIENT_SECRET'] = client_secret
    
    download_path = input(f"İndirme yolunu girin (mevcut: {config['DOWNLOAD_PATH']}): ")
    if download_path:
        config['DOWNLOAD_PATH'] = download_path
    else:
        config['DOWNLOAD_PATH'] = DEFAULT_DOWNLOAD_PATH
    
    save_config(config)
    print("Ayarlar başarıyla güncellendi.")



#BEĞENİLENLERİ İNDİR
def get_spotify_connection_liked():
    scope = "user-library-read"  # Kullanıcıya özgü veriler için gerekli izin
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=config['CLIENT_ID'],
                                                  client_secret=config['CLIENT_SECRET'],
                                                  redirect_uri="http://localhost:8888/callback",
                                                  scope=scope))
    return sp

# Beğenilen şarkıları al
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
        print(f"İndiriliyor: {query} olarak {filename}")
        search_youtube_and_download(query, download_path)
        print(f"İndirme tamamlandı: {filename}")


#İzinler

def ensure_permissions(file_path):
    """ Dosya izinlerini kontrol eder ve gerekirse ayarlar. """
    if not os.path.exists(file_path):
        print(f"{file_path} bulunamadı, oluşturuluyor...")
        open(file_path, 'w').close()  # Dosyayı oluştur

    # Dosya izinlerini kontrol et ve düzelt
    permissions = os.stat(file_path).st_mode
    if not (permissions & stat.S_IWUSR):
        print(f"{file_path} yazma izni yok, ayarlanıyor...")
        os.chmod(file_path, permissions | stat.S_IWUSR)
    print(f"{file_path} izinler güncellendi: {oct(os.stat(file_path).st_mode)}")

def create_cache_file(cache_path=".cache"):
    """ Token önbellek dosyasını oluşturur ve izinlerini ayarlar. """
    if not os.path.exists(cache_path):
        print(f"{cache_path} bulunamadı, oluşturuluyor...")
        open(cache_path, 'w').close()  # Dosyayı oluştur

    # Dosya izinlerini kontrol et ve düzelt
    permissions = os.stat(cache_path).st_mode
    if not (permissions & stat.S_IWUSR):
        print(f"{cache_path} yazma izni yok, ayarlanıyor...")
        os.chmod(cache_path, permissions | stat.S_IWUSR)
    print(f"{cache_path} izinler güncellendi: {oct(os.stat(cache_path).st_mode)}")


# Ana menü
def main_menu():
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n--- Ana Menü ---")
        print("1. Video/Ses İndirici")
        print("2. Spotify İndirici")
        print("3. Spotify Beğenilen Şarkıları İndir")
        print("4. Ayarları Güncelle")
        print("Q. Çıkış")

        choice = input("Bir seçenek seçin: ").strip().upper()

        try:
            if choice == '1':
                download_type = choose_download_type()
                if not download_type:
                    print("Programdan çıkılıyor.")
                    exit()

                if download_type == 'video':
                    quality = choose_video_quality()
                    if not quality:
                        print("Programdan çıkılıyor.")
                        exit()

                    output_format = input("İndirme formatını seçin (örn. mp4, mkv, webm): ").strip()
                    video_url = input("İndirmek istediğiniz video veya ses URL'sini girin: ").strip()
                    download_media(video_url, quality, output_format)

                elif download_type == 'ses':
                    quality = choose_audio_quality()
                    if not quality:
                        print("Programdan çıkılıyor.")
                        exit()

                    output_format = 'mp3'
                    video_url = input("İndirmek istediğiniz video veya ses URL'sini girin: ").strip()
                    download_media(video_url, quality, output_format)

            elif choice == '2':
                if not config['CLIENT_ID'] or not config['CLIENT_SECRET']:
                    print("Lütfen önce API kimlik bilgilerini ayarlayın.")
                    update_settings()
                else:
                    sp = get_spotify_connection(config['CLIENT_ID'], config['CLIENT_SECRET'])
                    if sp:
                        action = input("1. Tek Şarkı İndir\n2. Çalma Listesi İndir\nSeçenek: ").strip()
                        if action == '1':
                            download_single_track(sp)
                        elif action == '2':
                            download_playlist(sp)
                        else:
                            print("Geçersiz seçim.")

            elif choice == '3':
                sp = get_spotify_connection_liked()
                if sp:
                    download_liked_songs(sp)

            elif choice == '4':
                update_settings()
            elif choice == 'Q':
                print("Çıkılıyor...")
                break
            else:
                print("Geçersiz seçim, lütfen tekrar deneyin.")
        except Exception as e:
            print(f"Bir hata oluştu: {e}")

# Ana işlem
if __name__ == '__main__':
    config = load_config()
    main_menu()
