# app.py
from flask import Flask, render_template, request, session, redirect, url_for
import secrets
import lastfm
import spotify

app = Flask(__name__)
app.secret_key =  secrets.token_hex(16)

@app.route('/', methods=['GET', 'POST'])
def index():
    similarity_percentage = None
    common_items = []
    category = 'track'  
    
    if request.method == 'POST':
        user1 = request.form['user1']
        user2 = request.form['user2']
        category = request.form.get('category', 'track')
        
        try:
            similarity_percentage, common_items = lastfm.get_top_items_similarity(
                user1, 
                user2, 
                category, 
                lastfm.LIMIT
            )
        except Exception as e:
            return render_template('home.html', error=str(e))
    
    spotify_logged_in = 'token_info' in session
    return render_template('home.html',
                         similarity_percentage=similarity_percentage,
                         common_attributes=common_items,
                         category=category,
                         logged_in=spotify_logged_in)

@app.route('/spotify_login')
def spotify_login():
    
    auth_url = spotify.sp.auth_manager.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    
    session["token_info"] = spotify.sp.auth_manager.get_access_token(request.args['code'])
    return redirect(url_for('index'))

@app.route('/create_playlist', methods=['POST'])
@app.route('/create_playlist', methods=['POST'])
def create_playlist():

    if "token_info" not in session:
        return redirect(url_for('spotify_login'))
    
    spotify.sp.auth_manager.refresh_access_token(session["token_info"]["refresh_token"])
    user_id = spotify.sp.current_user()['id']
    user1 = request.form['user1']
    user2 = request.form['user2']
    category = request.form.get('category', 'track')
    
    try:
    
        similarity_percentage, common_items = lastfm.get_top_items_similarity(
            user1, 
            user2, 
            category,
            lastfm.LIMIT
        )
        
        message = spotify.add_common_items_to_playlist(user_id, user1, user2, category)
        
        spotify_logged_in = 'token_info' in session
        return render_template('home.html',
                             message=message,
                             similarity_percentage=similarity_percentage,
                             common_attributes=common_items,
                             category=category,
                             logged_in=spotify_logged_in)
    except Exception as e:
        return render_template('home.html', 
                             error=str(e),
                             similarity_percentage=None,
                             common_attributes=[],
                             category=category,
                             logged_in=True)

if __name__ == '__main__':
    app.run(debug=True)