import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random

st.set_page_config(page_title="Mood Mixer", page_icon="🎧", layout="centered")

st.title("🎧 Mood Mixer")
st.markdown("Turn any Spotify playlist into your perfect vibe in seconds!")

# Spotify OAuth
sp_oauth = SpotifyOAuth(
    client_id=st.secrets["SPOTIFY_CLIENT_ID"],
    client_secret=st.secrets["SPOTIFY_CLIENT_SECRET"],
    redirect_uri=st.secrets["SPOTIFY_REDIRECT_URI"],
    scope="playlist-read-private playlist-modify-public playlist-modify-private user-library-read"
)

# Authentication
if "token_info" not in st.session_state:
    auth_url = sp_oauth.get_authorize_url()
    st.markdown(f"<a href='{auth_url}' target='_self'><button style='padding:10px 20px; font-size:18px; background:#1DB954; color:white; border:none; border-radius:8px;'>🔗 Connect with Spotify</button></a>", unsafe_allow_html=True)
    st.stop()

else:
    token_info = st.session_state.token_info
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        st.session_state.token_info = token_info

    sp = spotipy.Spotify(auth=token_info['access_token'])

    # User info
    user = sp.current_user()
    st.success(f"Connected as **{user['display_name']}** 🎉")

    playlist_url = st.text_input("📋 Paste Spotify playlist URL:")
    mood = st.selectbox("🌈 Choose your mood", 
        ["Happy 😄", "Chill 😌", "Energetic ⚡", "Workout 💪", "Focus 🧠", "Party 🎉", "Sad ☔", "Romantic ❤️"])

    mood_map = {
        "Happy 😄": {"valence": 0.8, "energy": 0.7},
        "Chill 😌": {"valence": 0.5, "energy": 0.3},
        "Energetic ⚡": {"energy": 0.9, "danceability": 0.8},
        "Workout 💪": {"energy": 0.95, "danceability": 0.7, "tempo": 130},
        "Focus 🧠": {"energy": 0.4, "instrumentalness": 0.7},
        "Party 🎉": {"danceability": 0.9, "energy": 0.9},
        "Sad ☔": {"valence": 0.2, "energy": 0.4},
        "Romantic ❤️": {"valence": 0.6, "acousticness": 0.7}
    }

    if st.button("🔥 MIX IT!") and playlist_url:
        with st.spinner("Analyzing playlist and mixing vibes..."):
            try:
                playlist_id = playlist_url.split("/")[-1].split("?")[0]
                tracks = sp.playlist_tracks(playlist_id)["items"]
                track_ids = [item["track"]["id"] for item in tracks if item["track"]["id"]]

                if not track_ids:
                    st.error("No tracks found in playlist!")
                    st.stop()

                features = sp.audio_features(track_ids)
                target = mood_map[mood]

                # Simple similarity score
                def score(feat):
                    s = 0
                    for k, v in target.items():
                        if feat[k] is not None:
                            s += (feat[k] - v) ** 2
                    return s

                scored = [(t, score(f)) for t, f in zip(track_ids, features) if f]
                scored.sort(key=lambda x: x[1])
                recommended = [t for t, s in scored[:50]]  # Top 50

                # Create new playlist
                new_pl = sp.user_playlist_create(user["id"], f"Mood Mix: {mood}", public=True)
                sp.playlist_add_items(new_pl["id"], recommended)

                st.success("✅ New playlist created!")
                st.markdown(f"### 🎯 **{new_pl['name']}** ({len(recommended)} songs)")
                st.markdown(f"→ [Open in Spotify]({new_pl['external_urls']['spotify']})")

            except Exception as e:
                st.error(f"Error: {str(e)}")

# Callback handling
code = st.query_params.get("code")
if code:
    token_info = sp_oauth.get_access_token(code, as_dict=True)
    st.session_state.token_info = token_info
    st.rerun()
