import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("NSC KPI Dashboard")

# suburb name -> (lat, lon) so we can plot stores on a map
suburb_coords = {
    # NSW
    "Parramatta": (-33.8148, 151.0011), "Chatswood": (-33.7969, 151.1830),
    "Penrith": (-33.7511, 150.6942), "Liverpool": (-33.9200, 150.9236),
    "Bankstown": (-33.9171, 151.0347), "Hornsby": (-33.7040, 151.0987),
    "Blacktown": (-33.7688, 150.9063), "Campbelltown": (-34.0650, 150.8143),
    "Sutherland": (-34.0311, 151.0577), "Castle Hill": (-33.7315, 150.9816),
    "Ryde": (-33.8151, 151.1050), "Burwood": (-33.8774, 151.1037),
    "Miranda": (-34.0333, 151.1022), "Hurstville": (-33.9669, 151.1027),
    "Rockdale": (-33.9522, 151.1391), "North Sydney": (-33.8388, 151.2072),
    "Manly": (-33.7969, 151.2864), "Bondi Junction": (-33.8915, 151.2489),
    "Auburn": (-33.8483, 151.0327), "Mount Druitt": (-33.7667, 150.8206),
    "Newcastle": (-32.9283, 151.7817), "Wollongong": (-34.4278, 150.8931),
    "Maitland": (-32.7333, 151.5500), "Coffs Harbour": (-30.2963, 153.1135),
    "Tamworth": (-31.0927, 150.9289), "Orange": (-33.2839, 149.0988),
    "Dubbo": (-32.2431, 148.6047), "Wagga Wagga": (-35.1082, 147.3598),
    "Albury": (-36.0737, 146.9135), "Bathurst": (-33.4193, 149.5775),
    "Port Macquarie": (-31.4333, 152.9094), "Nowra": (-34.8797, 150.6017),
    "Lismore": (-28.8142, 153.2778), "Goulburn": (-34.7544, 149.7178),
    # VIC
    "Box Hill": (-37.8192, 145.1225), "Dandenong": (-37.9881, 145.2148),
    "Frankston": (-38.1418, 145.1234), "Ringwood": (-37.8140, 145.2296),
    "Craigieburn": (-37.5997, 144.9434), "Sunshine": (-37.7880, 144.8320),
    "Werribee": (-37.9007, 144.6631), "Broadmeadows": (-37.6833, 144.9167),
    "Glen Waverley": (-37.8783, 145.1628), "Doncaster": (-37.7833, 145.1250),
    "Cranbourne": (-38.0996, 145.2834), "Melton": (-37.6833, 144.5833),
    "Pakenham": (-38.0733, 145.4850), "Berwick": (-38.0333, 145.3500),
    "Bundoora": (-37.7000, 145.0583), "Preston": (-37.7411, 144.9986),
    "Footscray": (-37.8000, 144.9000), "Camberwell": (-37.8250, 145.0583),
    "Geelong": (-38.1499, 144.3617), "Ballarat": (-37.5622, 143.8503),
    "Bendigo": (-36.7570, 144.2794), "Shepparton": (-36.3833, 145.4000),
    "Warrnambool": (-38.3833, 142.4833), "Mildura": (-34.1855, 142.1625),
    "Wodonga": (-36.1219, 146.8878), "Traralgon": (-38.1966, 146.5378),
    # QLD
    "Brisbane City": (-27.4698, 153.0251), "Chermside": (-27.3855, 153.0349),
    "Ipswich": (-27.6171, 152.7606), "Springfield": (-27.6667, 152.9167),
    "Robina": (-28.0761, 153.3801), "Southport": (-27.9666, 153.4127),
    "Caboolture": (-27.0833, 152.9500), "Redcliffe": (-27.2333, 153.1000),
    "Carindale": (-27.5000, 153.1000), "Mount Gravatt": (-27.5333, 153.0833),
    "Indooroopilly": (-27.5000, 152.9667), "Capalaba": (-27.5333, 153.2000),
    "Browns Plains": (-27.6833, 153.0167), "Strathpine": (-27.3000, 152.9833),
    "Toowoomba": (-27.5598, 151.9507), "Cairns": (-16.9203, 145.7710),
    "Townsville": (-19.2590, 146.8169), "Mackay": (-21.1550, 149.1868),
    "Rockhampton": (-23.3791, 150.5100), "Bundaberg": (-24.8661, 152.3489),
    "Gladstone": (-23.8419, 151.2570), "Hervey Bay": (-25.2986, 152.8535),
    # WA
    "Perth": (-31.9505, 115.8605), "Joondalup": (-31.7448, 115.7661),
    "Cannington": (-32.0167, 115.9333), "Midland": (-31.8886, 116.0108),
    "Fremantle": (-32.0569, 115.7439), "Morley": (-31.8927, 115.9006),
    "Osborne Park": (-31.8927, 115.8236), "Malaga": (-31.8631, 115.9089),
    "Rockingham": (-32.2769, 115.7297), "Mandurah": (-32.5269, 115.7217),
    "Armadale": (-32.1500, 116.0167), "Kwinana": (-32.2500, 115.7833),
    "Bunbury": (-33.3271, 115.6414), "Geraldton": (-28.7742, 114.6142),
    "Kalgoorlie": (-30.7489, 121.4658), "Albany": (-35.0269, 117.8837),
    "Karratha": (-20.7364, 116.8460),
    "Baldivis": (-32.3360, 115.8220),
    # SA
    "Adelaide": (-34.9285, 138.6007), "Elizabeth": (-34.7181, 138.6689),
    "Marion": (-35.0167, 138.5589), "Mile End": (-34.9280, 138.5729),
    "Modbury": (-34.8333, 138.6833), "Noarlunga": (-35.1500, 138.5000),
    "Prospect": (-34.8833, 138.5944), "Salisbury": (-34.7667, 138.6417),
    "Gepps Cross": (-34.8500, 138.5833), "Woodville": (-34.8833, 138.5500),
    "Mount Gambier": (-37.8283, 140.7828), "Whyalla": (-33.0333, 137.5667),
    "Port Augusta": (-32.4833, 137.7667), "Port Lincoln": (-34.7267, 135.8600),
    # TAS
    "Hobart": (-42.8821, 147.3272), "Glenorchy": (-42.8306, 147.2728),
    "Launceston": (-41.4332, 147.1441), "Devonport": (-41.1795, 146.3502),
    "Burnie": (-41.0558, 145.9081),
    # ACT
    "Canberra": (-35.2809, 149.1300), "Belconnen": (-35.2384, 149.0668),
    "Tuggeranong": (-35.4167, 149.0833), "Fyshwick": (-35.3333, 149.1667),
    "Woden": (-35.3444, 149.0866),
    # NT
    "Darwin": (-12.4634, 130.8456), "Palmerston": (-12.4881, 130.9822),
    "Alice Springs": (-23.6980, 133.8807), "Katherine": (-14.4652, 132.2635),
}

# ---------- load the 3 files we need ----------
nsc_df = pd.read_excel("data/nationwide_supply_asset_list.xlsx")
nsc_df["Asset Type"] = nsc_df["Asset Make/Model"].str.split(" - ").str[0]
nsc_df["lat"] = nsc_df["Suburb"].map(lambda s: suburb_coords[s][0])
nsc_df["lon"] = nsc_df["Suburb"].map(lambda s: suburb_coords[s][1])

coretex_df = pd.read_excel("data/coretex_equipment_records.xlsx")

aroflo_df = pd.read_excel("data/aroflo_invoicing_report.xlsx")
aroflo_df["Invoice Date"] = pd.to_datetime(aroflo_df["Invoice Date"])

# ---------- reporting period picker (sidebar) ----------
st.sidebar.markdown("### Reporting period")
AS_OF_DATE = pd.Timestamp(st.sidebar.date_input("Reporting period end date", value=pd.Timestamp("2025-12-31")))
recency_cutoff = AS_OF_DATE - pd.Timedelta(days=60)

# ---------- asset accuracy: compare NSC vs Coretex ----------
nsc_serials = set(nsc_df["Serial Number"])
coretex_serials = set(coretex_df["Serial Number"])
missing_from_coretex = nsc_serials - coretex_serials
missing_from_nsc = coretex_serials - nsc_serials
asset_match_rate = (len(coretex_serials) - len(missing_from_nsc)) / len(coretex_serials) * 100

# split "missing from nsc" into New Asset (recent) vs Needs Review (old)
pending_coretex_df = coretex_df[coretex_df["Serial Number"].isin(missing_from_nsc)].copy()
pending_coretex_df["Asset Type"] = pending_coretex_df["Equipment Type"]
pending_coretex_df["Store Name"] = pending_coretex_df["Store Reference"]
pending_coretex_df["lat"] = pending_coretex_df["Suburb"].map(lambda s: suburb_coords[s][0])
pending_coretex_df["lon"] = pending_coretex_df["Suburb"].map(lambda s: suburb_coords[s][1])
pending_coretex_df["Installation Date"] = pd.to_datetime(pending_coretex_df["Installation Date"])
pending_coretex_df["Category"] = pending_coretex_df["Installation Date"].apply(
    lambda d: "New Asset" if d >= recency_cutoff else "Needs Review"
)
new_installs_df = pending_coretex_df[pending_coretex_df["Category"] == "New Asset"]
needs_review_gap_df = pending_coretex_df[pending_coretex_df["Category"] == "Needs Review"]

# find units Coretex marked Inactive recently (= removed)
coretex_status_map = dict(zip(coretex_df["Serial Number"], coretex_df["Status"]))
coretex_change_date_map = dict(zip(coretex_df["Serial Number"], pd.to_datetime(coretex_df["Status Change Date"])))
nsc_df["Coretex Status"] = nsc_df["Serial Number"].map(coretex_status_map)
nsc_df["Status Change Date"] = nsc_df["Serial Number"].map(coretex_change_date_map)
removed_assets_df = nsc_df[
    (nsc_df["Coretex Status"] == "Inactive") &
    (nsc_df["Status Change Date"] >= recency_cutoff)
].copy()

# match new installs to removed assets at the same store = replacement
removed_by_store = removed_assets_df.groupby("Store #")["Serial Number"].apply(list).to_dict()
new_by_store = new_installs_df.groupby("Store Reference")["Serial Number"].apply(list).to_dict()

def find_match(store, other_map, used):
    for s in other_map.get(store, []):
        if s not in used:
            used.add(s)
            return s
    return None

used_removed = set()
new_installs_df = new_installs_df.copy()
new_installs_df["Match Type"] = "New Store"
new_installs_df["Matched Removed Serial"] = "-"
for idx, row in new_installs_df.iterrows():
    match = find_match(row["Store Reference"], removed_by_store, used_removed)
    if match:
        new_installs_df.at[idx, "Match Type"] = "Replacement"
        new_installs_df.at[idx, "Matched Removed Serial"] = match

used_new = set()
removed_assets_df = removed_assets_df.copy()
removed_assets_df["Matched New Serial"] = "-"
removed_assets_df["Match Type"] = "Unmatched removal"
for idx, row in removed_assets_df.iterrows():
    match = find_match(row["Store #"], new_by_store, used_new)
    if match:
        removed_assets_df.at[idx, "Matched New Serial"] = match
        removed_assets_df.at[idx, "Match Type"] = "Replacement"

new_installs_df = new_installs_df.sort_values("Store Reference")
removed_assets_df = removed_assets_df.sort_values("Store #")

# serials on NSC but missing from Coretex entirely (shouldn't happen)
missing_entirely_df = nsc_df[nsc_df["Serial Number"].isin(missing_from_coretex)].copy()

# combine both "needs review" cases into one table
needs_review_combined = pd.concat([
    needs_review_gap_df.rename(columns={"Equipment Type": "Type", "Store Reference": "Store"})[["Serial Number", "Type", "Store", "State", "Installation Date"]].assign(Reason="On Coretex, not yet on NSC register (2+ months)"),
    missing_entirely_df.rename(columns={"Asset Make/Model": "Type", "Store Name": "Store"})[["Serial Number", "Type", "Store", "State"]].assign(Reason="Missing from Coretex entirely - unexpected")
], ignore_index=True)

# build map data - everything + pending installs, tagged by category
nsc_df["Category"] = nsc_df["Asset Type"]
removed_serials_set = set(removed_assets_df["Serial Number"])
nsc_df.loc[nsc_df["Serial Number"].isin(removed_serials_set), "Category"] = "Removed Asset"

map_df = pd.concat([
    nsc_df[["Store Name", "State", "Asset Type", "Category", "lat", "lon"]],
    pending_coretex_df[["Store Name", "State", "Asset Type", "Category", "lat", "lon"]]
], ignore_index=True)

# ---------- planned servicing: on-time rate this month ----------
target_month = AS_OF_DATE.strftime("%b")
scheduled_serials = set(nsc_df[nsc_df[target_month].notna()]["Serial Number"])

this_month_prevent = aroflo_df[
    (aroflo_df["Job Type"] == "Preventative Service") &
    (aroflo_df["Invoice Date"].dt.strftime("%b") == target_month) &
    (aroflo_df["Invoice Date"].dt.year == AS_OF_DATE.year)
]
invoiced_serials = set(this_month_prevent["Asset Serial Number"])

on_time_serials = scheduled_serials & invoiced_serials
outstanding_serials = scheduled_serials - invoiced_serials
servicing_on_time_rate = (len(on_time_serials) / len(scheduled_serials) * 100) if scheduled_serials else 0

# 24-month rolling trend, ending at the reporting date
nsc_df["Installation Date"] = pd.to_datetime(nsc_df["Installation Date"])

trend_rows = []
end_period = AS_OF_DATE.to_period("M")
start_period = end_period - 23
period_range = pd.period_range(start_period, end_period, freq="M")
for period in period_range:
    month_name = period.strftime("%b")
    period_ts = period.to_timestamp(how="end")

    eligible = nsc_df[
        (nsc_df[month_name].notna()) &
        (nsc_df["Installation Date"] <= period_ts)
    ]
    scheduled_this_period = set(eligible["Serial Number"])

    invoiced_this_period = set(aroflo_df[
        (aroflo_df["Job Type"] == "Preventative Service") &
        (aroflo_df["Invoice Date"].dt.strftime("%Y-%m") == str(period))
    ]["Asset Serial Number"])

    rate = (len(scheduled_this_period & invoiced_this_period) / len(scheduled_this_period) * 100) if scheduled_this_period else None
    trend_rows.append({"YearMonth": str(period), "On Time %": rate})

monthly_trend = pd.DataFrame(trend_rows)
servicing_2yr_avg_rate = monthly_trend["On Time %"].mean()

# ---------- reactive capex: predict next year's breakdown spend per asset ----------
from sklearn.linear_model import LinearRegression

NEAR_REGIONAL_SUBURBS = {
    "Newcastle", "Wollongong", "Maitland", "Nowra", "Goulburn",
    "Geelong", "Ballarat", "Bendigo", "Shepparton", "Traralgon",
    "Toowoomba", "Bunbury", "Launceston",
}
FAR_REGIONAL_SUBURBS = {
    "Coffs Harbour", "Tamworth", "Orange", "Dubbo", "Wagga Wagga", "Albury", "Bathurst",
    "Port Macquarie", "Lismore", "Warrnambool", "Mildura", "Wodonga",
    "Cairns", "Townsville", "Mackay", "Rockhampton", "Bundaberg", "Gladstone", "Hervey Bay",
    "Geraldton", "Kalgoorlie", "Albany", "Karratha",
    "Mount Gambier", "Whyalla", "Port Augusta", "Port Lincoln",
    "Devonport", "Burnie", "Alice Springs", "Katherine",
}

def classify_tier(suburb):
    if suburb in NEAR_REGIONAL_SUBURBS:
        return "Near-Regional"
    elif suburb in FAR_REGIONAL_SUBURBS:
        return "Far-Regional"
    else:
        return "Metro"

# train on all historical asset-years
lifetime_df = pd.read_excel("data/lifetime_maintenance_spend.xlsx", sheet_name="Lifetime Spend by Year")
lifetime_df["Asset Type"] = lifetime_df["Asset"].str.split(" - ").str[0]
serial_to_suburb = dict(zip(nsc_df["Serial Number"], nsc_df["Suburb"]))
lifetime_df["Suburb"] = lifetime_df["Serial"].map(serial_to_suburb)
lifetime_df["Location Tier"] = lifetime_df["Suburb"].apply(classify_tier)

lifetime_df = lifetime_df.sort_values(["Serial", "Year"])
lifetime_df["Prior Year Breakdown Spend"] = lifetime_df.groupby("Serial")["Breakdown Spend"].shift(1)
lifetime_df_with_history = lifetime_df.dropna(subset=["Prior Year Breakdown Spend"])

reactive_X = pd.get_dummies(
    lifetime_df_with_history[["Age at Year", "Asset Type", "Location Tier", "Prior Year Breakdown Spend"]],
    columns=["Asset Type", "Location Tier"], drop_first=True
)
reactive_y = lifetime_df_with_history["Breakdown Spend"]
reactive_model = LinearRegression()
reactive_model.fit(reactive_X, reactive_y)

# apply the trained model to every CURRENT asset, aged forward one year
latest_year_rows = lifetime_df.sort_values("Year").groupby("Serial").tail(1).set_index("Serial")

predict_df = nsc_df.copy()
predict_df["Asset Type"] = predict_df["Asset Make/Model"].str.split(" - ").str[0]
predict_df["Location Tier"] = predict_df["Suburb"].apply(classify_tier)
predict_df["Age at Year"] = ((AS_OF_DATE - predict_df["Installation Date"]).dt.days / 365.25) + 1
predict_df["Prior Year Breakdown Spend"] = predict_df["Serial Number"].map(latest_year_rows["Breakdown Spend"]).fillna(0)

reactive_X_predict = pd.get_dummies(
    predict_df[["Age at Year", "Asset Type", "Location Tier", "Prior Year Breakdown Spend"]],
    columns=["Asset Type", "Location Tier"], drop_first=True
)
reactive_X_predict = reactive_X_predict.reindex(columns=reactive_X.columns, fill_value=0)

predict_df["Predicted Breakdown Spend"] = reactive_model.predict(reactive_X_predict).clip(min=0)
reactive_capex_forecast = predict_df["Predicted Breakdown Spend"].sum()

# ---------- proactive capex: predict which assets become high-risk next year ----------
from sklearn.linear_model import LogisticRegression

TYPICAL_LIFE = {"Baler": 10, "Compactor": 17.5}
lifetime_df["Life Ratio"] = lifetime_df.apply(lambda r: r["Age at Year"] / TYPICAL_LIFE[r["Asset Type"]], axis=1)
lifetime_df["High Risk"] = (
    (lifetime_df["Life Ratio"] >= 0.9) &
    (lifetime_df["Cumulative Breakdown Spend as % of Replacement Cost"] >= 50)
).astype(int)

lifetime_df = lifetime_df.sort_values(["Serial", "Year"])
lifetime_df["Next Year High Risk"] = lifetime_df.groupby("Serial")["High Risk"].shift(-1)
lifetime_df_labeled = lifetime_df.dropna(subset=["Next Year High Risk"])

proactive_X = pd.get_dummies(
    lifetime_df_labeled[["Age at Year", "Asset Type", "Location Tier", "Cumulative Breakdown Spend as % of Replacement Cost"]],
    columns=["Asset Type", "Location Tier"], drop_first=True
)
proactive_y = lifetime_df_labeled["Next Year High Risk"]
proactive_model = LogisticRegression(max_iter=1000)
proactive_model.fit(proactive_X, proactive_y)

# apply to the CURRENT fleet, using this year's real numbers to predict NEXT year's risk
predict_df["Current Age"] = predict_df["Age at Year"] - 1  # undo the "+1" from the reactive model block, back to this year's real age
latest_cum_pct = lifetime_df.sort_values("Year").groupby("Serial").tail(1).set_index("Serial")["Cumulative Breakdown Spend as % of Replacement Cost"]
predict_df["Cumulative Breakdown Spend as % of Replacement Cost"] = predict_df["Serial Number"].map(latest_cum_pct).fillna(0)

proactive_X_predict = pd.get_dummies(
    predict_df[["Current Age", "Asset Type", "Location Tier", "Cumulative Breakdown Spend as % of Replacement Cost"]].rename(columns={"Current Age": "Age at Year"}),
    columns=["Asset Type", "Location Tier"], drop_first=True
)
proactive_X_predict = proactive_X_predict.reindex(columns=proactive_X.columns, fill_value=0)

predict_df["High Risk Probability"] = proactive_model.predict_proba(proactive_X_predict)[:, 1]
predict_df["Predicted High Risk"] = predict_df["High Risk Probability"] >= 0.35

proactive_capex_forecast = predict_df[predict_df["Predicted High Risk"]]["Current Replacement Cost"].sum()
high_risk_assets_df = predict_df[predict_df["Predicted High Risk"]]

# ---------- sidebar navigation ----------
section = st.sidebar.radio("Go to", [
    "Upload Files", "Asset Accuracy", "Planned Servicing",
    "Breakdowns-Balers", "Breakdowns-Compactors",
    "Pricing Compliance", "Safety Compliance", "Predictive Capex", "Recommendations"
])

# ---------- upload files tab ----------
if section == "Upload Files":
    st.subheader("Upload this month's files")
    st.write("Drop in the latest export from each of the four source systems to refresh the dashboard.")

    row1_a, row1_b = st.columns(2)
    with row1_a:
        asset_file = st.file_uploader("NSC asset register", type=["xlsx"])
    with row1_b:
        coretex_file = st.file_uploader("Coretex equipment records", type=["xlsx"])

    row2_a, row2_b = st.columns(2)
    with row2_a:
        aroflo_file = st.file_uploader("Aroflo 2yr invoicing report", type=["xlsx"])
    with row2_b:
        lifetime_file = st.file_uploader("Aroflo lifetime maintenance spend", type=["xlsx"])

    row3_a, row3_b = st.columns(2)
    with row3_a:
        verified_file = st.file_uploader("Verified sign-in records", type=["xlsx"])

    uploaded = [asset_file, coretex_file, aroflo_file, verified_file, lifetime_file]
    st.progress(sum(f is not None for f in uploaded) / len(uploaded))

    if all(uploaded):
        st.success("All 5 files uploaded")
    else:
        st.info(f"{sum(f is not None for f in uploaded)} of 5 files uploaded")

    st.caption("Note: uploaded files aren't wired into the dashboard's calculations yet - every tab currently reads from the local data/ folder. Connecting these uploads to the actual logic is a separate piece of work still to come.")
    st.info("Before reviewing the dashboard, set the **Reporting period end date** in the sidebar to match the month these files cover - the on-time rates and trend charts are calculated relative to that date.")


# ---------- asset accuracy tab ----------
elif section == "Asset Accuracy":
    st.subheader("Asset register accuracy")
    st.metric("Asset register accuracy", f"{asset_match_rate:.1f}%")

    asset_changes = pd.DataFrame({
        "Status": ["Total assets", "New Assets", "Removed Assets", "Needs Review"],
        "Count": [len(coretex_serials), len(new_installs_df), len(removed_assets_df), len(needs_review_combined)]
    })

    col_table, col_map = st.columns([1, 3])

    with col_table:
        st.table(asset_changes)
        st.caption("New Assets matched to a Removed Asset are like-for-like replacements. Other New Assets are likely a new store or an additional unit added for demand. Needs Review flags anything that doesn't fit that pattern.")

    with col_map:
        fig = px.scatter_geo(
            map_df, lat="lat", lon="lon",
            hover_name="Store Name",
            hover_data={"State": True, "Asset Type": True, "lat": False, "lon": False},
            color="Category",
            color_discrete_map={
                "Baler": "#f2c744",
                "Compactor": "#1f77b4",
                "New Asset": "green",
                "Needs Review": "red",
                "Removed Asset": "purple"
            },
            scope="world",
        )
        fig.update_geos(
            lataxis_range=[-45, -9], lonaxis_range=[108, 156],
            showland=True, landcolor="rgb(235,235,230)", showcountries=True,
        )
        fig.update_layout(
            title=dict(text="All Unit Locations", x=0.5, xanchor="center"),
            margin={"r":40,"t":50,"l":0,"b":0}, height=450,
            legend=dict(x=0.01, y=0.99, xanchor="left", yanchor="top")
        )
        st.plotly_chart(fig, width="stretch")

    if len(new_installs_df) > 0:
        with st.expander(f"View {len(new_installs_df)} New Asset(s)"):
            new_display = new_installs_df[["Serial Number", "Match Type", "Matched Removed Serial", "Equipment Type", "Store Reference", "Suburb", "State", "Installation Date"]].rename(
                columns={"Equipment Type": "Asset Type", "Store Reference": "Store Code", "Matched Removed Serial": "Matched Serial", "Installation Date": "Date"}
            )
            st.dataframe(new_display)
    else:
        st.success("No new assets this month.")

    if len(removed_assets_df) > 0:
        with st.expander(f"View {len(removed_assets_df)} Removed Asset(s)"):
            removed_display = removed_assets_df[["Serial Number", "Match Type", "Matched New Serial", "Asset Type", "Store #", "Suburb", "State", "Status Change Date"]].rename(
                columns={"Store #": "Store Code", "Matched New Serial": "Matched Serial", "Status Change Date": "Date"}
            )
            st.dataframe(removed_display)
    else:
        st.info("No removed assets this month.")

    if len(needs_review_combined) > 0:
        with st.expander(f"⚠️ View {len(needs_review_combined)} unit(s) needing review"):
            st.dataframe(needs_review_combined)
    else:
        st.info("Nothing flagged for review this month.")


# ---------- planned servicing tab ----------
elif section == "Planned Servicing":

    st.subheader("Planned servicing")

    completed_stores = set(nsc_df[nsc_df["Serial Number"].isin(on_time_serials)]["Store #"])
    outstanding_stores = set(nsc_df[nsc_df["Serial Number"].isin(outstanding_serials)]["Store #"])
    outstanding_df = nsc_df[nsc_df["Serial Number"].isin(outstanding_serials)]

    # metrics row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Completions on time (this month)", f"{servicing_on_time_rate:.1f}%", delta=f"{servicing_on_time_rate - servicing_2yr_avg_rate:.1f}% vs 2yr avg")
    col2.metric("Completions on time (2yr avg)", f"{servicing_2yr_avg_rate:.1f}%")
    col3.metric("Completed", f"{len(completed_stores)} stores")
    col4.metric("Outstanding", f"{len(outstanding_stores)} stores")

    colA, colSpacer, colB = st.columns([4, 1, 5])

    # simple rule: >2 pts below avg = flag it, >2 pts above = good result, else normal
    rate_diff = servicing_on_time_rate - servicing_2yr_avg_rate
    if rate_diff < -2:
        trend_caption = "Below average result - recommend investigating further why the outstanding is higher than standard."
    elif rate_diff > 2:
        trend_caption = "Above average result."
    else:
        trend_caption = "In line with the 2-year average."

    # line chart: on-time trend over 2 years
    with colA:
        trend_fig = px.line(monthly_trend, x="YearMonth", y="On Time %", title="On-Time Rate - Last 2 Years")
        trend_fig.update_yaxes(range=[70, 100], dtick=10, ticksuffix="%")
        trend_fig.update_xaxes(tickangle=-45)
        trend_fig.update_layout(height=220, margin={"l":0,"r":0,"t":40,"b":40}, xaxis_title=None, yaxis_title=None)
        st.plotly_chart(trend_fig, use_container_width=True)
        st.caption(trend_caption)

    # bar chart: outstanding by state
    with colB:
        state_fig = px.bar(
        outstanding_df.groupby("State").size().reset_index(name="Outstanding"),
        x="State", y="Outstanding", title="Outstanding Services by State"
        )
        state_fig.update_yaxes(dtick=1)
        state_fig.update_layout(height=220, margin={"l":0,"r":0,"t":40,"b":0}, xaxis_title=None, yaxis_title=None)
        st.plotly_chart(state_fig, use_container_width=True)

    # map: completed vs outstanding
    servicing_map_df = nsc_df[nsc_df["Serial Number"].isin(scheduled_serials)].copy()
    servicing_map_df["Category"] = servicing_map_df["Serial Number"].apply(
        lambda s: "Completed" if s in on_time_serials else "Outstanding"
    )

    servicing_fig = px.scatter_geo(
        servicing_map_df, lat="lat", lon="lon",
        hover_name="Store Name",
        hover_data={"State": True, "Asset Type": True, "lat": False, "lon": False},
        color="Category",
        color_discrete_map={"Completed": "green", "Outstanding": "red"},
        scope="world",
    )
    servicing_fig.update_geos(
        lataxis_range=[-45, -9], lonaxis_range=[108, 156],
        showland=True, landcolor="rgb(235,235,230)", showcountries=True,
    )
    servicing_fig.update_layout(
        title=dict(text="This Month's Scheduled Servicing", x=0.5, xanchor="center"),
        margin={"r":40,"t":50,"l":0,"b":0}, height=450,
        legend=dict(x=0.01, y=0.99, xanchor="left", yanchor="top")
    )
    st.plotly_chart(servicing_fig, use_container_width=True)

    completed_display_df = servicing_map_df[servicing_map_df["Category"] == "Completed"]
    outstanding_display_df = servicing_map_df[servicing_map_df["Category"] == "Outstanding"]

    # drop downs of completed and outstanding
    if len(completed_display_df) > 0:
        with st.expander(f"View {len(completed_display_df)} Completed Service(s)"):
            st.dataframe(completed_display_df[["Serial Number", "Asset Type", "Store Name", "Suburb", "State"]])
    else:
        st.info("No completed services this month.")

    if len(outstanding_display_df) > 0:
        with st.expander(f"View {len(outstanding_display_df)} Outstanding Service(s)"):
            st.dataframe(outstanding_display_df[["Serial Number", "Asset Type", "Store Name", "Suburb", "State"]])
    else:
        st.success("No outstanding services this month.")


# ---------- breakdowns - balers tab (placeholder, real data still to come) ----------
elif section == "Breakdowns-Balers":
    st.subheader("Breakdowns - Balers")
    col1, col2 = st.columns(2)
    col1.metric("Breakdowns this month", "11", delta="+18% vs 2yr avg")
    col2.metric("Spend this month", "$14.2k", delta="+22% vs 2yr avg")

    st.write("Breakdowns by state")
    baler_breakdown_state = pd.DataFrame({
        "State": ["NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT"],
        "Breakdowns": [3, 2, 2, 1, 1, 1, 0, 1]
    })
    st.bar_chart(baler_breakdown_state.set_index("State"))

    st.write("Where breakdowns happened")
    baler_map = pd.DataFrame({"lat": [-33.87, -37.81, -27.47], "lon": [151.21, 144.96, 153.02]})
    st.map(baler_map)

    st.write("Spend trend")
    baler_spend_trend = pd.DataFrame({
        "Month": ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "Spend": [9800, 11200, 9500, 12800, 10300, 14200]
    })
    st.line_chart(baler_spend_trend.set_index("Month"))


# ---------- breakdowns - compactors tab (placeholder) ----------
elif section == "Breakdowns-Compactors":
    st.subheader("Breakdowns - Compactors")
    col1, col2 = st.columns(2)
    col1.metric("Breakdowns this month", "3", delta="-10% vs 2yr avg")
    col2.metric("Spend this month", "$8.1k", delta="+5% vs 2yr avg")

    st.write("Breakdowns by state")
    compactor_breakdown_state = pd.DataFrame({
        "State": ["NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT"],
        "Breakdowns": [1, 1, 0, 1, 0, 0, 0, 0]
    })
    st.bar_chart(compactor_breakdown_state.set_index("State"))

    st.write("Where breakdowns happened")
    compactor_map = pd.DataFrame({"lat": [-33.87, -31.95], "lon": [151.21, 115.86]})
    st.map(compactor_map)

    st.write("Spend trend")
    compactor_spend_trend = pd.DataFrame({
        "Month": ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "Spend": [7000, 7500, 6400, 7100, 7700, 8100]
    })
    st.line_chart(compactor_spend_trend.set_index("Month"))


# ---------- pricing compliance tab (placeholder) ----------
elif section == "Pricing Compliance":
    st.subheader("Pricing compliance")
    st.metric("Invoices flagged", "2")
    flagged = pd.DataFrame({
        "Invoice": ["AF-40009", "AF-40713"],
        "Charged": ["$358", "$340"],
        "Expected": ["$408", "$490"]
    })
    st.table(flagged)


# ---------- safety compliance tab (placeholder) ----------
elif section == "Safety Compliance":
    st.subheader("Safety compliance (Verified)")
    col1, col2 = st.columns(2)
    col1.metric("This month", "91%", delta="+13% vs 2yr avg")
    col2.metric("2yr average", "78%")

    st.write("Compliance trend")
    compliance_trend = pd.DataFrame({
        "Month": ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "Compliance %": [88, 90, 89, 93, 90, 91]
    })
    st.line_chart(compliance_trend.set_index("Month"))

    st.write("Incomplete inductions")
    st.metric("Records", "5")


# ---------- predictive capex tab ----------
elif section == "Predictive Capex":
    st.subheader("Predictive capex - next 12 months")
    col1, col2 = st.columns(2)

    with st.expander("How this forecast is calculated"):
        st.markdown("""
        **Reactive (unplanned)** - predicts next year's breakdown spend per asset, based on:
        - Age and asset type
        - Location (metro vs regional)
        - Recent breakdown history

        **Proactive (planned)** - flags assets for replacement when **both**:
        - Age is near/past typical design life
        - Breakdown spend is over 50% of a new unit's cost

        Also catches young "lemons" - flagged separately, since these usually need a
        warranty conversation, not a routine replacement.
        """)

    col1.metric("Proactive (planned)", f"${proactive_capex_forecast:,.0f}")
    st.write("")
    high_risk_display = predict_df[predict_df["Predicted High Risk"]].copy()
    high_risk_display["Cumulative Breakdown Spend ($)"] = (
        high_risk_display["Cumulative Breakdown Spend as % of Replacement Cost"] / 100
        * high_risk_display["Current Replacement Cost"]
    )
    high_risk_display = high_risk_display[[
        "Serial Number", "Asset Type", "Store Name", "State", "Age at Year",
        "Cumulative Breakdown Spend ($)", "Current Replacement Cost",
        "Cumulative Breakdown Spend as % of Replacement Cost"
    ]].rename(columns={
        "Age at Year": "Age (yrs)",
        "Current Replacement Cost": "Replacement Cost",
        "Cumulative Breakdown Spend as % of Replacement Cost": "% of Replacement Cost"
    }).sort_values("% of Replacement Cost", ascending=False)
    high_risk_display["Age (yrs)"] = high_risk_display["Age (yrs)"].round(1)

    with st.expander(f"View {len(high_risk_display)} recommended replacement(s)"):
        st.dataframe(high_risk_display)
        young_high_spend = high_risk_display[high_risk_display["Age (yrs)"] < 5]
        if len(young_high_spend) > 0:
            st.warning(f"⚠️ {len(young_high_spend)} unit(s) flagged despite being under 5 years old - likely chronic reliability issues rather than routine end-of-life, worth escalating separately (e.g. manufacturer warranty claim) rather than routine replacement.")
    col2.metric("Reactive (unplanned)", f"${reactive_capex_forecast:,.0f}")

    st.write("")
    proactive_by_state = high_risk_display.groupby("State")["Replacement Cost"].sum().reset_index()
    proactive_by_state["Type"] = "Proactive"
    proactive_by_state = proactive_by_state.rename(columns={"Replacement Cost": "Capex"})

    reactive_by_state = predict_df.groupby("State")["Predicted Breakdown Spend"].sum().reset_index()
    reactive_by_state["Type"] = "Reactive"
    reactive_by_state = reactive_by_state.rename(columns={"Predicted Breakdown Spend": "Capex"})

    capex_by_state = pd.concat([proactive_by_state, reactive_by_state], ignore_index=True)

    state_capex_fig = px.bar(
        capex_by_state, x="State", y="Capex", color="Type", barmode="group",
        title="Forecast Capex by State", color_discrete_map={"Proactive": "#1f77b4", "Reactive": "#f2a65a"}
    )
    state_capex_fig.update_layout(height=350, margin={"l":0,"r":0,"t":40,"b":0}, yaxis_title="$")
    st.plotly_chart(state_capex_fig, use_container_width=True)

    st.write("")
    high_risk_display_map = predict_df[predict_df["Predicted High Risk"]].copy()
    high_risk_display_map["Is Young Lemon"] = (high_risk_display_map["Age at Year"] < 5)
    high_risk_display_map["Category"] = high_risk_display_map["Is Young Lemon"].map({True: "Young Lemon", False: "Recommended Replacement"})

    capex_map_fig = px.scatter_geo(
        high_risk_display_map, lat="lat", lon="lon",
        hover_name="Store Name",
        hover_data={"State": True, "Asset Type": True, "lat": False, "lon": False},
        color="Category",
        color_discrete_map={"Recommended Replacement": "#1f77b4", "Young Lemon": "red"},
        scope="world",
    )
    capex_map_fig.update_geos(
        lataxis_range=[-45, -9], lonaxis_range=[108, 156],
        showland=True, landcolor="rgb(235,235,230)", showcountries=True,
    )
    capex_map_fig.update_layout(
        title=dict(text="Recommended Replacements - Locations", x=0.5, xanchor="center"),
        margin={"r":40,"t":50,"l":0,"b":0}, height=450,
        legend=dict(x=0.01, y=0.99, xanchor="left", yanchor="top")
    )
    st.plotly_chart(capex_map_fig, use_container_width=True)

# ---------- recommendations tab (placeholder) ----------
elif section == "Recommendations":
    st.subheader("Planned replacement recommendations")
    st.write("Ranked by age \u00d7 2-year breakdown spend")

    recommendations = pd.DataFrame({
        "Serial": ["SN100542", "SN100808", "SN100200", "SN100280", "SN100823"],
        "Type": ["Baler", "Baler", "Baler", "Baler", "Baler"],
        "Store": ["Rockhampton, QLD", "Tuggeranong, ACT", "Nowra, NSW", "Glen Waverley, VIC", "Darwin, NT"],
        "Age (yrs)": [12.6, 7.3, 11.2, 3.4, 7.0],
        "2yr Spend": ["$8,726", "$7,421", "$7,360", "$6,771", "$7,258"]
    })
    st.table(recommendations)

    st.info("5 balers are flagged for replacement - all but one are past their typical 8-12 year lifespan and still racking up significant breakdown costs.")

    st.divider()

    st.subheader("Asset register accuracy")
    st.write("New installs pending registration")

    pending = pd.DataFrame({
        "Serial": ["SN900004", "SN900007", "SN900008", "SN900009", "SN900011"],
        "Store": ["Chermside, QLD", "Newcastle, NSW", "Ryde, NSW", "Craigieburn, VIC", "Springfield, QLD"],
        "Installed": ["9 Nov", "9 Nov", "24 Nov", "9 Dec", "17 Nov"]
    })
    st.table(pending)

    st.warning("Coretex logs new installs immediately, but it's currently taking 1-2 months for those units to appear on NSC's own asset register - all 8 of this month's new installs are still pending. Worth reviewing the registration process (who's responsible for updating the register, and how quickly after install) to close that gap, since it's the main source of asset accuracy discrepancies each month.")
