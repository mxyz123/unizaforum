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
    if not len(sys.argv) < 4:
        cur.execute(f"INSERT into USER (email, username, pswd, admin, gif) "
                    f"VALUES ('{sys.argv[1]}', '{sys.argv[2]}', '{encrypt(sys.argv[3])}', TRUE, FALSE);")
        mydb.commit()
        mydb.close()
        copy("static/pfp/pfp_.png", f"static/pfp/{sys.argv[1]}.png")
        print("Admin account created successfully.")
    else:
        email = input("Email: ")
        username = input("username: ")
        password = input("password: ")
        cur.execute(f"INSERT into USER (email, username, pswd, admin, gif) "
                    f"VALUES ('{email}', '{username}', '{encrypt(password)}', TRUE, FALSE);")
        mydb.commit()
        mydb.close()
        copy("static/pfp/pfp_.png", f"static/pfp/{username}.png")
        print("Admin account created successfully.")
