import os
import sys
import sqlite3
from hashing import encrypt
from shutil import copy

if __name__ == '__main__':
    if not os.path.exists("instance/uniza_forum.db"):
        print("Database doesn't exist yet, run the server to create it!")
        exit()
    mydb = sqlite3.connect("instance/uniza_forum.db")
    cur = mydb.cursor()
    username = input("username: ")
    gif = cur.execute(f"SELECT gif FROM USER WHERE username='{username}'")
    cur.execute(f"DELETE FROM USER WHERE username='{username}'")
    mydb.commit()
    mydb.close()
    if gif is True:
        os.remove(f"static/pfp/{username}.gif")
    else:
        os.remove(f"static/pfp/{username}.png")
    print("Account deleted successfully.")
