import spotipy
from pathlib import Path
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
import toml
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, Float
from sqlalchemy.orm import sessionmaker, relationship

basePath = Path(__file__).parent

logging.basicConfig(
    filename=basePath / "discoverWeekly.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-5.5s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

dbPath = "sqlite:///{}".format(basePath / "discoverWeekly.db")
engine = create_engine(dbPath)
Session = sessionmaker(bind=engine)
Base = declarative_base()


class Song(Base):
    __tablename__ = "songs"

    id = Column(String, primary_key=True, nullable=False)
    name = Column(String)
    times_seen = Column(Integer)

    def __repr__(self):
        return f"<Song(id={self.id}, name={self.name}, times_seen={self.times_seen})>"


Base.metadata.create_all(engine, checkfirst=True)


def authenticate():
    config = toml.load(basePath / "conf.toml")
    redirectUrl = "https://example.com/callback"
    scope = " ".join(
        [
            "user-read-currently-playing",
            "user-read-playback-state",
            "user-modify-playback-state",
            "user-library-read",
            "playlist-modify-private",
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
    return user, sp


def getDiscoverWeekly(
    user: spotipy.Spotify,
    discoverWeekly_id="37i9dQZEVXcEQGHXUmK96b",
    newDiscoverWeekly_id="10fTxvB9wxLtKuML78Z6CF",
):
    logging.info("getting playlist tracks...")
    tracks = user.playlist_tracks(discoverWeekly_id)

    songs = []
    songs_new = []
    for track in tracks["items"]:
        song = track["track"]["name"]
        song_id = track["track"]["id"]
        artists = [artist["name"] for artist in track["track"]["artists"]]
        songs.append((song_id, song, artists))

    logging.info("updating database...")
    with Session() as session:
        for song_id, name, artists in songs:
            song = session.query(Song).get(song_id)
            if song:
                song.times_seen += 1
            else:
                session.add(Song(id=song_id, name=name, times_seen=1))
                artist = " ".join(artists)
                logging.info(f"new Song: {name} - {artist} ({song_id})")
                songs_new.append(song_id)
        session.commit()
    user.playlist_replace_items(newDiscoverWeekly_id, songs_new)


user, sp = authenticate()

newDiscoverWeekly_id = "10fTxvB9wxLtKuML78Z6CF"
songs_new = [
    "1HHVtk0s64vSd2JxV03ynL",
    "7xK4mAIgIl7GRBGZKB9QXg",
    "2E0EXqwsXELsjYSCWHy65K",
    "3VZi5FjfKrL4S4NdMbce3J",
    "1Yjvp84kzDJ8HD3tRJr0T5",
    "0IXehCQY9Z9VwvCizoBauQ",
    "3JvCIGIzV5zwbF1EyReMTt",
    "2VlzXciW7QtomIOX3pmSMh",
    "4OXIMXSvmAuHIL4UuLCglf",
    "1hxxOv1emWViNUdqB5Uxe4",
    "6AF2f2H7hOsjHrrz8PBpIG",
    "4xyIOOcc0Yuv8mvcCn7biw",
    "1wKy1UGBNH8B7lTfxX4wm0",
    "5Jklf7IZm5sx7LvdYH84BA",
    "5NS2A4JYWEINqBeUt3uMrm",
    "4YQQL4MFAqFnkt4BMOIJxm",
    "3ZQpms23dgtgox86dd7eGV",
    "4ChDxebZnqV99jCzi7db9g",
    "6h2TL4YWi12yc5QctcRwFk",
    "5M9AvxuVkrY5j9OQkkn5kM",
    "2oAm3NUdqpNEAER7jGvT9f",
    "2h6jNrLsGagxnWnvBXWtyn",
    "2ByYZXoDr2EytEmHXemogT",
]

user.playlist_replace_items(newDiscoverWeekly_id, songs_new)


# getDiscoverWeekly(sp)
