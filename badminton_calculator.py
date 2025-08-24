import streamlit as st
import pandas as pd

st.set_page_config(page_title="Badminton Price Sharing Calculator", layout="centered")

st.title("🏸 Badminton Price Sharing Calculator")
st.markdown("**Split court booking costs fairly based on time played — with optional drinks cost.**")

# --- Booking Inputs ---
st.header("Court Booking Details")
num_courts = st.number_input("Number of courts", min_value=1, value=1)
session_duration_hr = st.number_input("Duration per court (in hours)", min_value=0.25, value=1.0, step=0.25)
hourly_rate = st.number_input("Hourly rate per court (₹)", min_value=1, value=600)

total_court_cost = num_courts * session_duration_hr * hourly_rate
st.write(f"**Total court cost:** ₹{total_court_cost:.2f}")

# --- Drinks / Extras ---
st.header("Extras (Optional)")
drinks_total = st.number_input("Total drinks/snacks cost (₹)", min_value=0.0, value=0.0, step=10.0)
drinks_split_mode = st.selectbox(
    "How to split drinks?",
    ["Equally among present players", "Proportionally by minutes played"]
)

# --- Player Inputs ---
st.header("Players & Playtime")
num_players = st.number_input("Number of players", min_value=2, value=4)
player_data = []
player_names = []

for i in range(int(num_players)):
    col1, col2 = st.columns([2, 1])
    with col1:
        name = st.text_input(f"Player {i+1} name", value=f"Player{i+1}", key=f"name_{i}").strip()
    with col2:
        mins = st.number_input(
            f"Minutes played",
            min_value=0,
            max_value=int(session_duration_hr * 60),
            value=int(session_duration_hr * 60),
            key=f"mins_{i}",
        )
    player_data.append({"name": name, "minutes_played": mins})
    player_names.append(name)

booker_idx = st.radio(
    "Who booked & paid in advance?",
    options=list(range(num_players)),
    format_func=lambda x: player_names[x] if player_names[x] else f"Player{x+1}",
)
booker_name = player_data[booker_idx]["name"] or f"Player{booker_idx+1}"

# --- Calculation ---
present_players = [p for p in player_data if p["minutes_played"] > 0]
total_played_minutes = sum(p["minutes_played"] for p in present_players)

if total_played_minutes == 0:
    st.warning("No one played! Please enter valid minutes (> 0) for at least one player.")
else:
    # Base court shares: proportional by minutes
    def court_share(p):
        return total_court_cost * (p["minutes_played"] / total_played_minutes) if total_played_minutes > 0 else 0.0

    # Drinks shares: either equal or proportional
    if drinks_total > 0 and len(present_players) > 0:
        if drinks_split_mode == "Equally among present players":
            equal_drinks = drinks_total / len(present_players)
            def drinks_share(p): return equal_drinks
        else:  # Proportional by minutes
            def drinks_share(p):
                return drinks_total * (p["minutes_played"] / total_played_minutes) if total_played_minutes > 0 else 0.0
    else:
        def drinks_share(p): return 0.0

    rows = []
    non_booker_settlements = []
    for p in present_players:
        cs = court_share(p)
        ds = drinks_share(p)
        total_share_unrounded = cs + ds
        # Round per-player shares for display/payment
        cs_r = round(cs, 2)
        ds_r = round(ds, 2)
        total_share = round(total_share_unrounded, 2)

        row = {
            "Player": p["name"],
            "Minutes Played": p["minutes_played"],
            "Court Share (₹)": cs_r,
            "Drinks Share (₹)": ds_r,
            "Total Share (₹)": total_share,
        }
        rows.append(row)

    df = pd.DataFrame(rows)

    # Compute settlements to the booker:
    # For non-bookers: they owe their Total Share
    # For the booker: he should receive the sum of others (booker's settlement = negative of that)
    # This ensures rounding reconciliation automatically.
    total_cost_all = round(total_court_cost + drinks_total, 2)

    # Build settlements
    settlements = []
    sum_non_bookers = 0.0
    for _, r in df.iterrows():
        if r["Player"] == booker_name:
            continue
        sum_non_bookers += r["Total Share (₹)"]
    sum_non_bookers = round(sum_non_bookers, 2)

    # Booker receives negative of others' sum
    # If the booker is not in present players (edge case), we'll skip the negative line
    for i, r in df.iterrows():
        if r["Player"] == booker_name:
            settlements.append(-sum_non_bookers)
        else:
            settlements.append(r["Total Share (₹)"])

    df["To Pay (+)/Receive (-) vs Booker (₹)"] = settlements

    st.subheader("Settlement Results")
    st.dataframe(df, hide_index=True, use_container_width=True)

    # Summary
    st.markdown(f"**Booker:** {booker_name}")
    st.markdown(f"**Total court cost:** ₹{total_court_cost:.2f}")
    st.markdown(f"**Total drinks cost:** ₹{drinks_total:.2f}")
    st.markdown(f"**Grand total (court + drinks): ₹{total_cost_all:.2f}**")

    # Who pays the booker
    st.markdown("### Who Pays the Booker")
    payers = df[(df["Player"] != booker_name) & (df["To Pay (+)/Receive (-) vs Booker (₹)"] > 0)][
        ["Player", "To Pay (+)/Receive (-) vs Booker (₹)"]
    ]
    if payers.empty:
        st.write("- No one owes the booker (check inputs).")
    else:
        for _, row in payers.iterrows():
            st.write(f"- **{row['Player']}** pays **₹{row['To Pay (+)/Receive (-) vs Booker (₹)']:.2f}** to **{booker_name}**")

    # Download CSV
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download settlement as CSV", data=csv, file_name="badminton_settlement.csv", mime="text/csv")

st.caption("Created by Aashish Sharma | Streamlined for quick, fair settlements")
