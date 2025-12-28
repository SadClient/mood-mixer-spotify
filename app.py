import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import re
import random

# Sayfa ayarları
st.set_page_config(page_title="Mood Mixer", page_icon="🎧", layout="centered")

# Custom CSS - blurlu şeffaf siyah arka plan + alxishq tarzı
st.markdown("""
    <style>
    .main {
        background: rgba(18, 18, 18, 0.95);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        color: white;
        min-height: 100vh;
    }
    .stButton>button {
        background: linear-gradient(90deg, #1DB954, #1ed760);
        color: white;
        font-weight: bold;
        border: none;
        border-radius: 16px;
        padding: 14px 32px;
        font-size: 20px;
        box-shadow: 0 4px 15px rgba(29, 185, 84, 0.4);
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(29, 185, 84, 0.6);
    }
    .stTextInput>div>div>input {
        background: #282828;
        color: white;
        border-radius: 12px;
        border: 1px solid #404040;
        padding: 12px;
    }
    .stSelectbox>div>div>select {
        background: #282828;
        color: white;
        border-radius: 12px;
    }
    h1 {
        font-size: 3.5rem;
        background: linear-gradient(90deg, #1DB954, #1ed760);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 10px;
    }
    .caption {
        text-align: center;
        color: #b3b3b3;
        font-size: 16px;
        margin-top: 80px;
        font-weight: 500;
    }
    .caption strong {
        color: #1DB954;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🎧 Mood Mixer v2")

st.markdown("""
    <div style="text-align: center; font-size: 1.4rem; color: #b3b3b3; margin-bottom: 30px;">
        <strong>Remix your playlist with a fresh vibe</strong><br>
        Shuffle, reorder and give it your personal touch 🔥
    </div>
    """, unsafe_allow_html=True)

# OAuth
sp_oauth = SpotifyOAuth(
    client_id=st.secrets["SPOTIFY_CLIENT_ID"],
    client_secret=st.secrets["SPOTIFY_CLIENT_SECRET"],
    redirect_uri=st.secrets["SPOTIFY_REDIRECT_URI"],
    scope="playlist-read-private playlist-modify-public playlist-modify-private user-library-read"
)

code = st.query_params.get("code")

if "token_info" not in st.session_state:
    if code:
        token_info = sp_oauth.get_access_token(code)
        cached = sp_oauth.get_cached_token()
        st.session_state.token_info = cached
        st.rerun()
    else:
        auth_url = sp_oauth.get_authorize_url()
        st.markdown(
            f'''
            <div style="text-align: center; margin: 40px 0;">
                <a href="{auth_url}" target="_blank">
                    <button style="
                        padding: 18px 40px;
                        font-size: 22px;
                        background: linear-gradient(90deg, #1DB954, #1ed760);
                        color: white;
                        border: none;
                        border-radius: 16px;
                        cursor: pointer;
                        box-shadow: 0 6px 20px rgba(29, 185, 84, 0.4);
                    ">
                        🔗 Connect with Spotify
                    </button>
                </a>
            </div>
            ''',
            unsafe_allow_html=True
        )
        st.info("👆 Press the button above to connect (opens in new tab)")
        st.stop()

# Token refresh
token_info = st.session_state.token_info
if sp_oauth.is_token_expired(token_info):
    token_info = sp_oauth.refresh_access_token(token_info["refresh_token"])
    st.session_state.token_info = token_info

sp = spotipy.Spotify(auth=token_info["access_token"])
user = sp.current_user()

st.success(f"✅ Connected: **{user['display_name']}**")

# Arayüz
col1, col2 = st.columns(2)
with col1:
    playlist_url = st.text_input("📋 Playlist link:", placeholder="https://open.spotify.com/playlist/...")
with col2:
    mood = st.selectbox("🌈 Select a Mood:", [
        "Happy 😄", "Chill 😌", "Energetic ⚡", "Workout 💪",
        "Focus 🧠", "Party 🎉", "Sad ☔", "Romantic ❤️"
    ])

custom_name = st.text_input("✨ New playlist name (optional):", 
                            placeholder="e.g. My Chill Vibes 🌙, Party Starter 🔥, Sad Hours ☔")

if st.button("🔥 MIX IT! Create new vibe"):
    if not playlist_url:
        st.error("Please paste a playlist link!")
        st.stop()

    with st.spinner("Remixing your playlist with fresh energy..."):
        try:
            match = re.search(r"playlist[/:]([A-Za-z0-9]{22})", playlist_url)
            if not match:
                st.error("Invalid playlist link!")
                st.stop()
            playlist_id = match.group(1)

            track_ids = []
            results = sp.playlist_tracks(playlist_id)
            track_ids.extend([item["track"]["id"] for item in results["items"] if item["track"] and item["track"]["id"]])
            while results["next"]:
                results = sp.next(results)
                track_ids.extend([item["track"]["id"] for item in results["items"] if item["track"] and item["track"]["id"]])

            if len(track_ids) < 3:
                st.error("Not enough songs in the playlist!")
                st.stop()

            random.seed(hash(mood) + hash(custom_name or ""))
            random.shuffle(track_ids)

            playlist_name = custom_name.strip() or f"Mood Mix: {mood} 🎯"

            new_playlist = sp.user_playlist_create(
                user["id"],
                name=playlist_name,
                public=True,
                description="Remixed with Mood Mixer by Sad_Always 🎧 https://mixer.alxishq.site"
            )

            for i in range(0, len(track_ids), 100):
                sp.playlist_add_items(new_playlist["id"], track_ids[i:i+100])

            st.success("✅ Your remixed playlist is ready!")
            st.balloons()
            st.markdown(f"### 🎶 **{new_playlist['name']}** ({len(track_ids)} songs)")
            st.markdown(f"→ [Open on Spotify]({new_playlist['external_urls']['spotify']})")

        except Exception as e:
            st.error(f"Error: {str(e)}")

# Güzel alt yazı
st.markdown("""
    <div class="caption">
        Made with ❤️ by <strong>Sad_Always</strong><br>
        A <strong>AlexisHq</strong> project — <a href="https://alxishq.site" style="color:#1DB954; text-decoration: none; font-weight: bold;">alxishq.site</a>
    </div>
    """, unsafe_allow_html=True)
