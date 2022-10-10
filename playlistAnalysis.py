import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
import toml
from pprint import pprint

config = toml.load("conf.toml")
redirectUrl = "https://example.com/callback"
scope = " ".join(
    [
        "user-read-currently-playing",
        "user-read-playback-state",
        "playlist-modify-private",
        "user-modify-playback-state",
        "user-library-read",
        "playlist-modify-public",
        "app-remote-control",
    ]
)
clientId = config["CLIENT_ID"]
clientSecret = config["CLIENT_SECRET"]

user = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=clientId,
        client_secret=clientSecret,
        redirect_uri=redirectUrl,
        scope=scope,
    )
)

sp = spotipy.Spotify(
    client_credentials_manager=SpotifyClientCredentials(
        client_id=clientId, client_secret=clientSecret
    )
)


def getCurrentPlaybackInfo(user: spotipy.Spotify):

    currentPlayback = user.current_playback()
    if currentPlayback and currentPlayback["currently_playing_type"] == "track":
        song = currentPlayback["item"]["name"]
        song_id = currentPlayback["item"]["id"]
        artists = [artist["name"] for artist in currentPlayback["item"]["artists"]]
        album = currentPlayback["item"]["album"]["name"]
        cover_url = currentPlayback["item"]["album"]["images"][-1]["url"]
        length_ms = currentPlayback["item"]["duration_ms"]
        position = currentPlayback["progress_ms"]

        print(
            f"{song} - {', '.join(artists)}: {position/1000}/{length_ms/1000}, {cover_url}"
        )


if __name__ == "__main__":

    getCurrentPlaybackInfo(user)
# song = spotify.audio_analysis(id)
# pprint(song)
# if __name__ == "__main__":
#     data = pd.read_csv("playlist_of_doom(1).csv")
#     cols = [
#         #        "Album Release Date",
#         # "Track Duration (ms)",
#         "Popularity",
#         # "Added At",
#         "Danceability",
#         "Energy",
#         "Key",
#         "Loudness",
#         "Mode",
#         "Speechiness",
#         "Acousticness",
#         "Instrumentalness",
#         "Liveness",
#         "Valence",
#         "Tempo",
#         "Time Signature",
#     ]
#     genreCols = ["Album Genres", "Artist Genres"]
#     for c in cols:
#         #     # maxRow = data.iloc[data[c].idxmax()]
#         #     # minRow = data.iloc[data[c].idxmin()]
#         print(f"{c}:")
#         #     # print(f"max: {maxRow['Track Name']} by {maxRow['Artist Name']}: {maxRow[c]}")
#         #     # print(f"max: {minRow['Track Name']} by {minRow['Artist Name']}: {minRow[c]}")
#         #     # print("")

#         sorted_df = data.sort_values(by=c)
#         print(sorted_df.loc[:, ["Track Name", "Artist Name", c]])

#     sorted_by_length = data.sort_values(by="Track Duration (ms)")
#     sorted_by_length["Track Duration (ms)"] /= 1000 * 60
#     print(sorted_by_length.loc[:, ["Track Name", "Artist Name", "Track Duration (ms)"]])
