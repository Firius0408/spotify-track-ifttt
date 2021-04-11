import requests
import spotifywebapi
import sys
import sqlite3
import datetime
import os
import signal
from concurrent.futures import ThreadPoolExecutor, wait
from users import users

CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID') 
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
IFTTT_URL = os.getenv('IFTTT_URL')

def interruptHandler(signum, frame):
    print('Signal %s intercepted, shutting down and reverting state' % signal.strsignal(signum))
    conn.execute("DROP TABLE tempplaylists")
    conn.commit()
    conn.interrupt()
    conn.close()
    exit(1)

signal.signal(signal.SIGINT, interruptHandler)
signal.signal(signal.SIGABRT, interruptHandler)
signal.signal(signal.SIGHUP, interruptHandler)
signal.signal(signal.SIGTERM, interruptHandler)
def addTrackIds(playlist, temptrackids):
    playlistid = playlist['id']
    try:
        tracks = sp.getTracksFromItem(playlist)
    except spotifywebapi.SpotifyError as err:
        print(err)
        return

    trackids = [track['track']['id'] for track in tracks if datetime.datetime.strptime(track['added_at'], '%Y-%m-%dT%H:%M:%SZ') > offset and track['track'] is not None and track['track']['id'] is not None]
    if trackids:
        temptrackids[playlistid] = trackids

redo_flag = False
if __name__ == '__main__':
    datafile = sys.path[0] + '/data.db'
    if len(sys.argv) > 1 and sys.argv[1] == 'redo':
        redo_flag = True
else:
    datafile = './data.db'

print('Starting at ' + datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") + ' UTC')
sp = spotifywebapi.Spotify(CLIENT_ID, CLIENT_SECRET)
conn = sqlite3.connect(datafile)
with conn:
    conn.execute("CREATE TABLE tempplaylists (user text, playlistid text)")
    if redo_flag is False:
        oldtime = conn.execute("SELECT timepoint FROM timepoint").fetchone()[0]
        offset = datetime.datetime.fromisoformat(oldtime)
        print('Using UTC offset of ' + offset.strftime("%Y-%m-%d %H:%M:%S") + '\n')
        conn.execute("DELETE FROM timepoint")
        conn.execute("DELETE FROM oldtimepoint")
        conn.execute("INSERT INTO timepoint VALUES (?)", (datetime.datetime.utcnow().isoformat(),))
        conn.execute("INSERT INTO oldtimepoint VALUES (?)", (oldtime,))
    else:
        oldtime = conn.execute("SELECT timepoint FROM oldtimepoint").fetchone()[0]
        offset = datetime.datetime.fromisoformat(oldtime)
        print('Using old UTC offset of ' + offset.strftime("%Y-%m-%d %H:%M:%S") + '\n')

executor = ThreadPoolExecutor()
for us in users:
    print('Starting user %s' % us)
    try:
        user = sp.getUser(us)
    except:
        print('Error with user %s: %s' % (us, sys.exc_info()[1]))
        continue
    try:
        playlists = sp.getUserPlaylists(user)
    except:
        print('Error with user %s playlists: %s' % (us, sys.exc_info()[1]))
        continue

    print('Finished pulling playlists')
    temptrackids = {}
    futures = []
    for playlist in playlists:
        if "Top Songs " in playlist['name'] or playlist['owner']['id'] != us:
            continue

        with conn:
            conn.execute("INSERT INTO tempplaylists VALUES (?, ?)", (us, playlist['id']))
        futures.append(executor.submit(addTrackIds, playlist, temptrackids))

    wait(futures)
    
    print('Finished pulling tracks')
    with conn:
        tempc = conn.execute("SELECT playlistid FROM tempplaylists WHERE user=? AND playlistid NOT IN (SELECT playlistid FROM playlists WHERE user=?)", (us, us))
    playlistids = tempc.fetchall()
    for i in playlistids:
        temp = sp.getPlaylistFromId(i[0])
        value1 = 'New playlist {} detected for user {}'.format(temp['name'], us)
        value3 = temp['external_urls']['spotify']
        payload = {'value1': value1, 'value2': None, 'value3': value3}
        r = requests.post(IFTTT_URL, data=payload)
    
    for k,v in temptrackids.items():
        temp = sp.getPlaylistFromId(k)
        tracks = sp.getTracksFromIds(v)
        tracknames = [track['name'] for track in tracks]
        value1 = 'New song(s) detected in playlist {} for user {}'.format(temp['name'], us)
        value2 = ', '.join(tracknames)
        value3 = temp['external_urls']['spotify']
        payload = {'value1': value1, 'value2': value2, 'value3': value3}
        r = requests.post(IFTTT_URL, data=payload)
    
    print('Finished user %s' % us)

executor.shutdown()
with conn:
    conn.execute("DROP TABLE playlists")
    conn.execute("ALTER TABLE tempplaylists RENAME TO playlists")
print('Committing database...')
conn.commit()
print('\nFinished at ' + datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S") + '\n')
conn.close()
