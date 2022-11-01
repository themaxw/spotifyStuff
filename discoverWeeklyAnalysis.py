from discoverWeeklyTracker import Song, DiscoverWeekly, Session, association_table
from playlistAnalysis import sp
from tqdm import tqdm

import sqlalchemy as sa

from typing import List


def getTracksInfo(tracks: List[Song]):
    tracks_info = []
    n_iter = int(round(len(tracks) / 50))
    for i_start, i_end in tqdm(
        [(i * 50, min((i + 1) * 50, len(tracks))) for i in range(n_iter)]
    ):
        tracks_info.extend(
            sp.tracks([item.id for item in tracks[i_start:i_end]])["tracks"]
        )

    return tracks_info


with Session() as session:
    # items: List[Song] = session.query(Song).filter(func.length(Song.mixes) > 1).all()

    # query all songs with more than one mix
    subq = (
        session.query(sa.func.count(association_table.c.song_id))
        .filter(association_table.c.song_id == Song.id)
        .scalar_subquery()
    )
    items = session.query(Song).filter(subq > 1).order_by(subq).all()
    # items = session.query(Song).filter(Song.artist == "Powermad").all()
    print(len(items))
    for i in items:
        print(i)

    # tracks = getTracksInfo(items)
    # for track in tracks:
    #     if track is None:
    #         print("yo wtf")
    #     for artist in track["artists"]:
    #         if artist["name"] == "Ulver":
    #             print(track["name"])
    #             # print(f"{track['artists']} \t\t\t {track['name']}")
