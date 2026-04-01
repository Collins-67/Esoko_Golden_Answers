import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="Esoko Audio Transcript", layout="wide")

# --- CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Using ttl=60 so it refreshes data once per minute
# Replace "Annotations" with your actual tab name if different
df = conn.read(worksheet="Annotations", skiprows=1, ttl=60)

st.title("🎧 Esoko Audio Transcript")

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

# Define keywords for your "Operational" template
weather_words = ['rain', 'forecast', 'mm', 'humidity', 'tomorrow']
action_words = ['spray', 'dry', 'ml', 'amount', 'days', 'dosage']

def check_is_golden(row):
    # Combines question and answer to look for keywords
    text = f"{row.get('Q1', '')} {row.get('A1', '')}".lower()
    has_weather = any(w in text for w in weather_words)
    has_action = any(a in text for a in action_words)
    return has_weather and has_action

# Create the virtual column
df['is_gold_candidate'] = df.apply(check_is_golden, axis=1)

# 3. SIDEBAR FILTERS
st.sidebar.header("Gold Standard Selection")
gold_only = st.sidebar.toggle("Show Operational Matches Only", value=False)

# If toggle is on, filter the dataframe
if gold_only:
    df_display = df[df['is_gold_candidate'] == True]
else:
    df_display = df

# 4. MAIN TABLE
st.title("🚜 Operational QA Training Pipeline")
selection = st.dataframe(
    df_display, 
    use_container_width=True, 
    on_select="rerun", 
    selection_mode="single-row"
)

# --- AUDIO & Q&A SECTION ---
if selection.selection.rows:
    selected_index = selection.selection.rows[0]
    row = df.iloc[selected_index]
    
    st.divider()
    
    # Create two columns: Left for Audio, Right for Q&A/Score
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Play Recording")
        # Extract the S3 link safely
        audio_link = row.get('File_Location')
        
        if pd.notna(audio_link) and str(audio_link).startswith("http"):
            st.audio(audio_link)
            st.caption(f"Recording ID: {row.get('Rec_ID', 'Unknown')}")
        else:
            st.warning("⚠️ No valid audio link found for this record.")
            
        # Optional: Show transcript excerpt here if you want it under the player
        if 'Transcript_Excerpt' in row and pd.notna(row['Transcript_Excerpt']):
            st.info(f"**Transcript Excerpt:**\n\n{row['Transcript_Excerpt']}")

    with col2:
        st.subheader("Q&A & Quality")
        
        # Check for Q1 and display chat style
        if 'Q1' in row and pd.notna(row['Q1']):
            st.chat_message("user").write(row['Q1'])
            # Only show A1 if Q1 exists
            if 'A1' in row and pd.notna(row['A1']):
                st.chat_message("assistant").write(row['A1'])
        else:
            st.write("_No Q&A pairs recorded._")
        
        st.divider()
        
        # Safe Quality Score display
        score = row.get('Composite_Score', 'N/A')
        st.write(f"**Quality Score:** {score}/5.0")
        
        # Safe Rejection Reason display
        if 'Rejection_Reason' in row and pd.notna(row['Rejection_Reason']):
            st.error(f"**Rejection Reason:** {row['Rejection_Reason']}")

else:
    # This shows when the app first loads or no row is clicked
    st.info("💡 Click a row in the table above to listen to the recording and see details.")
