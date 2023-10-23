import urllib3
import json
import os
import random
import string
import urllib.parse
import requests
import numpy as np

from database import *

TG_TOKEN = os.environ.get('BOT_TOKEN') 
URL = f"https://api.telegram.org/bot{TG_TOKEN}/"
http = urllib3.PoolManager()

# Основной функционал
def send_message(text, chat_id):
    final_text = text
    url = URL + f"sendMessage?text={final_text}&chat_id={chat_id}&parse_mode=html&disable_web_page_preview=True"
    http.request("GET", url)
    
def get_random_songs(artist):
    # Собираем 5 случайных песен исполнителя
    api_last = os.environ.get('MUSIC_TOKEN')
    url = f"http://ws.audioscrobbler.com/2.0/?method=artist.gettoptracks&artist={artist}&api_key={api_last}&format=json"
    response = http.request("GET", url)
    data = json.loads(response.data.decode('utf-8'))
    tracks = data['toptracks']['track']
    random_songs = random.sample(tracks, 5) # выбираем 5 случайных песен из списка без повторений
    random_songs_info = []
    # Вытаскиваем информацию о песнях
    for song in random_songs:
        song_name = song['name']
        artist_name = song['artist']['name']
        url = f"http://ws.audioscrobbler.com/2.0/?method=track.getInfo&api_key={api_last}&artist={artist_name}&track={song_name}&format=json"
        response = http.request("GET", url)
        data = json.loads(response.data.decode('utf-8'))
        track_info = data['track']
        url = urllib.parse.quote_plus(track_info['url'])
        random_songs_info.append((song_name, url))
    return random_songs_info

def get_artist_info(artist):
    api_last = os.environ.get('MUSIC_TOKEN')
    url = f"http://ws.audioscrobbler.com/2.0/?method=artist.getinfo&artist={artist}&api_key={api_last}&format=json&lang=ru"
    response = http.request("GET", url)
    data = json.loads(response.data.decode('utf-8'))
    artist_info = data['artist']['bio']['summary']
    # заменяем <a href на "ссылка на статью:"
    artist_info = artist_info.replace("<a href", "\n\nИнтересно? Продолжи чтение здесь")
    artist_info = artist_info.replace(">Read more on Last.fm</a>", " ")
    artist_info = artist_info.replace('"', '')
    artist_info = artist_info.replace(":=", " – ")
    artist_info = artist_info.replace("=", " – ")
    artist_info = urllib.parse.quote_plus(artist_info)
    return artist_info

def get_genre_songs(genre_reply):
    insert_genres("genres", genre_reply)
    api_last = os.environ.get('MUSIC_TOKEN')
    url = f"http://ws.audioscrobbler.com/2.0/?method=tag.gettopartists&tag={genre_reply}&api_key={api_last}&format=json"
    response = http.request("GET", url)
    data = json.loads(response.data)
    artists = data['topartists']['artist']
    top_artists = [f"{i+1}. {artist['name']} - {urllib.parse.quote_plus(artist['url'])}\n" for i, artist in enumerate(artists[:5])]
    return top_artists

def get_similar_artists(artist_name):
    api_key = os.environ.get('MUSIC_TOKEN')
    url = f"http://ws.audioscrobbler.com/2.0/?method=artist.getsimilar&artist={artist_name}&api_key={api_key}&format=json"
    response = requests.get(url)
    data = json.loads(response.text)
    if 'similarartists' in data and 'artist' in data['similarartists']:
        return [(artist['name'], urllib.parse.quote_plus(artist['url'])) for artist in data['similarartists']['artist']]
    else:
        return []

def get_similar_tracks(artist_name, track_name):
    api_key = os.environ.get('MUSIC_TOKEN')
    url = f"http://ws.audioscrobbler.com/2.0/?method=track.getsimilar&artist={artist_name}&track={track_name}&api_key={api_key}&format=json"
    response = requests.get(url)
    if response.status_code == 200:
        data = json.loads(response.content)
        if 'similartracks' in data and 'track' in data['similartracks']:
            tracks = data['similartracks']['track']
            return [f"<a href='{urllib.parse.quote_plus(track['url'])}'>{track['name']} - {track['artist']['name']}</a>\n" for track in tracks[:5]]
        else:
            return []
    else:
        return []

def explore_handler(artist, chat_id):
    insert_artists("artists", artist)
    random_songs_info = get_random_songs(artist)
    artist_info = get_artist_info(artist)
    songs_list = []
    for i, song_info in enumerate(random_songs_info, 1):
        song_name = song_info[0]
        url = song_info[1]
        songs_list.append(f"{i}. <a href='{url}'>{song_name}</a>")
    songs_list = "\n".join(songs_list)
    send_message(f"Конечно, вот, чем я могу поделиться 👇\n\n🎸 Об исполнителе:\n\n{artist_info}\n\n🚀 Подборка песен исполнителя {artist}:\n\n{songs_list}", chat_id)

def handler(event, context):

    message = json.loads(event['body'])
    chat_id = message['message']['chat']['id']
    reply = message['message']['text']

    if reply == "/start":
        start_message = "Привет! Я музыкальный бот, работающий на базе сервиса Last.fm и помогающий пользователям узнавать новое о музыкальном мире. Вот какие команды я умею выполнять:\n\n/start – пришлю краткое описание своего функционала 🤖\n\n/explore – расскажу несколько фактов о музыкальном исполнителе и пришлю подборку его композиций. Пример использования: /explore Hurts 🎧\n\n/genre – пришлю топ-5 исполнителей в интересующем тебя жанре/категории. Пример использования: /genre pop 🔠\n\n/recommendArtists – посоветую исполнителей, похожих на твоего любимчика. Пример использования: /recommendArtists Sia 📝\n\n/similarSongs - пришлю список песен похожих, на заданный трек исполнителя. Пример использования: /similarSongs Hurts - Wonderful Life 🎶"
        send_message(start_message, chat_id)

    elif reply.startswith("/explore"):
        artist = reply.split("/explore ", 1)
        if len(artist) < 2:
            send_message("Укажи название исполнителя после команды /explore. Например, /explore The Beatles", chat_id)
        else:
            artist = artist[1]
            explore_handler(artist, chat_id)
    
    elif reply.startswith("/genre"):
        genre_reply = reply.split("/genre ", 1)
        if len(genre_reply) < 2:
            send_message("Какой ваш любимый жанр? Ответь в формате: /genre pop", chat_id)
        else:
            genre_reply = genre_reply[1]
            top_artists = get_genre_songs(genre_reply)
            send_message(f"Нашел! Вот топ-5 исполнителей в жанре {genre_reply}:\n\n{''.join(top_artists)}", chat_id)   
    
    elif reply.startswith("/recommendArtists"):
        artist_name = reply.split("/recommendArtists ", 1)[1]
        similar_artists = get_similar_artists(artist_name)
        if similar_artists:
            message = f"Я тоже люблю {artist_name}, представляешь? 🥰 Думаю, ты оценишь по достоинству следующих исполнителей:\n\n"
            for i, artist in enumerate(similar_artists[:5]):
                message += f"{i+1}. {artist[0]} - {artist[1]}\n"
            send_message(message, chat_id)
        else:
            send_message(f"К сожалению, я не могу найти похожих исполнителей на {artist_name}", chat_id)
    
    elif reply.startswith("/similarSongs"):
        args = reply.split("/similarSongs ", 1)[1].split(" - ")
        if len(args) < 2:
            send_message("Укажите название исполнителя и трека через дефис. Например, /similarSongs Hurts - Wonderful Life", chat_id)
        else:
            artist_name, track_name = args
            insert_similar("similar", artist_name, track_name)
            similar_tracks = get_similar_tracks(artist_name, track_name)
            if similar_tracks:
                message = f"А ты знаешь толк в хорошей музыке! Вот список песен, похожих на {track_name} исполнителя {artist_name}. Нажми на песню, чтобы послушать ее на last.fm 💃\n\n{''.join(similar_tracks)}"
                send_message(message, chat_id)
            else:
                send_message(f"К сожалению, я не могу найти похожих треков на {track_name} исполнителя {artist_name}", chat_id)
                
    else:
        send_message("Прости, я не совсем понимаю что ты имеешь в виду", chat_id)

    return {
        'statusCode': 200,
        'body': json.dumps('Message sent')
    }
