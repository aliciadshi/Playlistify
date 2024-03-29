import os
from dotenv import find_dotenv, load_dotenv
import base64
import requests
import json
from datetime import datetime, timedelta
from flask import Flask, redirect, request, jsonify, session, render_template
import urllib.parse
import chatgpt

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

app = Flask(__name__)
app.secret_key = os.getenv("APP_SECRET_KEY")

client_id = os.getenv("SPOT_CLIENT_ID")
client_secret = os.getenv("SPOT_CLIENT_SECRET")
base_uri = "https://playlistify.me"
base_uri2 = "http://127.0.0.1:4444"
redirect_uri = base_uri2 + "/callback"

AUTH_URL = "https://accounts.spotify.com/authorize"
token_url = "https://accounts.spotify.com/api/token"
api_base_url = "https://api.spotify.com/v1/"

@app.route('/')
def index():

    result = render_template('index.html')

    return result

@app.route('/login')
def login():
    scope = 'user-read-private user-read-email'

    params = {
        'client_id': client_id,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': redirect_uri,
        'show_dialog': True
    }

    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    return redirect(auth_url)

@app.route('/callback')
def callback():
    if 'error' in request.args:
        return jsonify({"error": request.args['error']})
    
    if 'code' in request.args:
        req_body = {
            'code':request.args['code'],
            'grant_type': "authorization_code",
            'redirect_uri': redirect_uri,
            'client_id': client_id,
            'client_secret': client_secret
        }

        response = requests.post(token_url, data=req_body)
        
        try:
            token_info = response.json()
        except json.decoder.JSONDecoderError:
            print("decoder error")

        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token']
        session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']

        print("access_token (right after token_info):" + session['access_token'])

        return redirect('/playlists')
    

@app.route('/playlists')
def get_playlists():
    if 'access_token' not in session:
        return redirect('login')
    
    if datetime.now().timestamp () > session['expires_at']:
        return redirect('/refresh-token')
    
    headers = {
        'Authorization' : f"Bearer {session['access_token']}"
    }

    # response = requests.get(api_base_url + 'me/playlists', headers=headers)

    user = requests.get(api_base_url + 'me', headers=headers)

    print("access_token (right before user):" + session['access_token'])
    print(user)

    user_json = user.json()
    user_id = user_json["id"]

    response = requests.get(api_base_url + 'users/' + user_id + '/playlists', headers=headers)
    
    print("access_token (right before response):" + session['access_token'])
    print(response)
    
    playlists = response.json()

    result = ""

    items = []

    for i in range(playlists["total"]):
        playlist_id = playlists['items'][i]['id']
        playlist_name = playlists["items"][i]["name"]
        playlist_pfp = playlists["items"][i]["images"][0]["url"]
        playlist_link = base_uri2 + '/songs/' + playlist_id

        items.append({'name':playlist_name, 'link':playlist_link, 'image':playlist_pfp})

    result = render_template('playlists.html', items=items)

    return result

@app.route('/songs/<playlist_id>')
def get_songs(playlist_id):
    if 'refresh_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp () > session['expires_at']:
        return redirect('/refresh-token')
    
    headers = {
        'Authorization' : f"Bearer {session['access_token']}"
    }

    response = requests.get(api_base_url + 'playlists/' + playlist_id+ "/tracks", headers=headers)

    songs = response.json()
    result = ""

    songList = []

    for i in range(songs["total"]):
        if songs["items"][i]["is_local"] == True:
            i += 1
        else:
            song_name = songs["items"][i]["track"]["name"]
            song_artist = songs["items"][i]["track"]["album"]["artists"][0]["name"]

            songList.append({'track': song_name, 'artist': song_artist})

            result += str(i+1) + ". " + songs["items"][i]["track"]["name"] + " - " + songs["items"][i]["track"]["album"]["artists"][0]["name"] + "<br>  "

    result = "AI Generated Name: " + chatgpt.request_playlist_name(result)

    return render_template("songs.html", result=result, items=songList)



@app.route('/refresh-token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')
    
    if datetime.now().timestamp () > session['expires_at']:
        req_body = {
            'grant_type':'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id': client_id,
            'client_secret': client_secret
        }

        response = requests.post(token_url, data=req_body)
        new_token_info = response.json()

        session['access_token'] = new_token_info['access_token']
        session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']

        return redirect('/playlists')
    

if __name__ == '__main__':
    # app.run(host='0.0.0.0', debug=True, port=4444)
    privateIP = os.getenv("PRIVATE_IPV4")
    app.run(host=privateIP, debug=True)

# def search_for_artist(token, artist_name):
#     url = "https://api.spotify.com/v1/search"
#     headers = get_auth_header(token)
#     query =  f"?q={artist_name}&type=artist&limit=1"

#     query_url = url + query
#     result = get(query_url, headers=headers)
#     json_result = json.loads(result.content)["artists"]["items"]
#     if len(json_result) == 0:
#         print("No artist found")
#         return None
    
#     return json_result[0]

# def get_songs_by_artist(token, artist_id):
#     url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?country=US"
#     headers = get_auth_header(token)
#     result = get(url, headers=headers)
#     json_result = json.loads(result.content)["tracks"]
#     return json_result

# user_input = input("Artist Name: ")

# token = get_token()
# result = search_for_artist(token, user_input)
# artist_id = result["id"]
# songs = get_songs_by_artist(token, artist_id)

# for i, song in enumerate(songs):
#     print(f"{i + 1}. {song['name']}")