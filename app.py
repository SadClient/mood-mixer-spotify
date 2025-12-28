import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import re
import random

# Sayfa ayarları
st.set_page_config(page_title="Mood Mixer", page_icon="🎧", layout="centered")

# Başlık ve açıklama
st.title("🎧 Mood Mixer v2")
st.markdown("**Herhangi bir Spotify playlistini istediğin moda göre otomatik karıştır!**")
st.markdown("Spotify'ın kendi akıllı öneri sistemiyle daha iyi sonuçlar 🔥")

# Spotify OAuth ayarları
sp_oauth = SpotifyOAuth(
    client_id=st.secrets["SPOTIFY_CLIENT_ID"],
    client_secret=st.secrets["SPOTIFY_CLIENT_SECRET"],
    redirect_uri=st.secrets["SPOTIFY_REDIRECT_URI"],
    scope="playlist-read-private playlist-modify-public playlist-modify-private user-library-read"
)

# Query params'tan code'u al
code = st.query_params.get("code")

# Session state ile token yönetimi
if "token_info" not in st.session_state:
    if code:
        token_info = sp_oauth.get_access_token(code, as_dict=True)
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
                    🔗 Connect with Spotify (Yeni Sekmede Açılır)
                </button>
            </a>
            """,
            unsafe_allow_html=True
        )
        st.info("Bağlanmak için butona tıkla, izin ekranı yeni sekmede açılacak.")
        st.stop()

# Token refresh
token_info = st.session_state.token_info
if sp_oauth.is_token_expired(token_info):
    token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
    st.session_state.token_info = token_info

# Spotify client
sp = spotipy.Spotify(auth=token_info['access_token'])
user = sp.current_user()
st.success(f"✅ Bağlandı: **{user['display_name']}**")

# Arayüz
playlist_url = st.text_input("📋 Spotify playlist linkini yapıştır:", placeholder="https://open.spotify.com/playlist/...")
mood = st.selectbox("🌈 Hedef mood'un ne olsun?", [
    "Happy 😄",
    "Chill 😌",
    "Energetic ⚡",
    "Workout 💪",
    "Focus 🧠",
    "Party 🎉",
    "Sad ☔",
    "Romantic ❤️"
])

# Mood'a göre recommendation parametreleri
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

if st.button("🔥 MIX IT! Yeni vibe hazırla") and playlist_url:
    with st.spinner("Playlist analiz ediliyor, Spotify önerileri alınıyor..."):
        try:
            # Playlist ID çıkar
            match = re.search(r"playlist[/:]([A-Za-z0-9]{22})(?:\?|$)", playlist_url)
            if not match:
                st.error("Geçersiz playlist linki! Doğru formatta olduğundan emin ol.")
                st.stop()
            
            playlist_id = match.group(1)

            # Playlistteki şarkıları al
            tracks = sp.playlist_tracks(playlist_id)["items"]
            track_ids = [item["track"]["id"] for item in tracks if item["track"] and item["track"]["id"]]
            
            if len(track_ids) < 5:
                st.error("Playlistte en az 5 şarkı olmalı ki iyi öneri alınabilsin!")
                st.stop()

            # Rastgele 5 seed şarkı seç
            seed_tracks = random.sample(track_ids, 5)

            # Mood parametrelerini al
            params = mood_params[mood]
            params["limit"] = 50
            params["seed_tracks"] = seed_tracks

            # Recommendations al
            recommendations = sp.recommendations(**params)

            recommended_tracks = recommendations["tracks"]
            recommended_ids = [track["id"] for track in recommended_tracks]

            if not recommended_ids:
                st.error("Öneri alınamadı, farklı bir playlist dene.")
                st.stop()

            # Yeni playlist oluştur
            new_playlist = sp.user_playlist_create(
                user=user["id"],
                name=f"Mood Mix: {mood} 🎯 (v2)",
                public=True,
                description="Mood Mixer v2 ile Spotify önerileriyle hazırlandı 🎧 https://mixer.alxishq.site"
            )

            # Şarkıları 100'erli ekle
            for i in range(0, len(recommended_ids), 100):
                sp.playlist_add_items(new_playlist["id"], recommended_ids[i:i+100])

            st.success("✅ Yeni mood playlistin hazır!")
            st.balloons()
            st.markdown(f"### 🎶 **{new_playlist['name']}** ({len(recommended_ids)} şarkı)")
            st.markdown(f"→ [Spotify'da Aç]({new_playlist['external_urls']['spotify']})")

        except Exception as e:
            st.error(f"Hata: {str(e)}")
            st.info("Playlist herkese açık mı? Link doğru mu? Tekrar dene.")

# Alt bilgi
st.caption("Made with ❤️ by Sad_Always – Mood Mixer v2 (Spotify Recommendations) | https://alxishq.site")
