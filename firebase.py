import pyrebase

from secrets import FIREBASE_URL, FIREBASE_KEY

ref = pyrebase.Firebase(FIREBASE_URL, FIREBASE_KEY)
