import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import re
import random

# Sayfa ayarları
st.set_page_config(page_title="Mood Mixer", page_icon="🎧", layout="centered")

# Başlık
st.title("🎧 Mood Mixer v2")
st.markdown("**Playlistini istediğin moda göre Spotify'ın kendi önerileriyle karıştır!** 🔥")

# OAuth
sp_oauth = SpotifyOAuth(
    client_id=st.secrets["SPOTIFY_CLIENT_ID"],
    client_secret=st.secrets["SPOTIFY_CLIENT_SECRET"],
    redirect_uri=st.secrets["SPOTIFY_REDIRECT_URI"],
    scope="playlist-read-private playlist-modify-public playlist-modify-private user-library-read",
    cache_path=".cache",  # Streamlit Cloud'da çalışır
    show_dialog=True
)

code = st.query_params.get("code")

if "token_info" not in st.session_state:
    if code:
        # as_dict=False yapıyoruz (deprecation uyarısını kaldırmak için)
        token_info = sp_oauth.get_access_token(code, as_dict=False)
        # token_info artık string (access_token), ama refresh için dict lazım
        # Bu yüzden cached token'ı alalım (otomatik refresh yapar)
        token_info = sp_oauth.get_cached_token()
        st.session_state.token_info = token_info
        st.rerun()
    else:
        auth_url = sp_oauth.get_authorize_url()
        st.markdown(
            f"""
            <a href='{auth_url}' target='_blank'>
                <button style="
                    padding: 15px 30px;
                    font-size: 20px;
                    background: #1DB954;
                    color: white;
                    border: none;
                    border-radius: 12px;
                    cursor: pointer;
                ">
                    🔗 Connect with Spotify
                </button>
            </a>
            """,
            unsafe_allow_html=True
        )
        st.info("Butona tıkla, yeni sekmede Spotify ile bağlan.")
        st.stop()

# Token refresh (otomatik)
token_info = sp_oauth.refresh_access_token(st.session_state.token_info["refresh_token"]) if sp_oauth.is_token_expired(st.session_state.token_info) else st.session_state.token_info
st.session_state.token_info = token_info

# Client
sp = spotipy.Spotify(auth=token_info["access_token"])
user = sp.current_user()
st.success(f"✅ Bağlandı: **{user['display_name']}**")

# Arayüz ve gerisi aynı (recommendations kısmı)
playlist_url = st.text_input("📋 Playlist linki:", placeholder="https://open.spotify.com/playlist/...")
mood = st.selectbox("🌈 Mood seç:", [
    "Happy 😄", "Chill 😌", "Energetic ⚡", "Workout 💪",
    "Focus 🧠", "Party 🎉", "Sad ☔", "Romantic ❤️"
])

mood_params = {
    "Happy 😄": {"target_valence": 0.9, "target_energy": 0.7, "target_danceability": 0.7},
    "Chill 😌": {"target_valence": 0.5, "target_energy": 0.3, "min_instrumentalness": 0.4},
    "Energetic ⚡": {"target_energy": 0.9, "target_danceability": 0.8},
    "Workout 💪": {"target_energy": 0.95, "target_tempo": 130, "target_danceability": 0.7},
    "Focus 🧠": {"target_energy": 0.4, "target_instrumentalness": 0.8, "target_acousticness": 0.6},
    "Party 🎉": {"target_danceability": 0.9, "target_energy": 0.9, "target_valence": 0.8},
    "Sad ☔": {"target_valence": 0.2, "target_energy": 0.4, "target_acousticness": 0.7},
    "Romantic ❤️": {"target_valence": 0.6, "target_energy": 0.5, "target_acousticness": 0.8}
}

if st.button("🔥 MIX IT!") and playlist_url:
    with st.spinner("Öneriler alınıyor..."):
        try:
            match = re.search(r"playlist[/:]([A-Za-z0-9]{22})", playlist_url)
            if not match:
                st.error("Geçersiz link!")
                st.stop()
            playlist_id = match.group(1)

            tracks = sp.playlist_tracks(playlist_id)["items"]
            track_ids = [t["track"]["id"] for t in tracks if t["track"] and t["track"]["id"]]

            if len(track_ids) < 5:
                st.error("En az 5 şarkı lazım!")
                st.stop()

            seed_tracks = random.sample(track_ids, 5)
            params = mood_params[mood].copy()
            params["limit"] = 50
            params["seed_tracks"] = seed_tracks

            recs = sp.recommendations(**params)
            rec_ids = [t["id"] for t in recs["tracks"]]

            new_pl = sp.user_playlist_create(user["id"], f"Mood Mix: {mood} 🎯", public=True,
                                             description="Mood Mixer v2 ile hazırlandı")
            for i in range(0, len(rec_ids), 100):
                sp.playlist_add_items(new_pl["id"], rec_ids[i:i+100])

            st.success("✅ Hazır!")
            st.balloons()
            st.markdown(f"### 🎶 {new_pl['name']} ({len(rec_ids)} şarkı)")
            st.markdown(f"→ [Aç]({new_pl['external_urls']['spotify']})")

        except Exception as e:
            st.error(f"Hata: {str(e)}")

st.caption("Made with ❤️ by Sad_Always – v2 Recommendations")
