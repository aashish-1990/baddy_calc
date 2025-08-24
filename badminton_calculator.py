import streamlit as st
import pandas as pd

st.set_page_config(page_title="Badminton Price Sharing Calculator", layout="centered")

st.title("🏸 Badminton Price Sharing Calculator")
st.markdown("Split court booking fairly + include drinks paid by one player.")

# --- Court Booking ---
st.header("Court Booking Details")
num_courts = st.number_input("Number of courts", min_value=1, value=1)
session_duration_hr = st.number_input("Duration per court (in hours)", min_value=0.25, value=1.0, step=0.25)
hourly_rate = st.number_input("Hourly rate per court (₹)", min_value=1, value=600)

total_court_cost = round(num_courts * session_duration_hr * hourly_rate, 2)
st.write(f"**Total court cost:** ₹{total_court_cost:.2f}")

# --- Players & Minutes ---
st.header("Players & Minutes Played")
num_players = st.number_input("Number of players", min_value=2, value=4, step=1)

player_rows = []
player_names = []

for i in range(int(num_players)):
    c1, c2 = st.columns([2, 1])
    with c1:
        name = st.text_input(f"Player {i+1} name", value=f"Player{i+1}", key=f"name_{i}").strip() or f"Player{i+1}"
    with c2:
        mins = st.number_input(
            "Minutes played",
            min_value=0,
            max_value=int(session_duration_hr * 60),
            value=int(session_duration_hr * 60),
            step=5,
            key=f"mins_{i}",
        )
    player_rows.append({"name": name, "minutes_played": mins})
    player_names.append(name)

# Who booked
booker_idx = st.radio(
    "Who booked & paid the court in advance?",
    options=list(range(int(num_players))),
    format_func=lambda idx: player_names[idx],
)
booker_name = player_names[booker_idx]

# --- Drinks Section ---
st.header("Drinks / Snacks")
drinks_total = st.number_input("Total drinks/snacks cost (₹)", min_value=0.0, value=0.0, step=10.0)
drinks_payer_name = None
if drinks_total > 0:
    drinks_payer_idx = st.selectbox("Who paid for drinks?", options=list(range(int(num_players))), format_func=lambda idx: player_names[idx])
    drinks_payer_name = player_names[drinks_payer_idx]

# --- Settlement ---
present_players = [p for p in player_rows if p["minutes_played"] > 0]
total_played_minutes = sum(p["minutes_played"] for p in present_players)
n_present = len(present_players)

if total_played_minutes == 0:
    st.warning("No one played! Please enter minutes > 0.")
else:
    drinks_share_each = round(drinks_total / n_present, 2) if drinks_total > 0 else 0.0
    rows = []

    for p in player_rows:
        name = p["name"]
        mins = p["minutes_played"]
        played = mins > 0

        # Court share proportional to minutes
        court_share = round(total_court_cost * (mins / total_played_minutes), 2) if played else 0.0
        drink_share = drinks_share_each if (played and drinks_total > 0) else 0.0
        owed = round(court_share + drink_share, 2)

        # Contributions
        contributed = 0.0
        if name == booker_name:
            contributed += total_court_cost
        if drinks_total > 0 and drinks_payer_name and name == drinks_payer_name:
            contributed += drinks_total
        net = round(contributed - owed, 2)

        rows.append({
            "Player": name,
            "Minutes Played": mins,
            "Court Share (₹)": court_share,
            "Drinks Share (₹)": drink_share,
            "Total Owed (₹)": owed,
            "Total Contributed (₹)": contributed,
            "Net Balance (₹) (+receive / -pay)": net,
        })

    df = pd.DataFrame(rows)

    st.subheader("Settlement Summary")
    st.dataframe(df, hide_index=True, use_container_width=True)

    # Totals
    grand_total = round(total_court_cost + drinks_total, 2)
    st.markdown(f"**Booker:** {booker_name}")
    if drinks_total > 0 and drinks_payer_name:
        st.markdown(f"**Drinks paid by:** {drinks_payer_name} | ₹{drinks_total:.2f}")
    st.markdown(f"**Grand total (court + drinks): ₹{grand_total:.2f}**")

    # Suggested Settlements
    st.subheader("Suggested Settlements")
    creditors, debtors = [], []
    for _, r in df.iterrows():
        if r["Net Balance (₹) (+receive / -pay)"] > 0.005:
            creditors.append([r["Player"], float(r["Net Balance (₹) (+receive / -pay)"])])
        elif r["Net Balance (₹) (+receive / -pay)"] < -0.005:
            debtors.append([r["Player"], float(-r["Net Balance (₹) (+receive / -pay)"])])

    transfers = []
    ci, di = 0, 0
    while ci < len(creditors) and di < len(debtors):
        c_name, c_amt = creditors[ci]
        d_name, d_amt = debtors[di]
        pay = round(min(c_amt, d_amt), 2)
        if pay > 0:
            transfers.append((d_name, c_name, pay))
            creditors[ci][1] -= pay
            debtors[di][1] -= pay
        if creditors[ci][1] <= 0.005: ci += 1
        if debtors[di][1] <= 0.005: di += 1

    if not transfers:
        st.write("- No transfers required (all settled).")
    else:
        for payer, receiver, amt in transfers:
            st.write(f"- **{payer}** pays **₹{amt:.2f}** to **{receiver}**")

    # Download CSV
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download settlement as CSV", data=csv, file_name="badminton_settlement.csv", mime="text/csv")

st.caption("Created by Aashish Sharma | Simple settlement of court + drinks")
