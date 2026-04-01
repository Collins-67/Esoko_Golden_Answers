import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Esoko Audio Explorer", layout="wide")

# --- CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Using ttl=60 so it refreshes data once per minute
# Replace "Annotations" with your actual tab name if different
df = conn.read(worksheet="Annotations", skiprows=1, ttl=60)

st.title("🎧 Esoko Hotline Audio Explorer")

# --- SIDEBAR FILTERS ---
st.sidebar.header("Filter Records")
if 'Lang_Detected' in df.columns:
    langs = st.sidebar.multiselect("Language", df['Lang_Detected'].unique())
    if langs:
        df = df[df['Lang_Detected'].isin(langs)]

# --- DATA TABLE ---
# Show all columns, but allow single-row selection
selection = st.dataframe(
    df, 
    use_container_width=True, 
    on_select="rerun", 
    selection_mode="single-row"
)

# --- AUDIO PLAYER LOGIC ---
if selection.selection.rows:
    selected_idx = selection.selection.rows[0]
    row = df.iloc[selected_idx]
    
    st.divider()
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("Play Recording")
        # Extract the S3 link from your 'File_Location' column
        audio_url = row['File_Location']
        
        if pd.notna(audio_url):
            st.audio(audio_url)
            st.write(f"**ID:** {row['Rec_ID']}")
        else:
            st.warning("No audio link found for this record.")

    with col_right:
        st.subheader("Details & Transcript")
        if 'Transcript_Excerpt' in row and pd.notna(row['Transcript_Excerpt']):
            st.info(row['Transcript_Excerpt'])
        
        if 'Decision' in row:
            st.write(f"**Decision:** {row['Decision']}")
else:
    st.info("💡 Select a row above to listen to the audio.")