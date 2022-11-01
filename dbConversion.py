import logging
from datetime import date
from pathlib import Path
from pprint import pprint

import spotipy
import toml
from spotipy.oauth2 import SpotifyClientCredentials
from sqlalchemy import (
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (
    relationship,
    sessionmaker,
)


basePath = Path(__file__).parent
logging.basicConfig(
    filename=basePath / "discoverWeeklyConversion.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-5.5s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# spotify API bizniz
config = toml.load("conf.toml")
clientId = config["CLIENT_ID"]
clientSecret = config["CLIENT_SECRET"]
sp = spotipy.Spotify(
    client_credentials_manager=SpotifyClientCredentials(
        client_id=clientId, client_secret=clientSecret
    )
)


# DB bizniz
dbPath_old = "sqlite:///{}".format(basePath / "discoverWeekly.db")
dbPath_new = "sqlite:///{}".format(basePath / "discoverWeekly_new.db")

engine_old = create_engine(dbPath_old)
Session_old = sessionmaker(bind=engine_old)
Base_old = declarative_base()

engine_new = create_engine(dbPath_new)
Session_new = sessionmaker(bind=engine_new)
Base = declarative_base()


# OLD DATABASE
class Song_old(Base_old):
    __tablename__ = "songs"

    id = Column(String, primary_key=True, nullable=False)
    name = Column(String)
    times_seen = Column(Integer)

    def __repr__(self):
        return f"<Song(id={self.id}, name={self.name}, times_seen={self.times_seen})>"


Base_old.metadata.create_all(engine_old, checkfirst=True)

# NEW DATABASE


# class Base(DeclarativeBase):
#     pass


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

    def __repr__(self):
        return f"<Song(id={self.id}, artist={self.artist}, name={self.name}, times_seen={len(self.mixes)})>"


Base.metadata.create_all(engine_new, checkfirst=True)


def divide_chunks(l, n):

    # looping till length l
    for i in range(0, len(l), n):
        yield l[i : i + n]


def read_log(file: Path):
    d = {}

    with open(file) as f:
        for line in f:
            if line[29:].startswith("new Song"):
                date_added = date.fromisoformat(line[:10])
                id = line[-24:-2]
                d[id] = {"date": date_added}

    # get more info from spotify
    for chunk in divide_chunks(list(d.keys()), 50):
        tracks = sp.tracks(chunk)
        for t in tracks["tracks"]:
            print(type(t))
            id = t["id"]
            album = t["album"]["name"]
            artists = ", ".join([a["name"] for a in t["artists"]])
            d[id]["album"] = album
            d[id]["artist"] = artists
    return d


if __name__ == "__main__":
    date_dict = read_log(basePath / "discoverWeekly.log")

    with Session_old() as s_old, Session_new() as s_new:
        # create dummy dates
        dummy_dates = [
            DiscoverWeekly(date=date.fromisoformat(date_str))
            for date_str in ["2000-01-01", "2000-01-02", "2000-01-03"]
        ]
        for d in dummy_dates:
            s_new.add(d)

        # iterate over all old songs
        songs: list[Song_old] = s_old.query(Song_old).all()
        for i, song in enumerate(songs):
            # get artist name etc
            album = date_dict[song.id]["album"]
            artist = date_dict[song.id]["artist"]
            date_first_seen = date_dict[song.id]["date"]

            # add first mix
            mix = s_new.query(DiscoverWeekly).get(date_first_seen)
            if not mix:
                mix = DiscoverWeekly(date=date_first_seen)
                s_new.add(mix)

            new_song = Song(id=song.id, album=album, artist=artist, name=song.name)
            new_song.mixes.append(mix)
            if song.times_seen > 1:
                new_song.mixes.extend(dummy_dates[: song.times_seen - 1])
            s_new.add(new_song)
        s_new.commit()
        for mix in s_new.query(DiscoverWeekly).all():
            print(mix.songs)
