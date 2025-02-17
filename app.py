from flask import Flask, render_template, request, jsonify
import requests
import numpy as np

app = Flask(__name__)

API_URL = 'https://ws.audioscrobbler.com/2.0/'
API_KEY = '5e959628524d81db916165e8dd19ceb3'
limit = 500

def get_api_url(params):
    url = f'{API_URL}?'
    for key, value in params.items():
        url += f'{key}={value}&'
    return url[:-1]

def get_top(username, limit, method):
    params = {
        'method': method,
        'user': username,
        'api_key': API_KEY,
        'format': 'json',
        'limit': limit
    }
    url = get_api_url(params)
    response = requests.get(url)
    return response.json()

def get_top_artists(username, limit):
    return get_top(username, limit, 'user.gettopartists')

def get_top_albums(username, limit):
    return get_top(username, limit, 'user.gettopalbums')

def get_top_tracks(username, limit):
    return get_top(username, limit, 'user.gettoptracks')


def convert_top_artists_response(response):
    if 'error' in response:
        raise Exception(response['message'])
    return [{
        'name': artist['name'],
        'playcount': int(artist['playcount']),
        'rank': int(artist['@attr']['rank'])
    } for artist in response['topartists']['artist']]

def convert_top_albums_response(response):
    if 'error' in response:
        raise Exception(response['message'])
    return [{
        'name': f"{album['artist']['name']} - {album['name']}",
        'playcount': int(album['playcount']),
        'rank': int(album['@attr']['rank'])
    } for album in response['topalbums']['album']]

def convert_top_tracks_response(response):
    if 'error' in response:
        raise Exception(response['message'])
    return [{
        'name': f"{track['artist']['name']} - {track['name']}",
        'playcount': int(track['playcount']),
        'rank': int(track['@attr']['rank'])
    } for track in response['toptracks']['track']]

def calculate_jaccard_similarity(list1, list2):
    set1 = set(list1)
    set2 = set(list2)
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    similarity = (intersection / union) * 100 
    return round(similarity, 1)  


@app.route('/', methods=['GET', 'POST'])
def index():
    similarity_percentage = None
    common_attributes = []
    
    if request.method == 'POST':
        user1 = request.form['user1']
        user2 = request.form['user2']
        category = request.form['category']

        if category == 'artist':
            data1 = convert_top_artists_response(get_top_artists(user1, limit))
            data2 = convert_top_artists_response(get_top_artists(user2, limit))
        elif category == 'album':
            data1 = convert_top_albums_response(get_top_albums(user1, limit))
            data2 = convert_top_albums_response(get_top_albums(user2, limit))
        elif category == 'track':
            data1 = convert_top_tracks_response(get_top_tracks(user1, limit))
            data2 = convert_top_tracks_response(get_top_tracks(user2, limit))
        
  
        similarity_percentage = calculate_jaccard_similarity([item['name'] for item in data1], [item['name'] for item in data2])

        common_attributes = [item for item in data1 if item['name'] in [attr['name'] for attr in data2]]

    return render_template('home.html', similarity_percentage=similarity_percentage, common_attributes=common_attributes)

if __name__ == '__main__':
    app.run(debug=True)