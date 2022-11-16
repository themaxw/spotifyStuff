import spotipy
from pathlib import Path
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
import toml
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, Float, Table, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
import datetime

basePath = Path(__file__).parent
cachePath = basePath / ".cache"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-5.5s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(basePath / "discoverWeekly.log"),
        logging.StreamHandler(),
    ],
)

dbPath = "sqlite:///{}".format(basePath / "discoverWeekly.db")
engine = create_engine(dbPath)
Session = sessionmaker(bind=engine)
Base = declarative_base()


association_table = Table(
    "association_table",
    Base.metadata,
    Column("discoverWeekly_date", ForeignKey("discoverWeekly.date"), primary_key=True),
    Column("song_id", ForeignKey("songs.id"), primary_key=True),
)


class DiscoverWeekly(Base):
    __tablename__ = "discoverWeekly"
    date = Column(Date, primary_key=True, nullable=False)
    songs = relationship("Song", secondary=association_table, back_populates="mixes")


class Song(Base):
    __tablename__ = "songs"

    id = Column(String, primary_key=True)
    name = Column(String)
    artist = Column(String)
    album = Column(String)
    mixes = relationship(
        "DiscoverWeekly",
        secondary=association_table,
        back_populates="songs",
        order_by=DiscoverWeekly.date,
    )

    def as_dict(self):
        return {
            "name": self.name,
            "artist": self.artist,
            "mixes": [mix.date for mix in self.mixes],
        }

    def __repr__(self):
        return f"<Song(id={self.id}, artist={self.artist}, name={self.name}, times_seen={len(self.mixes)})>"


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
            cache_path=cachePath,
        )
    )

    sp = spotipy.Spotify(
        client_credentials_manager=SpotifyClientCredentials(
            client_id=clientId, client_secret=clientSecret
        )
    )
    return user, sp


def track_discover_weekly(
    user: spotipy.Spotify, discoverWeekly_id="37i9dQZEVXcEQGHXUmK96b"
):
    with Session() as session:
        if check_mix_already_tracked(session):
            logging.info("mix was already tracked")
            return

    logging.info("getting playlist tracks...")
    tracks = user.playlist_tracks(discoverWeekly_id)

    songs = []

    for track in tracks["items"]:
        song = track["track"]["name"]
        song_id = track["track"]["id"]
        album = track["track"]["album"]["name"]
        artists = " ".join([artist["name"] for artist in track["track"]["artists"]])
        songs.append((song_id, song, artists, album))

    logging.info("updating database...")
    with Session() as session:
        mix = get_this_weeks_mix(session)
        for song_id, name, artist, album in songs:
            song: Song = session.query(Song).get(song_id)
            if song:
                song.mixes.append(mix)
            else:
                session.add(
                    Song(id=song_id, name=name, album=album, artist=artist, mixes=[mix])
                )
                logging.info(f"new Song: {name} - {artist} ({song_id})")
        session.commit()


def update_playlist(
    user: spotipy.Spotify, newDiscoverWeekly_id="10fTxvB9wxLtKuML78Z6CF"
):

    with Session() as session:
        mix = get_this_weeks_mix(session)
        new_songs = [song.id for song in mix.songs if len(song.mixes) == 1]
        user.playlist_replace_items(newDiscoverWeekly_id, new_songs)
        logging.info("updated playlist")


def remove_mix(date: datetime.date = datetime.date.today()):
    """Use this after accidentally analysing a playlist twice a week"""
    with Session() as session:
        mix = get_this_weeks_mix(session)
        for song in mix.songs:
            if mix in song.mixes and len(song.mixes) == 1:
                session.delete(song)
            session.delete(mix)
        session.commit()


def check_mix_already_tracked(session, date: datetime.date = datetime.date.today()):
    monday = date - datetime.timedelta(days=date.weekday())
    mix = session.query(DiscoverWeekly).get(monday)
    return mix is not None and len(mix.songs) > 0


def get_this_weeks_mix(
    session, date: datetime.date = datetime.date.today()
) -> DiscoverWeekly:
    monday = date - datetime.timedelta(days=date.weekday())
    mix = session.query(DiscoverWeekly).get(monday)
    if not mix:
        mix = DiscoverWeekly(date=monday)
        session.add(mix)
    return mix


def fixAllOfThisWeek(user: spotipy.Spotify, discoverWeekly_id="37i9dQZEVXcEQGHXUmK96b"):
    """Use this after accidentally analysing a playlist twice a week

    Args:
        user (spotipy.Spotify): _description_
        discoverWeekly_id (str, optional): _description_. Defaults to "37i9dQZEVXcEQGHXUmK96b".
    """
    logging.info("getting playlist tracks...")
    tracks = user.playlist_tracks(discoverWeekly_id)
    logging.info("updating database...")
    with Session() as session:
        mix = get_this_weeks_mix(session)
        for track in tracks["items"]:
            song_id = track["track"]["id"]
            song = session.query(Song).get(song_id)
            if len(song.mixes) > 1:
                song.mixes[0] = mix
                logging.info([mix.date for mix in song.mixes])
        session.commit()


if __name__ == "__main__":

    user, sp = authenticate()
    # TODO fix everything, implement check to only check once
    track_discover_weekly(user)
    update_playlist(user)
    # fixAllOfThisWeek(user)
