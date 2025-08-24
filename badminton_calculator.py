import streamlit as st
import pandas as pd

st.set_page_config(page_title="Badminton Price Sharing Calculator", layout="centered")

st.title("🏸 Badminton Price Sharing Calculator")
st.markdown(
    "Split **court costs** by time played and **drinks** equally among players who played. "
    "One person (who played) pays for drinks; that amount is added to their contribution for settlement."
)

# --- Court Booking Details ---
st.header("Court Booking Details")
num_courts = st.number_input("Number of courts", min_value=1, value=1)
session_duration_hr = st.number_input("Duration per court (in hours)", min_value=0.25, value=1.0, step=0.25)
hourly_rate = st.number_input("Hourly rate per court (₹)", min_value=1.0, value=600.0, step=10.0)

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

booker_idx = st.radio(
    "Who booked & paid the court in advance?",
    options=list(range(int(num_players))),
    format_func=lambda idx: player_names[idx],
)
booker_name = player_names[booker_idx]

# --- Determine present players (must have played > 0 minutes) ---
present_players = [p for p in player_rows if p["minutes_played"] > 0]
present_names = [p["name"] for p in present_players]
total_played_minutes = sum(p["minutes_played"] for p in present_players)
n_present = len(present_players)

if total_played_minutes == 0 or n_present == 0:
    st.warning("No one played! Please enter valid minutes (> 0) for at least one player.")
else:
    # --- Drinks (single payer must be among present players) ---
    st.header("Drinks / Snacks")
    drinks_total = st.number_input("Total drinks/snacks cost (₹)", min_value=0.0, value=0.0, step=10.0)
    drinks_payer_name = None
    if drinks_total > 0:
        if not present_names:
            st.error("Drinks payer must be someone who played. Please enter minutes first.")
        else:
            drinks_payer_name = st.selectbox(
                "Who paid for drinks? (must be among players who played)",
                options=present_names,
                index=0,
            )

    # Drinks are split equally among present players
    drinks_share_each = round(drinks_total / n_present, 2) if drinks_total > 0 else 0.0

    # --- Build per-player ledger ---
    rows = []
    for p in player_rows:
        name = p["name"]
        mins = p["minutes_played"]
        played = mins > 0

        # Court share proportional by minutes among present players
        court_share = round(total_court_cost * (mins / total_played_minutes), 2) if played else 0.0

        # Drinks share equal among present players only
        drink_share = drinks_share_each if (played and drinks_total > 0) else 0.0

        total_owed = round(court_share + drink_share, 2)

        # Contributions:
        # - Booker contributes total court cost
        # - Drinks payer (who must be present) contributes drinks_total
        contributed = 0.0
        if name == booker_name:
            contributed += total_court_cost
        if drinks_total > 0 and drinks_payer_name and name == drinks_payer_name:
            contributed += drinks_total
        contributed = round(contributed, 2)

        # Net balance = Contribution - Owed
        # Positive => should receive; Negative => should pay
        net = round(contributed - total_owed, 2)

        rows.append(
            {
                "Player": name,
                "Minutes Played": mins,
                "Court Share (₹)": court_share,
                "Drinks Share (₹)": drink_share,
                "Total Owed (₹)": total_owed,
                "Total Contributed (₹)": contributed,
                "Net Balance (₹) (+receive / -pay)": net,
            }
        )

    df = pd.DataFrame(rows)

    # --- Display results ---
    st.subheader("Settlement Summary")
    st.dataframe(df, hide_index=True, use_container_width=True)

    grand_total = round(total_court_cost + drinks_total, 2)
    st.markdown(f"**Booker:** {booker_name}")
    if drinks_total > 0 and drinks_payer_name:
        st.markdown(f"**Drinks paid by:** {drinks_payer_name}  |  **Total drinks:** ₹{drinks_total:.2f}")
    else:
        st.markdown("**Drinks:** ₹0.00")
    st.markdown(f"**Grand total (court + drinks): ₹{grand_total:.2f}**")

    # Sums sanity
    sum_owed = round(df["Total Owed (₹)"].sum(), 2)
    sum_contrib = round(df["Total Contributed (₹)"].sum(), 2)
    sum_net = round(df["Net Balance (₹) (+receive / -pay)"].sum(), 2)
    st.markdown(
        f"- Sum of owed: **₹{sum_owed:.2f}**  |  "
        f"Sum of contributions: **₹{sum_contrib:.2f}**  |  "
        f"Net balance total: **₹{sum_net:.2f}**"
    )

    # --- Suggested Settlements (who pays whom) ---
    st.subheader("Suggested Settlements")
    creditors = []  # (name, amount_to_receive)
    debtors = []    # (name, amount_to_pay)

    for _, r in df.iterrows():
        net = r["Net Balance (₹) (+receive / -pay)"]
        if net > 0.005:
            creditors.append([r["Player"], float(net)])
        elif net < -0.005:
            debtors.append([r["Player"], float(-net)])  # store positive amount to pay

    # Greedy settlement
    transfers = []
    ci, di = 0, 0
    while ci < len(creditors) and di < len(debtors):
        c_name, c_amt = creditors[ci]
        d_name, d_amt = debtors[di]
        pay = round(min(c_amt, d_amt), 2)
        if pay > 0:
            transfers.append((d_name, c_name, pay))
            creditors[ci][1] = round(c_amt - pay, 2)
            debtors[di][1] = round(d_amt - pay, 2)
        if creditors[ci][1] <= 0.005:
            ci += 1
        if debtors[di][1] <= 0.005:
            di += 1

    if not transfers:
        st.write("- No transfers required (everyone is settled).")
    else:
        for payer, receiver, amt in transfers:
            st.write(f"- **{payer}** pays **₹{amt:.2f}** to **{receiver}**")

    # CSV download
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download settlement as CSV",
        data=csv,
        file_name="badminton_settlement.csv",
        mime="text/csv",
    )

st.caption("Created by Aashish Sharma | Court split by minutes, drinks split equally, drinks payer must have played")
