
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from smart_cradle_server import User, Agent, SensorData, VideoFrame, db
import cv2
import numpy as np
from io import BytesIO

# --- Database Connection ---
def get_db_session():
    sql_uri = os.getenv('SQLALCHEMY_DATABASE_URI')
    if not sql_uri:
        db_user = os.getenv('MYSQL_USER', 'sc_user')
        db_pass = os.getenv('MYSQL_PASSWORD', 'SC_password_12!45')
        db_host = os.getenv('MYSQL_HOST', '34.121.73.128')
        db_port = os.getenv('MYSQL_PORT', '3306')
        db_name = os.getenv('MYSQL_DATABASE', 'smartcradle')
        sql_uri = f'mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}'
    
    engine = create_engine(sql_uri)
    Session = sessionmaker(bind=engine)
    return Session()

# --- Data Loading ---
def load_agents(session):
    return session.query(Agent).all()

def load_sensor_data(session, agent_id, start_date, end_date):
    query = session.query(SensorData).filter(
        SensorData.agent_id == agent_id,
        SensorData.timestamp.between(start_date, end_date)
    ).order_by(SensorData.timestamp)
    return pd.read_sql(query.statement, query.session.bind)

def load_video_frames(session, agent_id, start_time, end_time):
    return session.query(VideoFrame).filter(
        VideoFrame.agent_id == agent_id,
        VideoFrame.timestamp.between(start_time, end_time)
    ).order_by(VideoFrame.timestamp).all()

# --- Video Processing ---
def create_video_from_frames(frames):
    if not frames:
        return None

    # Use in-memory file
    output_bytes = BytesIO()
    
    # Assuming all frames have the same dimensions
    frame_data = frames[0].frame
    nparr = np.frombuffer(frame_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    height, width, layers = img.shape
    size = (width, height)

    # Use avc1 for broader browser compatibility (H.264)
    fourcc = cv2.VideoWriter_fourcc(*'avc1') 
    # Use a temporary file name for the writer, but we write to memory
    out = cv2.VideoWriter('temp.mp4', fourcc, 10, size)

    for frame_obj in frames:
        nparr = np.frombuffer(frame_obj.frame, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        out.write(img)
    
    out.release()

    # This part is tricky as VideoWriter writes to a file path.
    # A common workaround is to write to a temp file and read it back.
    # For a pure in-memory solution, other libraries might be needed,
    # but this is a practical approach for Streamlit.
    with open('temp.mp4', 'rb') as f:
        output_bytes.write(f.read())
    
    os.remove('temp.mp4') # Clean up the temp file
    
    output_bytes.seek(0)
    return output_bytes

# --- Streamlit UI ---
st.set_page_config(layout="wide")
st.title("Smart Cradle Data Viewer")

db_session = get_db_session()

# Agent Selection
agents = load_agents(db_session)
agent_dict = {agent.uuid: agent.id for agent in agents}
selected_uuid = st.sidebar.selectbox("Select a Cradle (Agent)", list(agent_dict.keys()))

if selected_uuid:
    agent_id = agent_dict[selected_uuid]

    # Date Range Selection
    st.sidebar.header("Select Date Range")
    start_date = st.sidebar.date_input("Start Date", pd.to_datetime("today").normalize() - pd.Timedelta(days=1))
    end_date = st.sidebar.date_input("End Date", pd.to_datetime("today").normalize() + pd.Timedelta(days=1))

    # Load Sensor Data
    sensor_df = load_sensor_data(db_session, agent_id, start_date, end_date)

    st.header(f"Sensor Data for {selected_uuid}")

    if not sensor_df.empty:
        # Data Cleaning and Preparation
        sensor_df['timestamp'] = pd.to_datetime(sensor_df['timestamp'])
        sensor_df.set_index('timestamp', inplace=True)

        # Plotting
        st.subheader("Temperature Over Time")
        st.line_chart(sensor_df['temperature'].dropna())

        st.subheader("Crying Detection Over Time")
        crying_df = sensor_df['crying'].dropna().str.get_dummies()
        if not crying_df.empty:
            st.bar_chart(crying_df)
        else:
            st.write("No crying detection data available for this period.")

        st.subheader("Direction Over Time")
        direction_df = sensor_df['direction'].dropna().str.get_dummies()
        if not direction_df.empty:
            st.bar_chart(direction_df)
        else:
            st.write("No direction data available for this period.")

    else:
        st.write("No sensor data available for the selected date range.")

    # Video Playback Section
    st.header("Video Playback")
    st.sidebar.header("Select Video Time")
    video_date = st.sidebar.date_input("Video Date", pd.to_datetime("today").normalize())
    video_time = st.sidebar.time_input("Video Start Time", pd.to_datetime("now").time())

    selected_datetime = pd.to_datetime(f"{video_date} {video_time}")
    end_datetime = selected_datetime + pd.Timedelta(minutes=1)

    st.write(f"Attempting to load video from {selected_datetime} to {end_datetime}")

    if st.sidebar.button("Load Video"):
        video_frames = load_video_frames(db_session, agent_id, selected_datetime, end_datetime)
        
        if video_frames:
            st.write(f"Found {len(video_frames)} frames. Creating video...")
            video_bytes = create_video_from_frames(video_frames)
            if video_bytes:
                st.video(video_bytes, format='video/mp4')
            else:
                st.write("Could not create video from frames.")
        else:
            st.write("No video frames found for the selected time range.")

db_session.close()
