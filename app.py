import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import re
import random

st.set_page_config(page_title="Mood Mixer", page_icon="ᯤ", layout="centered")

st.title("🎧 Mood Mixer v2")
st.markdown("**Shuffle and remix your playlist with a fresh vibe!** 🔥")

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
            f'<a href="{auth_url}" target="_blank"><button style="padding:15px 30px; font-size:20px; background:#1DB954; color:white; border:none; border-radius:12px; cursor:pointer;">🔗 Connect with Spotify</button></a>',
            unsafe_allow_html=True
        )
        st.info("Press the Button, Connect by new tab.")
        st.stop()

token_info = st.session_state.token_info
if sp_oauth.is_token_expired(token_info):
    token_info = sp_oauth.refresh_access_token(token_info["refresh_token"])
    st.session_state.token_info = token_info

sp = spotipy.Spotify(auth=token_info["access_token"])
user = sp.current_user()
st.success(f"✅ Connected: **{user['display_name']}**")

playlist_url = st.text_input("📋 Playlist link:", placeholder="https://open.spotify.com/playlist/...")
mood = st.selectbox("🌈 Select a Mood:", [
    "Happy 😄", "Chill 😌", "Energetic ⚡", "Workout 💪",
    "Focus 🧠", "Party 🎉", "Sad ☔", "Romantic ❤️"
])

if st.button("🔥 MIX IT! Create new vibe") and playlist_url:
    with st.spinner("Remixing your playlist with fresh energy..."):
        try:
            match = re.search(r"playlist[/:]([A-Za-z0-9]{22})", playlist_url)
            if not match:
                st.error("Invalid playlist link!")
                st.stop()
            playlist_id = match.group(1)

            # Tüm şarkıları al (100'den fazla varsa hepsini)
            track_ids = []
            results = sp.playlist_tracks(playlist_id)
            track_ids.extend([item["track"]["id"] for item in results["items"] if item["track"] and item["track"]["id"]])
            
            while results["next"]:
                results = sp.next(results)
                track_ids.extend([item["track"]["id"] for item in results["items"] if item["track"] and item["track"]["id"]])

            if len(track_ids) < 3:
                st.error("Not enough songs in the playlist!")
                st.stop()

            # Mood'a göre hafif sıralama (rastgele ama mood ismine göre seed)
            random.seed(hash(mood))  # Aynı mood aynı sıralama
            random.shuffle(track_ids)

            # Yeni playlist
            new_playlist = sp.user_playlist_create(
                user["id"],
                name=f"Mood Mix: {mood} 🎯",
                public=True,
                description="Remixed with Mood Mixer V2 🎧 https://mixer.alxishq.site"
            )

            # Şarkıları 100'erli ekle
            for i in range(0, len(track_ids), 100):
                sp.playlist_add_items(new_playlist["id"], track_ids[i:i+100])

            st.success("✅ Your remixed playlist is ready!")
            st.balloons()
            st.markdown(f"### 🎶 **{new_playlist['name']}** ({len(track_ids)} songs)")
            st.markdown(f"→ [Open on Spotify]({new_playlist['external_urls']['spotify']})")

        except Exception as e:
            st.error(f"Error: {str(e)}")

st.caption("Made with ❤️ by Sad_Always – Mood Mixer v2 A AlexisHq project.")
