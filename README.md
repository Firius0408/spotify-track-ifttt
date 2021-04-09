# Spotify Track

Simple python scripts to track users playlists for new song updates and push notifications through IFTTT

## Setup

This project uses Python 3.9 and pipenv, and SQLite for database

Spotify API keys and IFTTT webhook should be placed in `.env`:

`SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET`, and `IFTTT_URL`

The users to be tracked should be placed `users.py` as a list called `users`

```python
python3 -m pip install pipenv
pipenv install
pipenv run python3 setupdatabase.py
```

## Tracking

The `track.py` script scans for songs and playlists added or created since the last runtime

`pipenv run python3 track.py`

## Redo

Sometimes the script can fail on a run. To redo the run:

`pipenv run python3 track.py redo`

Copyright © Brian Cheng 2021
