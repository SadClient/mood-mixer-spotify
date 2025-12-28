import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import re
import random

st.set_page_config(page_title="Mood Mixer", page_icon="ᯤ", layout="centered")

st.title("🎧 Mood Mixer v2")
st.markdown("**Customize your playlist with Spotify's smart recommendations to match your mood!** 🔥")

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

# Token refresh
token_info = st.session_state.token_info
if sp_oauth.is_token_expired(token_info):
    token_info = sp_oauth.refresh_access_token(token_info["refresh_token"])
    st.session_state.token_info = token_info

sp = spotipy.Spotify(auth=token_info["access_token"])
user = sp.current_user()
st.success(f"✅ Connected: **{user['display_name']}**")

# Market (ülke kodu) - 404 hatasını önlemek için zorunlu
market = user.get("country", "US")  # TR yoksa US fallback

playlist_url = st.text_input("📋 Playlist link:", placeholder="https://open.spotify.com/playlist/...")
mood = st.selectbox("🌈 Select a Mood:", [
    "Happy 😄", "Chill 😌", "Energetic ⚡", "Workout 💪",
    "Focus 🧠", "Party 🎉", "Sad ☔", "Romantic ❤️"
])

mood_targets = {
    "Happy 😄": {"target_valence": 0.9, "target_energy": 0.7, "target_danceability": 0.7},
    "Chill 😌": {"target_valence": 0.5, "target_energy": 0.3, "target_danceability": 0.4},
    "Energetic ⚡": {"target_energy": 0.9, "target_danceability": 0.8},
    "Workout 💪": {"target_energy": 0.95, "target_tempo": 130, "target_danceability": 0.7},
    "Focus 🧠": {"target_energy": 0.3, "target_instrumentalness": 0.8},
    "Party 🎉": {"target_danceability": 0.9, "target_energy": 0.9, "target_valence": 0.8},
    "Sad ☔": {"target_valence": 0.2, "target_energy": 0.4},
    "Romantic ❤️": {"target_valence": 0.6, "target_energy": 0.5, "target_acousticness": 0.7}
}

if st.button("🔥 MIX IT!") and playlist_url:
    with st.spinner("Spotify suggestions are being collected..."):
        try:
            match = re.search(r"playlist[/:]([A-Za-z0-9]{22})", playlist_url)
            if not match:
                st.error("Invalid playlist link!")
                st.stop()
            playlist_id = match.group(1)

            tracks = sp.playlist_tracks(playlist_id)["items"]
            track_ids = [t["track"]["id"] for t in tracks if t["track"] and t["track"]["id"]]

            if len(track_ids) < 5:
                st.error("The playlist must have at least 5 songs!")
                st.stop()

            seed_tracks = random.sample(track_ids, 5)
            targets = mood_targets[mood]

            # İlk deneme: Mood target'larla
            try:
                recommendations = sp.recommendations(
                    seed_tracks=seed_tracks,
                    limit=50,
                    market=market,
                    **targets
                )
                rec_tracks = recommendations["tracks"]
                if len(rec_tracks) > 0:
                    st.info(f"Perfect match for {mood}! 🎯")
                else:
                    raise spotipy.SpotifyException(404, -1, "No results")
            except spotipy.SpotifyException:
                # Fallback: Sadece seed_tracks ile benzer şarkılar
                st.info("Strong mood match not available in your region. Getting songs very similar to your playlist instead... 😊")
                recommendations = sp.recommendations(
                    seed_tracks=seed_tracks,
                    limit=50,
                    market=market
                )
                rec_tracks = recommendations["tracks"]

            rec_ids = [track["id"] for track in rec_tracks]

            if len(rec_ids) == 0:
                st.error("No suggestions found even with fallback. Try a different playlist!")
                st.stop()

            new_playlist = sp.user_playlist_create(
                user["id"],
                name=f"Mood Mix: {mood} 🎯",
                public=True,
                description="Prepared with Mood Mixer V2 🎧 https://mixer.alxishq.site"
            )

            for i in range(0, len(rec_ids), 100):
                sp.playlist_add_items(new_playlist["id"], rec_ids[i:i+100])

            st.success("✅ Your new playlist is ready!")
            st.balloons()
            st.markdown(f"### 🎶 **{new_playlist['name']}** ({len(rec_ids)} songs)")
            st.markdown(f"→ [Open on Spotify]({new_playlist['external_urls']['spotify']})")

        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            st.info("Try again with a different mood or playlist.")

st.caption("Made with ❤️ by Sad_Always – Mood Mixer v2 A AlexisHq project.")
