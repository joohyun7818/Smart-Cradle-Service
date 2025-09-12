#!/usr/bin/env python3
"""
Cleanup script to remove frames older than a retention period and delete DB rows.
Usage: python3 scripts/cleanup_old_data.py --frames-days 7 --sensors-days 30
"""
import os
import argparse
import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DEFAULT_DB_URL = os.getenv('SQLALCHEMY_DATABASE_URI')

parser = argparse.ArgumentParser()
parser.add_argument('--frames-days', type=int, default=7)
parser.add_argument('--sensors-days', type=int, default=30)
parser.add_argument('--db-url', type=str, default=DEFAULT_DB_URL)
args = parser.parse_args()

if not args.db_url:
    raise SystemExit('DB URL not provided via --db-url or SQLALCHEMY_DATABASE_URI env')

engine = create_engine(args.db_url)
Session = sessionmaker(bind=engine)

threshold_frames = datetime.datetime.utcnow() - datetime.timedelta(days=args.frames_days)
threshold_sensors = datetime.datetime.utcnow() - datetime.timedelta(days=args.sensors_days)

with Session() as session:
    # 1) Find old frames to delete
    rows = session.execute(text('SELECT id, path FROM frames WHERE created_at < :t'), {'t': threshold_frames.isoformat()}).fetchall()
    for r in rows:
        fid = r[0]
        path = r[1]
        try:
            if os.path.exists(path):
                os.remove(path)
                print(f'Deleted file {path}')
        except Exception as e:
            print('Failed to delete file', path, e)
        # delete DB row
        session.execute(text('DELETE FROM frames WHERE id = :id'), {'id': fid})
    session.commit()

    # 2) Delete old sensor readings
    res = session.execute(text('DELETE FROM sensor_readings WHERE created_at < :t'), {'t': threshold_sensors.isoformat()})
    print('Deleted sensor rows:', res.rowcount)
    session.commit()
