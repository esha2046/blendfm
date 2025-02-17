from flask import Flask, render_template, request, jsonify
import requests
import numpy as np

app = Flask(__name__)

API_URL = 'https://ws.audioscrobbler.com/2.0/'
API_KEY = '5e959628524d81db916165e8dd19ceb3'
limit = 1000

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

import numpy as np

def calculate_enhanced_similarity(list1, list2, top_weight=2.0, top_n=20, playcount_weight=1.5, rank_decay_factor=0.005):
    
    dict1 = {item['name']: item for item in list1}
    dict2 = {item['name']: item for item in list2}
    
    common_items = set(dict1.keys()).intersection(set(dict2.keys()))
    all_items = set(dict1.keys()).union(set(dict2.keys()))
    
    if not all_items:
        return 0.0
    
    total_score = 0
    max_possible_score = 0
    
    for name in all_items:
        weight = 1.0
        
        if name in common_items:
            item1, item2 = dict1[name], dict2[name]
            
            rank1, rank2 = item1['rank'], item2['rank']
            
            if rank1 <= top_n or rank2 <= top_n:
                top_modifier = max(1.0, top_weight * (1 - min(rank1, rank2) / top_n))
                weight *= top_modifier
            
            pc1, pc2 = item1['playcount'], item2['playcount']
            if pc1 > 0 and pc2 > 0:
                playcount_ratio = min(pc1, pc2) / max(pc1, pc2)
                weight *= (0.5 + playcount_weight * playcount_ratio)
            
            rank_diff = abs(rank1 - rank2)
            rank_decay = np.exp(-rank_decay_factor * rank_diff)
            weight *= rank_decay
            
            total_score += weight
        
        max_possible_score += weight
    
    raw_similarity = total_score / max_possible_score if max_possible_score > 0 else 0
    
    if raw_similarity == 0:
        boosted_similarity = 0
    elif raw_similarity < 0.2: 
        boosted_similarity = 0.2 + raw_similarity * 2
    elif raw_similarity < 0.5:  
        boosted_similarity = 0.5 + (raw_similarity - 0.2) * 1.2
    else: 
        boosted_similarity = 0.8 + (raw_similarity - 0.5) * 0.8
    
    boosted_similarity = min(boosted_similarity, 1.0)
    
    return round(boosted_similarity * 100, 1)

def get_top_items_similarity(user1, user2, category, limit):
    
    if category == 'artist':
        data1 = convert_top_artists_response(get_top_artists(user1, limit))
        data2 = convert_top_artists_response(get_top_artists(user2, limit))
    elif category == 'album':
        data1 = convert_top_albums_response(get_top_albums(user1, limit))
        data2 = convert_top_albums_response(get_top_albums(user2, limit))
    elif category == 'track':
        data1 = convert_top_tracks_response(get_top_tracks(user1, limit))
        data2 = convert_top_tracks_response(get_top_tracks(user2, limit))
    else:
        raise ValueError(f"Invalid category: {category}")
    
    
    similarity = calculate_enhanced_similarity(data1, data2)
    
    
    common_names = set(item['name'] for item in data1).intersection(set(item['name'] for item in data2))
    dict1 = {item['name']: item for item in data1}
    dict2 = {item['name']: item for item in data2}
    
    common_items = []
    for name in common_names:
        item1 = dict1[name]
        item2 = dict2[name]
        
        avg_rank = (item1['rank'] + item2['rank']) / 2
        total_plays = item1['playcount'] + item2['playcount']
        common_items.append({
            'name': name,
            'playcount': total_plays,
            'rank': item1['rank'],  
            'avg_rank': avg_rank,  
            'user1_rank': item1['rank'],
            'user2_rank': item2['rank'],
            'user1_plays': item1['playcount'],
            'user2_plays': item2['playcount']
        })
    
  
    common_items.sort(key=lambda x: x['avg_rank'])
    
    return similarity, common_items

@app.route('/', methods=['GET', 'POST'])
def index():
    similarity_percentage = None
    common_attributes = []
    
    if request.method == 'POST':
        user1 = request.form['user1']
        user2 = request.form['user2']
        category = request.form['category']
        
        try:
            similarity_percentage, common_attributes = get_top_items_similarity(
                user1, user2, category, limit
            )
        except Exception as e:
            return render_template('home.html', error=str(e))
    
    return render_template('home.html', 
                          similarity_percentage=similarity_percentage, 
                          common_attributes=common_attributes)
if __name__ == '__main__':
    app.run(debug=True)