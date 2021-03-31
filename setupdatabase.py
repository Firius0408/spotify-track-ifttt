import spotifywebapi
import sys
import os
import sqlite3
import datetime
import os
from users import users

CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID') 
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

if __name__ == '__main__':
    datafile = sys.path[0] + '/data.db'
else:
    datafile = './data.db'

try:
    os.remove(datafile)
except FileNotFoundError:
    pass

print(datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S") + '\n')
sp = spotifywebapi.Spotify(CLIENT_ID, CLIENT_SECRET)
conn = sqlite3.connect(datafile)
c = conn.cursor()
with conn:
    conn.execute("CREATE TABLE playlists (user text, playlistid text)")
    conn.execute("CREATE TABLE timepoint (timepoint text)")
    conn.execute("CREATE TABLE oldtimepoint (timepoint text)")
    conn.execute("INSERT INTO timepoint VALUES (?)", (datetime.datetime.utcnow().isoformat(),))
    conn.execute("INSERT INTO oldtimepoint VALUES (?)", (datetime.datetime.utcnow().isoformat(),))
for us in users:
    print('Starting user %s' % us)
    try:
        user = sp.getUser(us)
        playlists = sp.getUserPlaylists(user)
    except:
        print(sys.exc_info()[0])
        os.remove(datafile)
        exit(1)

    for playlist in playlists:
        conn.execute("INSERT INTO playlists VALUES (?, ?)", (us, playlist['id']))

    print('Finished user %s' % us)

print('Committing database...')
conn.commit()
print('Finished\n')
conn.close()
