#%%
from discoverWeeklyTracker import (
    Song,
    DiscoverWeekly,
    Session,
    association_table,
    engine,
)
import pandas as pd
import matplotlib.pyplot as plt
import sqlalchemy as sa
from datetime import date

#%%
with Session() as session:
    subq = (
        session.query(sa.func.count(association_table.c.song_id))
        .filter(association_table.c.song_id == Song.id)
        .scalar_subquery()
    )
    items = session.query(Song).filter(subq > 1).order_by(subq).all()
    df = pd.DataFrame([item.as_dict() for item in items])

# %%
df["times_seen"] = df.apply(lambda row: len(row["mixes"]), axis=1)
df["first_seen"] = df.apply(
    lambda row: min([mix for mix in row["mixes"] if mix > date(2001, 1, 1)]), axis=1
)

#%%
with Session() as session:
    mixes = session.query(DiscoverWeekly).all()
    mixes_list = []
    for mix in mixes:
        if mix.date < date(2001, 1, 1):
            continue
        new_songs = 0
        for song in mix.songs:
            first_seen = min(
                [smix.date for smix in song.mixes if smix.date > date(2001, 1, 1)]
            )
            if first_seen == mix.date:
                new_songs += 1
        mixes_list.append({"date": mix.date, "new_songs": new_songs})
    df_mixes = pd.DataFrame(mixes_list)
# %%
df_mixes.plot("date", "new_songs", kind="bar", grid=True, figsize=(20, 10))
print(df_mixes["new_songs"].mean())
plt.xticks(rotation=90)
plt.savefig("plots/new_songs_per_week.jpg")
pass
