# spotify.py
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import lastfm
import os
from dotenv import load_dotenv

load_dotenv()

SPOTIPY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = "https://blendfm.onrender.com/callback"
SCOPE = "playlist-modify-public playlist-modify-private"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope=SCOPE
))

def search_spotify_track(track_name):
    try:
        results = sp.search(q=track_name, limit=1, type='track')
        tracks = results.get('tracks', {}).get('items', [])
        return tracks[0]['id'] if tracks else None
    except Exception as e:
        print(f"Error searching for track {track_name}: {str(e)}")
        return None


def create_spotify_playlist(user_id, playlist_name):
    playlist = sp.user_playlist_create(user=user_id, name=playlist_name, public=True)
    return playlist['id']


def add_tracks_to_playlist(playlist_id, track_ids):

    for i in range(0, len(track_ids), 100):
        chunk = track_ids[i:i + 100]
        sp.playlist_add_items(playlist_id, chunk)

def add_common_items_to_playlist(spotify_user_id, lastfm_user1, lastfm_user2, category):

    try:
        similarity, common_items = lastfm.get_top_items_similarity(
            lastfm_user1, 
            lastfm_user2, 
            category,
            lastfm.LIMIT
        )
        
        if category == 'track':
            track_ids = [search_spotify_track(item['name']) for item in common_items]
            track_ids = [tid for tid in track_ids if tid]  # none value removed
            
            if not track_ids:
                return "No matching tracks found on Spotify."
            
            playlist_name = f"{lastfm_user1} + {lastfm_user2}"
            playlist_id = create_spotify_playlist(spotify_user_id, playlist_name)
            add_tracks_to_playlist(playlist_id, track_ids)
            
            return f"Added {len(track_ids)} tracks to the playlist!"
        else:
            return f"Playlist creation is only supported for tracks, not {category}s"
            
    except Exception as e:
        raise Exception(f"Error creating playlist: {str(e)}")