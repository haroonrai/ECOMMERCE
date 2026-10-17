import os
import sqlite3
from seed_healthcare import seed_pure_healthcare

def seed_database(force=False):
    seed_pure_healthcare(force=force)

if __name__ == '__main__':
    seed_database(force=True)
