import base64
import datetime
import json
import urllib
import random

import config
import requests
import spotipy
from flask import Blueprint, redirect, request, session, url_for

spotify_bp = Blueprint('spotify', __name__,
                       template_folder='templates/instagram')

spotify_at = 'sp_access_token'

# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)

# Server-side Parameters
CLIENT_SIDE_URL = "http://127.0.0.1"
PORT = 5000
REDIRECT_URI = "{}:{}/callback/q".format(CLIENT_SIDE_URL, PORT)
SCOPE = "playlist-modify-public playlist-modify-private"


@spotify_bp.route("/callback/q")
def callback():
    # Auth Step 4: Requests refresh and access tokens
    auth_token = request.args['code']
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": url_for('spotify.callback', _external=True)
    }
    base64encoded = base64.b64encode("{}:{}".format(config.SPOTIFY_CLIENT_ID, config.SPOTIFY_CLIENT_SECRET))
    headers = {"Authorization": "Basic {}".format(base64encoded)}
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload, headers=headers)

    # Auth Step 5: Tokens are Returned to Application
    response_data = json.loads(post_request.text)
    access_token = response_data["access_token"]
    session[spotify_at] = access_token
    sp = spotipy.Spotify(auth=access_token)
    username = sp.current_user()['id']
    session['spotify_user'] = username
    # refresh_token = response_data["refresh_token"]
    # token_type = response_data["token_type"]
    # expires_in = response_data["expires_in"]
    # playlist_url = get_recommendations(access_token)
    return redirect('/')


@spotify_bp.route('/auth/spotify')
def login():
    auth_query_parameters = {
        "response_type": "code",
        "redirect_uri": url_for('spotify.callback', _external=True),
        "scope": SCOPE,
        "client_id": config.SPOTIFY_CLIENT_ID
    }
    url_args = "&".join(["{}={}".format(key, urllib.quote(val)) for key, val in auth_query_parameters.iteritems()])
    auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
    return redirect(auth_url)


def get_recommendations(sentiment_data):
    token = session[spotify_at]
    sp = spotipy.Spotify(auth=token)

    dt = datetime.datetime.now()
    creation_time = dt.strftime('%m/%d/%Y %H:%M')

    username = session.get('spotify_user', 'spotify')
    pl = sp.user_playlist_create(username, "TuneMyLife - " + creation_time, public=True)

    tracks_uris = []
    for pic_sentiment in sentiment_data:
        if pic_sentiment:
            tracks = sp.recommendations(seed_artists=[], seed_genres=['chill', 'rock', 'electronic', 'classical', 'r-n-b'],
                                        seed_tracks=[], limit=10, country=None, **pic_sentiment)
            if tracks:
                songs = [random.choice(tracks['tracks']) for i in range(3)]

                # Get the tracks uris
                for tr in songs:
                    tracks_uris.append(tr['uri'])

    # Add tracks to the new playlist
    snapshot_id = sp.user_playlist_add_tracks(username, pl['id'], tracks_uris)

    return pl['external_urls']['spotify']


def create_playlist(token, tracks):
    sp = spotipy.Spotify(auth=token)

    dt = datetime.datetime.now()
    creation_time = dt.strftime('%m/%d/%Y %H:%M')

    username = session.get('spotify_user', 'spotify')
    pl = sp.user_playlist_create(username, "TuneMyLife - " + creation_time, public=True)

    # Get the tracks uris
    tracks_uris = []
    for tr in tracks['tracks']:
        tracks_uris.append(tr['uri'])

    # Add tracks to the new playlist
    snapshot_id = sp.user_playlist_add_tracks(username, pl['id'], tracks_uris)

    return pl['external_urls']['spotify']
