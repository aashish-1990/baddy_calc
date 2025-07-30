import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
from PIL import Image

st.set_page_config(page_title="Badminton Price Sharing Calculator", layout="centered")

st.title("🏸 Badminton Price Sharing Calculator + UPI Payment")
st.markdown("**Split court costs instantly – pay and settle with UPI in one click!**")

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

player_names = []
for i in range(int(num_players)):
    col1, col2 = st.columns([2, 1])
    with col1:
        name = st.text_input(f"Player {i+1} name", value=f"Player{i+1}", key=f"name_{i}")
    with col2:
        mins = st.number_input(f"Minutes played", min_value=0, max_value=int(session_duration_hr*60), value=int(session_duration_hr*60), key=f"mins_{i}")
    player_data.append({"name": name.strip(), "minutes_played": mins})
    player_names.append(name.strip())

booker_idx = st.radio("Who booked & paid in advance?", options=list(range(num_players)), format_func=lambda x: player_names[x])
booker_name = player_data[booker_idx]['name']
booker_upi_id = st.text_input("Booker's UPI ID (for payment links & QR)", value="aashish@ybl")

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
    pay_to_booker = df[(df["Player"] != booker_name) & (df["To Pay (+)/Receive (-)"] > 0)][["Player", "To Pay (+)/Receive (-)"]]
    if not pay_to_booker.empty:
        st.markdown("### Who Pays the Booker (with UPI):")
        for _, row in pay_to_booker.iterrows():
            upi_amount = row['To Pay (+)/Receive (-)']
            payee = booker_name.replace(" ", "%20")
            upi_url = f"upi://pay?pa={booker_upi_id}&pn={payee}&am={upi_amount:.2f}&cu=INR"
            st.markdown(f"#### {row['Player']} pays ₹{upi_amount:.2f} to {booker_name}")

            # UPI Pay link
            st.markdown(f"[Pay via UPI](<{upi_url}>)", unsafe_allow_html=True)

            # QR Code generation
            qr = qrcode.QRCode(box_size=6, border=2)
            qr.add_data(upi_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buf = BytesIO()
            img.save(buf, format="PNG")
            st.image(buf.getvalue(), width=150, caption="Scan to pay (any UPI app)")

    st.markdown(f"*Total shares add up to: ₹{total_shares:.2f}*")

st.caption("Created by Aashish Sharma | Powered by Streamlit + UPI")

