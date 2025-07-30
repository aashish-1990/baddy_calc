import streamlit as st
import pandas as pd

st.set_page_config(page_title="Badminton Price Sharing Calculator", layout="centered")

st.title("🏸 Badminton Price Sharing Calculator")
st.markdown("**Split court costs easily, fairly, and instantly after every session!**")

# --- Booking Inputs ---
st.header("Court Booking Details")
num_courts = st.number_input("Number of courts", min_value=1, value=1)
session_duration_hr = st.number_input("Duration per court (in hours)", min_value=0.25, value=1.0, step=0.25)
hourly_rate = st.number_input("Hourly rate per court (₹)", min_value=1, value=600)

total_cost = num_courts * session_duration_hr * hourly_rate
st.write(f"**Total cost for booking:** ₹{total_cost:.2f}")

# --- Player Inputs ---
st.header("Players & Playtime")
num_players = st.number_input("Number of players", min_value=2, value=4)
player_data = []

booker_idx = st.radio("Who booked & paid in advance?", options=list(range(num_players)), format_func=lambda x: f"Player {x+1}")

st.write("*Enter 0 for minutes if absent (absentees pay nothing).*")

for i in range(int(num_players)):
    col1, col2 = st.columns([2, 1])
    with col1:
        name = st.text_input(f"Player {i+1} name", value=f"Player{i+1}", key=f"name_{i}")
    with col2:
        mins = st.number_input(f"Minutes played", min_value=0, max_value=int(session_duration_hr*60), value=int(session_duration_hr*60), key=f"mins_{i}")
    player_data.append({"name": name.strip(), "minutes_played": mins})

booker_name = player_data[booker_idx]['name']

# --- Calculation ---
present_players = [p for p in player_data if p['minutes_played'] > 0]
total_played_minutes = sum(p['minutes_played'] for p in present_players)

if total_played_minutes == 0:
    st.warning("No one played! Please enter valid minutes for at least one player.")
else:
    st.subheader("Settlement Results")
    result_data = []
    total_shares = 0
    for p in present_players:
        share = total_cost * (p['minutes_played'] / total_played_minutes)
        is_booker = p['name'] == booker_name
        settlement = -share if is_booker else share
        total_shares += share
        result_data.append({
            "Player": p['name'],
            "Minutes Played": p['minutes_played'],
            "Share (₹)": round(share, 2),
            "To Pay (+)/Receive (-)": round(settlement, 2)
        })

    df = pd.DataFrame(result_data)
    st.dataframe(df, hide_index=True)

    st.markdown(f"**Booker ({booker_name}) paid ₹{total_cost:.2f} in advance.**")
    pay_to_booker = df[df["To Pay (+)/Receive (-)"] > 0][["Player", "To Pay (+)/Receive (-)"]]
    if not pay_to_booker.empty:
        st.markdown("### Who Pays the Booker:")
        for _, row in pay_to_booker.iterrows():
            st.write(f"- {row['Player']} pays ₹{row['To Pay (+)/Receive (-)']:.2f} to {booker_name}")

    st.markdown(f"*Total shares add up to: ₹{total_shares:.2f}*")

st.caption("Created by Aashish Sharma | Powered by Streamlit")
