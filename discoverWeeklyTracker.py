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

logging.basicConfig(filename=basePath / "discoverWeekly.log", level=logging.INFO)

dbPath = "sqlite:///{}".format(basePath / "discoverWeekly.db")
engine = create_engine("sqlite:///discoverWeekly.db")
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
    user: spotipy.Spotify, discoverWeekly_id="37i9dQZEVXcEQGHXUmK96b"
):
    logging.info("getting playlist tracks...")
    tracks = user.playlist_tracks(discoverWeekly_id)
    songs = []
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
        session.commit()


user, sp = authenticate()
getDiscoverWeekly(sp)
