smart_cradle_server_v2

This folder contains a v2 of the server which stores sensor readings and frames into the database/filesystem.

Run:

1. Install dependencies

pip install -r requirements.txt

2. Configure environment variables (see ../smart_cradle_server/.env.example as reference)

3. Start

gunicorn -w 2 -b 0.0.0.0:8000 smart_cradle_server_v2:app

Notes:
- Frames are saved under $DATA_DIR/frames by default (/data/frames)
- Cleanup script available at ../scripts/cleanup_old_data.py
