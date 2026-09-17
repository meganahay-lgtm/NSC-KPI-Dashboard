# ============================================================
# TABLE OF CONTENTS
#   1. Setup
#   2. Suburb coordinates lookup
#   3. Load data files (shared by every tab)
#   4. Reporting period picker (shared)
#   5. Sidebar navigation
#   6. Tab - About Us
#   7. Tab - Upload Files
#   8. Tab - Safety Compliance
#   9. Tab - Pricing Compliance
#        - metric logic
#        - metrics row
#        - flagged invoices dropdown
#        - flagged by type bar chart
#  10. Tab - Asset Accuracy
#        - metric logic
#        - summary table + map
#        - New/Removed/Needs Review dropdowns
#  11. Tab - Planned Servicing
#        - metric logic
#        - metrics row
#        - on-time trend line chart
#        - outstanding by state bar chart
#        - completed/outstanding map
#        - completed/outstanding dropdowns
#  12. Tab - Breakdowns-Balers
#        - metric logic
#        - metrics row
#        - data-driven insight (repeat offenders / high-cost repairs)
#        - spend trend line chart + by-state bar chart
#        - map
#        - breakdown details dropdown
#  13. Tab - Breakdowns-Compactors
#        - metric logic
#        - metrics row
#        - data-driven insight (repeat offenders / high-cost repairs)
#        - spend trend line chart + by-state bar chart
#        - map
#        - breakdown details dropdown
#  14. Tab - Predictive Capex
#        - reactive model (regression)
#        - proactive model (classification)
#        - how this is calculated explainer
#        - proactive/reactive metrics + recommended replacements dropdown
#        - capex by state bar chart
#        - recommended replacements map
# ============================================================




# ============================================================
# 1. SETUP
# ============================================================
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

section = st.sidebar.radio("Navigation", [
    "About Us", "Upload Files", "Safety Compliance", "Pricing Compliance",
    "Asset Register Accuracy", "Planned Servicing", "Breakdowns-Balers", "Breakdowns-Compactors",
    "Predictive Capex"
])

SECTION_TITLES = {
    "About Us": ("ℹ️", "About This Dashboard"),
    "Upload Files": ("📁", "Upload Your Data"),
    "Safety Compliance": ("🦺", "Safety Compliance"),
    "Pricing Compliance": ("💲", "Pricing Compliance"),
    "Asset Register Accuracy": ("📋", "Asset Register Accuracy"),
    "Planned Servicing": ("🗓️", "Planned Servicing"),
    "Breakdowns-Balers": ("⚠️", "Breakdowns - Balers"),
    "Breakdowns-Compactors": ("⚠️", "Breakdowns - Compactors"),
    "Predictive Capex": ("📈", "Predictive Capex"),
}

icon, page_title = SECTION_TITLES[section]
st.header("National Supply Co - KPI Dashboard")
st.subheader(f"{icon} {page_title}")





# ============================================================
# 2. SUBURB COORDINATES LOOKUP
# ============================================================
@st.cache_data
def load_postcode_lookup():
    postcodes_df = pd.read_csv("data/australian_postcodes.csv")
    postcodes_df = postcodes_df[["locality", "state", "long", "lat"]].dropna(subset=["lat", "long"])
    postcodes_df = postcodes_df[(postcodes_df["lat"] != 0) & (postcodes_df["long"] != 0)]
    postcodes_df["locality"] = postcodes_df["locality"].str.upper()
    return postcodes_df.groupby(["locality", "state"])[["lat", "long"]].first()

postcodes_lookup = load_postcode_lookup()

def get_suburb_coords(suburb, state):
    key = (suburb.upper(), state)
    if key in postcodes_lookup.index:
        row = postcodes_lookup.loc[key]
        return row["lat"], row["long"]
    return None, None





# ============================================================
# 3. LOAD DATA FILES (shared by every tab)
# ============================================================

def extract_coords(row):
    coords = get_suburb_coords(row["Suburb"], row["State"])
    return pd.Series({"lat": coords[0], "lon": coords[1]})

UPLOAD_KEYS = ["asset_file", "coretex_file", "aroflo_file", "verified_file", "lifetime_file"]
using_uploaded_files = all(st.session_state.get(key) is not None for key in UPLOAD_KEYS)

STATE_COLORS = {
    "NSW": "#4C78A8",
    "VIC": "#F58518",
    "QLD": "#E45756",
    "WA":  "#72B7B2",
    "SA":  "#54A24B",
    "TAS": "#EECA3B",
    "ACT": "#B279A2",
    "NT":  "#FF9DA6",
}

STATE_ORDER = ["NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT"]

if using_uploaded_files:
    for key in UPLOAD_KEYS:
        st.session_state[key].seek(0)
    nsc_df = pd.read_excel(st.session_state["asset_file"])
    coretex_df = pd.read_excel(st.session_state["coretex_file"])
    aroflo_df = pd.read_excel(st.session_state["aroflo_file"])
    verified_df = pd.read_excel(st.session_state["verified_file"])
    lifetime_df = pd.read_excel(st.session_state["lifetime_file"], sheet_name="Lifetime Spend by Year")
else:
    nsc_df = pd.read_excel("data/nationwide_supply_asset_list.xlsx")
    coretex_df = pd.read_excel("data/coretex_equipment_records.xlsx")
    aroflo_df = pd.read_excel("data/aroflo_invoicing_report.xlsx")
    verified_df = pd.read_excel("data/verified_signin_records.xlsx")
    lifetime_df = pd.read_excel("data/lifetime_maintenance_spend.xlsx", sheet_name="Lifetime Spend by Year")

nsc_df["Asset Type"] = nsc_df["Asset Make/Model"].str.split(" - ").str[0]
nsc_df[["lat", "lon"]] = nsc_df.apply(extract_coords, axis=1)
nsc_df["Installation Date"] = pd.to_datetime(nsc_df["Installation Date"])  # needed by Planned Servicing, Breakdowns AND Predictive Capex

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

nsc_df["Location Tier"] = nsc_df["Suburb"].apply(classify_tier)
nsc_df["Pricing Tier"] = nsc_df["Location Tier"].replace({"Near-Regional": "Regional", "Far-Regional": "Regional"})

aroflo_df["Invoice Date"] = pd.to_datetime(aroflo_df["Invoice Date"])

verified_df["Sign-In Date"] = pd.to_datetime(verified_df["Sign-In Date & Time"])
verified_df["Asset Serial"] = verified_df["Purpose of Visit"].str.split("Asset ").str[1]
verified_df["Visit Type"] = verified_df["Purpose of Visit"].str.split(" - Asset").str[0]





# ============================================================
# 4. REPORTING PERIOD PICKER (shared - sidebar)
# ============================================================
st.sidebar.markdown("### Reporting period")
AS_OF_DATE = pd.Timestamp(st.sidebar.date_input("Reporting period end date", value=pd.Timestamp("2025-12-31")))
recency_cutoff = AS_OF_DATE - pd.Timedelta(days=60)





# ============================================================
# 5. MAP STYLING
# ============================================================
def style_map(fig, dark):
    if dark:
        fig.update_geos(
            landcolor="rgb(40,40,40)", showland=True, showcountries=True,
            countrycolor="rgb(90,90,90)", bgcolor="rgba(0,0,0,0)",
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
    else:
        fig.update_geos(
            landcolor="rgb(235,235,230)", showland=True, showcountries=True,
            countrycolor="rgb(180,180,180)", bgcolor="rgba(0,0,0,0)",
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="black"))
    return fig

dark_maps = st.sidebar.toggle("Dark mode maps")





# ============================================================
# 6. TAB - ABOUT US
# ============================================================
if section == "About Us":

    text_col, photo_col = st.columns([3, 2])

    with text_col:
        st.markdown(
            "This dashboard tracks all the core KPIs below for balers and compactors across Nationwide Supply Co's store network."
        )
        st.markdown(
            "Built for Coretex to manage each month to review with NSC's Facilities Operations team."
        )
        st.write("")
        st.write("")
        st.write("")
        st.subheader("Core KPIs")

    with photo_col:
        with st.container(key="about_photos"):
            baler_col, compactor_col = st.columns(2)
            with baler_col:
                st.image("assets/baler_image.png", caption="Baler", width=200)
            with compactor_col:
                st.image("assets/compactor_image.png", caption="Compactor", width=320)

    st.markdown("""
        <style>
        .st-key-about_photos {
            margin-top: -50px;
        }
        </style>
    """, unsafe_allow_html=True)

    coverage_items = [
        {"icon": "🦺", "title": "Safety Compliance", "description": "Verified is NSC's contractor safety system, requiring sign-in and induction for every contractor before they can start work on site."},
        {"icon": "💲", "title": "Pricing Compliance", "description": "Checks invoiced preventative service prices against contracted rates by location tier."},
        {"icon": "📋", "title": "Asset Register Accuracy", "description": "Checks that assets on site match what's recorded in the asset register."},
        {"icon": "🗓️", "title": "Planned Servicing", "description": "Tracks whether preventative servicing is happening on schedule across the store network."},
        {"icon": "⚠️", "title": "Breakdowns", "description": "Tracks breakdown frequency, cost and location for balers and compactors."},
        {"icon": "📈", "title": "Predictive Capex", "description": "Flags assets likely to need replacement based on cost and age trends."},
    ]

    row1 = st.columns(3)
    row2 = st.columns(3)
    card_columns = row1 + row2

    for index, item in enumerate(coverage_items):
        with card_columns[index]:
            with st.container(border=True):
                st.markdown(
                    f"<div style='display:flex; align-items:center; gap:10px;'>"
                    f"<span style='font-size:36px; line-height:1;'>{item['icon']}</span>"
                    f"<span style='font-size:19px; font-weight:700;'>{item['title']}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
                st.write("")
                st.write(item["description"])





# ============================================================
# 7. TAB - UPLOAD FILES
# ============================================================
elif section == "Upload Files":

    st.write("Drop in the latest export from each of the four source systems to refresh the dashboard.")

    row1_a, row1_b = st.columns(2)
    with row1_a:
        asset_file = st.file_uploader("NSC asset register", type=["xlsx"], key="asset_file")
    with row1_b:
        coretex_file = st.file_uploader("Coretex equipment records", type=["xlsx"], key="coretex_file")

    row2_a, row2_b = st.columns(2)
    with row2_a:
        aroflo_file = st.file_uploader("Aroflo 2yr invoicing report", type=["xlsx"], key="aroflo_file")
    with row2_b:
        lifetime_file = st.file_uploader("Aroflo lifetime maintenance spend", type=["xlsx"], key="lifetime_file")

    row3_a, row3_b = st.columns(2)
    with row3_a:
        verified_file = st.file_uploader("Verified sign-in records", type=["xlsx"], key="verified_file")

    uploaded = [asset_file, coretex_file, aroflo_file, verified_file, lifetime_file]
    st.progress(sum(f is not None for f in uploaded) / len(uploaded))

    if all(uploaded):
        st.success("All 5 files uploaded - the dashboard is now using this data instead of the local sample files.")
    else:
        st.info(f"{sum(f is not None for f in uploaded)} of 5 files uploaded - showing local sample data until all 5 are provided.")

    st.info("Before reviewing the dashboard, set the **Reporting period end date** in the sidebar to match the month these files cover - the on-time rates and trend charts are calculated relative to that date.")




# ============================================================
# 8. TAB - SAFETY COMPLIANCE
# ============================================================
elif section == "Safety Compliance":

    st.write("")

    st.markdown("Checks that contractors signed in and completed induction before starting work on site.")

    st.write("")

    with st.expander("More Info"):
        st.markdown(
            "- Verified logs contractor sign-in and induction before work starts on site\n"
            "- Incomplete inductions mean licence and insurance weren't verified, which is a WHS and compliance risk"
        )

    st.divider()

    target_year_month = AS_OF_DATE.strftime("%Y-%m")
    verified_all = verified_df.copy()
    verified_all["YearMonth"] = verified_all["Sign-In Date"].dt.strftime("%Y-%m")
    verified_pairs_any = set(zip(verified_all["Asset Serial"], verified_all["YearMonth"], verified_all["Visit Type"]))
    verified_pairs_completed = set(zip(
        verified_all[verified_all["Induction Completed"] == "Yes"]["Asset Serial"],
        verified_all[verified_all["Induction Completed"] == "Yes"]["YearMonth"],
        verified_all[verified_all["Induction Completed"] == "Yes"]["Visit Type"]
    ))

    this_month_invoices = aroflo_df[
        aroflo_df["Invoice Date"].dt.strftime("%Y-%m") == target_year_month
    ].copy()

    compliance_categories = []
    missing_signin_rows = []
    incomplete_induction_asset_rows = []
    for index, row in this_month_invoices.iterrows():
        pair = (row["Asset Serial Number"], target_year_month, row["Job Type"])
        if pair in verified_pairs_completed:
            compliance_categories.append("Compliant")
        else:
            compliance_categories.append("Not Compliant")
            if pair in verified_pairs_any:
                incomplete_induction_asset_rows.append(row)
            else:
                missing_signin_rows.append(row)

    this_month_invoices["Category"] = compliance_categories
    missing_signin_df = pd.DataFrame(missing_signin_rows)
    incomplete_induction_df = pd.DataFrame(incomplete_induction_asset_rows)

    signed_in_count = compliance_categories.count("Compliant")
    compliance_rate_this_month = (signed_in_count / len(this_month_invoices) * 100) if len(this_month_invoices) > 0 else 0

    trend_rows = []
    end_period = AS_OF_DATE.to_period("M")
    start_period = end_period - 23
    period_range = pd.period_range(start_period, end_period, freq="M")
    for period in period_range:
        year_month = str(period)
        invoices_this_period = aroflo_df[
            aroflo_df["Invoice Date"].dt.strftime("%Y-%m") == year_month
        ]
        if len(invoices_this_period) == 0:
            trend_rows.append({"YearMonth": year_month, "Compliance %": None})
            continue
        matched = 0
        for index, row in invoices_this_period.iterrows():
            pair = (row["Asset Serial Number"], year_month, row["Job Type"])
            if pair in verified_pairs_completed:
                matched += 1
        rate = matched / len(invoices_this_period) * 100
        trend_rows.append({"YearMonth": year_month, "Compliance %": rate})

    compliance_trend_df = pd.DataFrame(trend_rows)
    compliance_2yr_avg = compliance_trend_df["Compliance %"].mean()

    store_to_lat = dict(zip(nsc_df["Store #"], nsc_df["lat"]))
    store_to_lon = dict(zip(nsc_df["Store #"], nsc_df["lon"]))
    store_to_name = dict(zip(nsc_df["Store #"], nsc_df["Store Name"]))
    this_month_invoices["lat"] = this_month_invoices["Store Reference"].map(store_to_lat)
    this_month_invoices["lon"] = this_month_invoices["Store Reference"].map(store_to_lon)


    col1, col2, col3 = st.columns(3)
    col1.metric("Invoiced jobs fully sign-in compliant", f"{signed_in_count} of {len(this_month_invoices)}")
    col2.metric("This month compliance", f"{compliance_rate_this_month:.1f}%", delta=f"{compliance_rate_this_month - compliance_2yr_avg:.1f}% vs 2yr avg")
    col3.metric("2yr average", f"{compliance_2yr_avg:.1f}%")

    st.divider()

    insight_lines = []
    if len(incomplete_induction_df) > 0:
        insight_lines.append(
            f"{len(incomplete_induction_df)} job(s) were signed in but had an incomplete induction - this is commonly a new technician who hasn't attended an NSC site before. "
            "Recommend reviewing new technician set-up in Verified to reduce this lag."
        )
    if len(missing_signin_df) > 0:
        insight_lines.append(
            f"{len(missing_signin_df)} job(s) had no matching sign-in at all - follow up required to confirm who attended site and why they didn't sign in."
        )

    if insight_lines:
        st.warning("⚠️ " + "  \n".join(insight_lines))
    else:
        st.success("All invoiced jobs this period were fully sign-in compliant.")

    # ---------- missing sign-ins dropdown ----------
    if len(missing_signin_df) > 0:
        missing_signin_df["Store Name"] = missing_signin_df["Store Reference"].map(store_to_name)
        missing_signin_df["Technician Name"] = "Unknown"
        with st.expander(f"View {len(missing_signin_df)} invoiced job(s) with no matching sign-in"):
            missing_display = missing_signin_df[[
                "Invoice Number", "Invoice Date", "Store Reference", "Store Name", "Asset Serial Number", "Job Type", "Technician Name"
            ]].sort_values("Invoice Date").copy()
            missing_display["Invoice Date"] = missing_display["Invoice Date"].dt.date
            st.dataframe(missing_display)
    else:
        st.success("All invoiced jobs this period have a matching sign-in record.")


    # ---------- incomplete inductions dropdown ----------
    if len(incomplete_induction_df) > 0:
        incomplete_induction_df["Store Name"] = incomplete_induction_df["Store Reference"].map(store_to_name)

        pair_to_tech = dict(zip(
            zip(verified_all["Asset Serial"], verified_all["YearMonth"], verified_all["Visit Type"]),
            verified_all["Technician Name"]
        ))
        incomplete_tech_names = []
        for index, row in incomplete_induction_df.iterrows():
            pair = (row["Asset Serial Number"], target_year_month, row["Job Type"])
            incomplete_tech_names.append(pair_to_tech.get(pair, "Unknown"))
        incomplete_induction_df["Technician Name"] = incomplete_tech_names

        with st.expander(f"View {len(incomplete_induction_df)} job(s) signed in but with incomplete induction"):
            incomplete_display = incomplete_induction_df[[
                "Invoice Number", "Invoice Date", "Store Reference", "Store Name", "Asset Serial Number", "Job Type", "Technician Name"
            ]].sort_values("Invoice Date").copy()
            incomplete_display["Invoice Date"] = incomplete_display["Invoice Date"].dt.date
            st.dataframe(incomplete_display)
    else:
        st.success("No signed-in jobs had incomplete inductions this period.")

    st.write("")
    st.write("")
    st.write("")

    trend_data = compliance_trend_df.dropna(subset=["Compliance %"])
    trend_fig = px.line(trend_data, x="YearMonth", y="Compliance %", title="Sign-In Compliance - Last 2 Years")
    trend_fig.update_yaxes(range=[0, 100], dtick=20, ticksuffix="%")
    trend_fig.update_xaxes(tickangle=-45)
    trend_fig.update_layout(height=300, margin={"l":0,"r":0,"t":40,"b":40}, xaxis_title=None, yaxis_title=None)
    x_min = trend_data["YearMonth"].min()
    x_max = trend_data["YearMonth"].max()
    y_min = trend_data["Compliance %"].min()
    y_max = trend_data["Compliance %"].max()
    trend_fig.add_scatter(
        x=[x_min, x_max], y=[y_min, y_max],
        mode="lines", name="Overall Trend", line=dict(dash="dot", color="grey")
    )
    st.plotly_chart(trend_fig, use_container_width=True)

    st.write("")
    st.write("")
    st.write("")

    st.divider()

    # ---------- map ----------
    signin_map_fig = px.scatter_geo(
        this_month_invoices, lat="lat", lon="lon",
        hover_name="Store Name",
        hover_data={"Asset Serial Number": True, "Job Type": True, "lat": False, "lon": False},
        color="Category",
        color_discrete_map={"Compliant": "green", "Not Compliant": "red"},
        scope="world",
    )
    signin_map_fig.update_traces(marker=dict(size=10))
    signin_map_fig.update_geos(
        lataxis_range=[-45, -9], lonaxis_range=[108, 156],
        showland=True, landcolor="rgb(235,235,230)", showcountries=True,
    )
    signin_map_fig.update_layout(
        title=dict(text="This Month's Invoiced Jobs - Sign-In Compliance", x=0.5, xanchor="center"),
        margin={"r":40,"t":50,"l":0,"b":0}, height=450,
        legend=dict(x=0.01, y=0.99, xanchor="left", yanchor="top")
    )
    style_map(signin_map_fig, dark_maps)
    st.plotly_chart(signin_map_fig, use_container_width=True)






# ============================================================
# 9. TAB - PRICING COMPLIANCE
# ============================================================
elif section == "Pricing Compliance":

    st.write("")

    st.markdown("Checks invoiced preventative service prices against contracted rates by asset type and location tier.")

    st.write("")

    with st.expander("More Info"):
        st.markdown(
            "- The contract has agreed rates for preventative services for each asset type and location tier (Metro/Regional)\n"
            "- This dashboard reconciles invoices against those rates to catch manual invoicing errors or unauthorised increases\n"
            "- Catches over/undercharges early, before they compound across the store network"
        )

    st.divider()

    # ---------- metric logic ----------
    RATE = {
        ("Baler", "Metro"): 340, ("Baler", "Regional"): 408,
        ("Compactor", "Metro"): 490, ("Compactor", "Regional"): 588,
    }

    serial_to_type = dict(zip(nsc_df["Serial Number"], nsc_df["Asset Type"]))
    serial_to_pricing_tier = dict(zip(nsc_df["Serial Number"], nsc_df["Pricing Tier"]))

    prev_df = aroflo_df[aroflo_df["Job Type"] == "Preventative Service"].copy()
    prev_df["Asset Type"] = prev_df["Asset Serial Number"].map(serial_to_type)
    prev_df["Pricing Tier"] = prev_df["Asset Serial Number"].map(serial_to_pricing_tier)

    expected_prices = []
    for index, row in prev_df.iterrows():
        asset_type = row["Asset Type"]
        pricing_tier = row["Pricing Tier"]
        expected_prices.append(RATE[(asset_type, pricing_tier)])

    prev_df["Expected Price"] = expected_prices

    flagged_df = prev_df[prev_df["Amount (AUD)"] != prev_df["Expected Price"]].copy()

     # ---------- metrics row ----------

    compliance_rate = (len(prev_df) - len(flagged_df)) / len(prev_df) * 100

    col1, col2, col3 = st.columns(3)
    col1.metric("Invoices flagged", len(flagged_df))
    col2.metric("Preventative invoices checked", len(prev_df))
    col3.metric("Pricing compliance rate", f"{compliance_rate:.1f}%")

    st.write("")
    st.divider()
    # ---------- pricing insight caption ----------

    if len(flagged_df) == 0:
        st.success("All preventative invoices this period were priced correctly.")
    else:
        total_variance = (flagged_df["Amount (AUD)"] - flagged_df["Expected Price"]).sum()
        if total_variance > 0:
            st.warning(f"⚠️ {len(flagged_df)} invoice(s) flagged, resulting in a total overcharge of ${total_variance:,.0f} - Coretex to review with accounts dept.")
        elif total_variance < 0:
            st.warning(f"⚠️ {len(flagged_df)} invoice(s) flagged, resulting in a total undercharge of ${abs(total_variance):,.0f}.")
        else:
            st.warning(f"⚠️ {len(flagged_df)} invoice(s) flagged for incorrect pricing, though total charged happened to match total expected overall.")

    if len(flagged_df) > 0:


        # ---------- flagged invoices dropdown ----------
        flagged_display = flagged_df[[
            "Invoice Number", "Invoice Date", "Store Reference", "Asset Serial Number",
            "Asset Type", "Pricing Tier", "Amount (AUD)", "Expected Price"
        ]].rename(columns={"Amount (AUD)": "Charged"}).sort_values("Invoice Date")

        with st.expander(f"View {len(flagged_df)} flagged invoice(s)"):
            st.dataframe(flagged_display)

    st.write("")
    st.write("")

    # ---------- pricing scatter across all preventative invoices ----------
    st.write("")
    prev_df["Status"] = "Correctly Priced"
    prev_df.loc[prev_df["Amount (AUD)"] != prev_df["Expected Price"], "Status"] = "Flagged"

    scatter_fig = px.scatter(
        prev_df, x="Invoice Date", y="Amount (AUD)", color="Status",
        color_discrete_map={"Correctly Priced": "#c7c7c7", "Flagged": "red"},
        title="Preventative Servicing Prices - Last 2 Years"
    )
    scatter_fig.update_yaxes(rangemode="tozero", tickprefix="$")
    scatter_fig.update_layout(height=350, margin={"l":0,"r":0,"t":40,"b":0}, yaxis_title=None)

    for (asset_type, tier), price in RATE.items():
        scatter_fig.add_hline(
            y=price, line_dash="dot", line_color="grey",
            annotation_text=f"{asset_type} {tier} ${price}", annotation_position="top right"
        )

    st.plotly_chart(scatter_fig, use_container_width=True)

    st.caption(
        "Each dot is an invoiced preventative service; dashed lines mark the contracted rate per asset type and location tier.  \n"
        "Red dots are flagged (priced above or below the rate) - Coretex need to review why they charged NSC a rate that is outside the contracted scope.  \n"
        "Over charged invoices may require accounts to issue a credit note."
    )




# ============================================================
# 10. TAB - ASSET ACCURACY
# ============================================================
elif section == "Asset Register Accuracy":

    st.write("")

    st.markdown("Reconciles NSC's asset register against Coretex's records to catch what's missing, newly added, or removed.")

    st.write("")

    with st.expander("More Info"):
        st.markdown(
            "- NSC's asset register and Coretex's equipment records should always match, since both track what's actually installed on site\n"
            "- Keeping them aligned matters because servicing, safety compliance and billing all rely on knowing exactly what's on site\n"
            "- Replacements are new installs matched to a removed asset at the same store\n"
            "- New Stores are additional units with no matched removal\n"
            "- Needs Review flags anything that doesn't fit that pattern, including removals with no matching new install"
        )

    # ---------- metric logic ----------
    nsc_serials = set(nsc_df["Serial Number"])
    coretex_serials = set(coretex_df["Serial Number"])
    missing_from_coretex = nsc_serials - coretex_serials
    missing_from_nsc = coretex_serials - nsc_serials
    asset_match_rate = (len(coretex_serials) - len(missing_from_nsc)) / len(coretex_serials) * 100

    # ---------- helper functions ----------
    def extract_coords(row):
        coords = get_suburb_coords(row["Suburb"], row["State"])
        return pd.Series({"lat": coords[0], "lon": coords[1]})

    def classify_installation(date_value):
        if date_value >= recency_cutoff:
            return "New Asset"
        else:
            return "Needs Review"

    # ---------- dataframe logic ----------
    pending_coretex_df = coretex_df[coretex_df["Serial Number"].isin(missing_from_nsc)].copy()
    pending_coretex_df["Asset Type"] = pending_coretex_df["Equipment Type"]
    pending_coretex_df["Store Name"] = pending_coretex_df["Store Reference"]
    pending_coretex_df["Installation Date"] = pd.to_datetime(pending_coretex_df["Installation Date"])

    pending_coretex_df[["lat", "lon"]] = pending_coretex_df.apply(extract_coords, axis=1)
    pending_coretex_df["Category"] = pending_coretex_df["Installation Date"].apply(classify_installation)

    new_installs_df = pending_coretex_df[pending_coretex_df["Category"] == "New Asset"]
    needs_review_gap_df = pending_coretex_df[pending_coretex_df["Category"] == "Needs Review"]

    coretex_status_map = dict(zip(coretex_df["Serial Number"], coretex_df["Status"]))
    coretex_change_date_map = dict(zip(coretex_df["Serial Number"], pd.to_datetime(coretex_df["Status Change Date"])))
    nsc_df["Coretex Status"] = nsc_df["Serial Number"].map(coretex_status_map)
    nsc_df["Status Change Date"] = nsc_df["Serial Number"].map(coretex_change_date_map)
    removed_assets_df = nsc_df[
        (nsc_df["Coretex Status"] == "Inactive") &
        (nsc_df["Status Change Date"] >= recency_cutoff)
    ].copy()

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

    missing_entirely_df = nsc_df[nsc_df["Serial Number"].isin(missing_from_coretex)].copy()

    needs_review_combined = pd.concat([
        needs_review_gap_df.rename(columns={"Equipment Type": "Type", "Store Reference": "Store"})[["Serial Number", "Type", "Store", "State", "Installation Date"]].assign(Reason="On Coretex, not yet on NSC register (2+ months)"),
        missing_entirely_df.rename(columns={"Asset Make/Model": "Type", "Store Name": "Store"})[["Serial Number", "Type", "Store", "State"]].assign(Reason="Missing from Coretex entirely - unexpected")
    ], ignore_index=True)

    nsc_df["Category"] = nsc_df["Asset Type"]
    removed_serials_set = set(removed_assets_df["Serial Number"])
    nsc_df.loc[nsc_df["Serial Number"].isin(removed_serials_set), "Category"] = "Removed Asset"

    map_df = pd.concat([
        nsc_df[["Store Name", "State", "Asset Type", "Category", "lat", "lon"]],
        pending_coretex_df[["Store Name", "State", "Asset Type", "Category", "lat", "lon"]]
    ], ignore_index=True)

    # ---------- summary metric + flag ----------
    st.divider()

    st.metric("Asset register accuracy", f"{asset_match_rate:.1f}%")

    if len(new_installs_df) > 0 or len(removed_assets_df) > 0:
        st.warning(f"⚠️ {len(new_installs_df)} new asset(s) need to be added and {len(removed_assets_df)} need to be removed from NSC's register.")

    # ---------- New/Removed/Needs Review dropdowns ----------
    # if len(new_installs_df) > 0:
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

    st.divider()

    st.write("")
    st.write("")
    st.write("")

    asset_changes = pd.DataFrame({
        "Status": ["Total assets", "New Assets", "Removed Assets", "Needs Review"],
        "Count": [len(coretex_serials), len(new_installs_df), len(removed_assets_df), len(needs_review_combined)]
    })

    col_table, col_map = st.columns([1, 3])

    with col_table:
        replacement_count = len(new_installs_df[new_installs_df["Match Type"] == "Replacement"])
        new_store_count = len(new_installs_df[new_installs_df["Match Type"] == "New Store"])
        needs_review_count = len(needs_review_combined) + len(removed_assets_df[removed_assets_df["Match Type"] == "Unmatched removal"])
        no_change_count = len(coretex_serials) - replacement_count - new_store_count - needs_review_count

        asset_pie_df = pd.DataFrame({
            "Status": ["No Change", "Replacements", "New Stores", "Needs Review"],
            "Count": [no_change_count, replacement_count, new_store_count, needs_review_count]
        })

        pie_fig = px.pie(
            asset_pie_df, names="Status", values="Count",
            title=f"Asset Register<br>{len(coretex_serials)} Total Assets",
            color="Status",
            hole=0.5,
            color_discrete_map={
                "No Change": "#9e9e9e",
                "Replacements": "green",
                "New Stores": "#f2c744",
                "Needs Review": "red"
            }
        )
        pie_fig.update_traces(domain=dict(x=[0, 0.6], y=[0, 1]), textinfo="none")

        total = asset_pie_df["Count"].sum()
        label_colors = {"No Change": "#9e9e9e", "Replacements": "green", "New Stores": "#f2c744", "Needs Review": "red"}
        y_positions = [0.95, 0.65, 0.35, 0.05]
        for (idx, row), y in zip(asset_pie_df.iterrows(), y_positions):
            pct = row["Count"] / total * 100
            pie_fig.add_annotation(
                x=0.75, y=y, xref="paper", yref="paper",
                text=f"<b>{row['Status']}</b><br>{row['Count']} ({pct:.0f}%)",
                showarrow=False, align="left", xanchor="left",
                font=dict(color=label_colors[row["Status"]], size=13)
            )

        pie_fig.update_layout(
            margin={"l": 0, "r": 0, "t": 60, "b": 20},
            height=320,
            showlegend=False
        )
        st.plotly_chart(pie_fig, use_container_width=True)
        st.caption("Replacements are new installs matched to a removed asset at the same store. New Stores are additional units with no matched removal. Needs Review flags anything that doesn't fit that pattern, including removals with no matching new install.")

    # ---------- map ----------
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
            margin={"r":40,"t":50,"l":0,"b":60}, height=450,
            legend=dict(orientation="h", yanchor="top", y=-0.08, xanchor="center", x=0.5),
            legend_title_text=""
        )
        fig.update_traces(marker=dict(size=10))
        style_map(fig, dark_maps)
        st.plotly_chart(fig, width="stretch")






# ============================================================
# 11. TAB - PLANNED SERVICING
# ============================================================
elif section == "Planned Servicing":

    st.write("")

    st.markdown("Checks whether scheduled preventative servicing is happening on time across the store network.")

    st.write("")

    with st.expander("More Info"):
        st.markdown(
            "- Each asset has a scheduled preventative service month based on its install date\n"
            "- This dashboard checks whether that servicing was actually completed on time, and tracks the trend over the last 2 years\n"
            "- Flags outstanding services early, before a missed service turns into an unplanned breakdown"
        )

    st.divider()

    # ---------- metric logic ----------
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

    # ---------- metrics row ----------

    completed_stores = set(nsc_df[nsc_df["Serial Number"].isin(on_time_serials)]["Store #"])
    outstanding_stores = set(nsc_df[nsc_df["Serial Number"].isin(outstanding_serials)]["Store #"])
    outstanding_df = nsc_df[nsc_df["Serial Number"].isin(outstanding_serials)]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Completions on time (this month)", f"{servicing_on_time_rate:.1f}%", delta=f"{servicing_on_time_rate - servicing_2yr_avg_rate:.1f}% vs 2yr avg")
    col2.metric("Completions on time (2yr avg)", f"{servicing_2yr_avg_rate:.1f}%")
    col3.metric("Completed", f"{len(completed_stores)} stores")
    col4.metric("Outstanding", f"{len(outstanding_stores)} stores")

    st.divider()

    rate_diff = servicing_on_time_rate - servicing_2yr_avg_rate
    if rate_diff < -2:
        st.warning("⚠️ Below average result - recommend investigating further why the outstanding is higher than standard.")
    elif rate_diff > 2:
        st.success("Above average result.")
    else:
        st.info("In line with the 2-year average.")

    # ---------- completed/outstanding map ----------
    servicing_map_df = nsc_df[nsc_df["Serial Number"].isin(scheduled_serials)].copy()

    def classify_servicing(serial_number):
        if serial_number in on_time_serials:
            return "Completed"
        else:
            return "Outstanding"

    servicing_map_df["Category"] = servicing_map_df["Serial Number"].apply(classify_servicing)

    # ---------- completed/outstanding tables ----------
    completed_display_df = servicing_map_df[servicing_map_df["Category"] == "Completed"]
    outstanding_display_df = servicing_map_df[servicing_map_df["Category"] == "Outstanding"]

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

    st.write("")
    st.write("")
    st.write("")

    colA, colSpacer, colB = st.columns([4, 1, 5])

    # ---------- on-time trend line chart ----------
    with colA:
        trend_fig = px.line(monthly_trend, x="YearMonth", y="On Time %", title="On-Time Rate - Last 2 Years")
        trend_fig.update_yaxes(range=[70, 100], dtick=10, ticksuffix="%")
        trend_fig.update_xaxes(tickangle=-45)
        trend_fig.update_layout(height=220, margin={"l":0,"r":0,"t":40,"b":40}, xaxis_title=None, yaxis_title=None)
        st.plotly_chart(trend_fig, use_container_width=True)

    # ---------- outstanding by state bar chart ----------
    with colB:
        state_fig = px.bar(
        outstanding_df.groupby("State").size().reset_index(name="Outstanding"),
        x="State", y="Outstanding", title="Outstanding Services by State"
        )
        state_fig.update_yaxes(dtick=1)
        state_fig.update_layout(height=220, margin={"l":0,"r":0,"t":40,"b":0}, xaxis_title=None, yaxis_title=None)
        st.plotly_chart(state_fig, use_container_width=True)

    st.write("")
    st.write("")
    st.write("")

    st.divider()

    # ---------- map visual ----------
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
    servicing_fig.update_traces(marker=dict(size=10))
    style_map(servicing_fig, dark_maps)
    st.plotly_chart(servicing_fig, use_container_width=True)






# ============================================================
# 12. TAB - BREAKDOWNS-BALERS
# ============================================================
elif section == "Breakdowns-Balers":

    st.write("")

    st.markdown("Tracks unplanned baler breakdown repairs - frequency, cost and location this month versus the 2-year average.")

    st.write("")

    with st.expander("More Info"):
        st.markdown(
            "- Breakdowns are unplanned and unbudgeted, unlike preventative servicing\n"
            "- Can signal a specific unit needing escalation (repeat failures, a major fault) rather than routine wear and tear\n"
            "- Helps separate one-off repair costs from patterns worth investigating further with Facility Managers"
        )

    st.divider()

    # ---------- data prep ----------
    serial_to_type = dict(zip(nsc_df["Serial Number"], nsc_df["Asset Type"]))
    store_to_state = dict(zip(nsc_df["Store #"], nsc_df["State"]))
    store_to_lat = dict(zip(nsc_df["Store #"], nsc_df["lat"]))
    store_to_lon = dict(zip(nsc_df["Store #"], nsc_df["lon"]))
    serial_to_install_date = dict(zip(nsc_df["Serial Number"], nsc_df["Installation Date"]))

    breakdown_df = aroflo_df[aroflo_df["Job Type"] == "Breakdown Repair"].copy()
    breakdown_df["Asset Type"] = breakdown_df["Asset Serial Number"].map(serial_to_type)
    breakdown_df["State"] = breakdown_df["Store Reference"].map(store_to_state)
    breakdown_df["lat"] = breakdown_df["Store Reference"].map(store_to_lat)
    breakdown_df["lon"] = breakdown_df["Store Reference"].map(store_to_lon)

    type_breakdown_df = breakdown_df[breakdown_df["Asset Type"] == "Baler"]

    target_year_month = AS_OF_DATE.strftime("%Y-%m")
    this_month_breakdowns = type_breakdown_df[
        type_breakdown_df["Invoice Date"].dt.strftime("%Y-%m") == target_year_month
    ]

    # ---------- 2yr trend & averages ----------
    end_period = AS_OF_DATE.to_period("M")
    start_period = end_period - 23
    period_range = pd.period_range(start_period, end_period, freq="M")

    trend_rows = []
    for period in period_range:
        year_month = str(period)
        period_df = type_breakdown_df[type_breakdown_df["Invoice Date"].dt.strftime("%Y-%m") == year_month]
        trend_rows.append({
            "YearMonth": year_month,
            "Breakdowns": len(period_df),
            "Spend": period_df["Amount (AUD)"].sum()
        })
    trend_df = pd.DataFrame(trend_rows)
    breakdowns_2yr_avg = trend_df["Breakdowns"].mean()
    spend_2yr_avg = trend_df["Spend"].mean()

    breakdowns_count = len(this_month_breakdowns)
    spend_this_month = this_month_breakdowns["Amount (AUD)"].sum()

    count_delta = ((breakdowns_count - breakdowns_2yr_avg) / breakdowns_2yr_avg * 100) if breakdowns_2yr_avg else 0
    spend_delta = ((spend_this_month - spend_2yr_avg) / spend_2yr_avg * 100) if spend_2yr_avg else 0

    # ---------- metrics row ----------
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Breakdowns this month", breakdowns_count, delta=f"{count_delta:+.0f}% vs 2yr avg", delta_color="off")
    col2.metric("2yr avg breakdowns", f"{breakdowns_2yr_avg:.1f}")
    col3.metric("Spend this month", f"${spend_this_month:,.0f}", delta=f"{spend_delta:+.0f}% vs 2yr avg", delta_color="off")
    col4.metric("2yr avg spend", f"${spend_2yr_avg:,.0f}")

    st.divider()

    # ---------- data-driven insight ----------
    repeat_counts = this_month_breakdowns["Asset Serial Number"].value_counts()
    repeat_offenders = repeat_counts[repeat_counts > 1]

    serial_to_store = dict(zip(this_month_breakdowns["Asset Serial Number"], this_month_breakdowns["Store Name"]))
    serial_to_assettype = dict(zip(this_month_breakdowns["Asset Serial Number"], this_month_breakdowns["Asset Type"]))

    young_repeat_serials = []
    young_repeat_labels = []
    older_repeat_serials = []
    older_repeat_labels = []
    for serial, count in repeat_offenders.items():
        install_date = serial_to_install_date.get(serial)
        age_years = (AS_OF_DATE - install_date).days / 365.25 if pd.notna(install_date) else None
        label = f"{serial} - {serial_to_store.get(serial)} ({serial_to_assettype.get(serial)}, {count}x)"
        if age_years is not None and age_years <= 3:
            young_repeat_serials.append(serial)
            young_repeat_labels.append(label)
        else:
            older_repeat_serials.append(serial)
            older_repeat_labels.append(label)

    if young_repeat_serials:
        young_spend = this_month_breakdowns[this_month_breakdowns["Asset Serial Number"].isin(young_repeat_serials)]["Amount (AUD)"].sum()
        young_result = f"{', '.join(young_repeat_labels)} (${young_spend:,.0f})"
    else:
        young_result = None

    if older_repeat_serials:
        older_spend = this_month_breakdowns[this_month_breakdowns["Asset Serial Number"].isin(older_repeat_serials)]["Amount (AUD)"].sum()
        older_result = f"{', '.join(older_repeat_labels)} (${older_spend:,.0f})"
    else:
        older_result = None

    avg_repair_cost = type_breakdown_df["Amount (AUD)"].mean()
    high_cost_repairs = this_month_breakdowns[
        (this_month_breakdowns["Amount (AUD)"] > avg_repair_cost * 2) &
        (~this_month_breakdowns["Asset Serial Number"].isin(repeat_offenders.index))
    ]
    if len(high_cost_repairs) > 0:
        high_cost_result = ", ".join(
            f"{row['Asset Serial Number']} - {row['Store Name']} ({row['Asset Type']}, ${row['Amount (AUD)']:,.0f})"
            for index, row in high_cost_repairs.iterrows()
        )
    else:
        high_cost_result = None

    insight_lines = []
    if young_result:
        insight_lines.append(f"**Repeat breakdowns, 3yrs old or less (warranty candidates):** {young_result}")
    if older_result:
        insight_lines.append(f"**Repeat breakdowns, over 3yrs old (fault-finding/wear parts):** {older_result}")
    if high_cost_result:
        insight_lines.append(f"**Repairs costing over 2x the average (${avg_repair_cost:,.0f}):** {high_cost_result}")

    if insight_lines:
        st.warning("⚠️ " + "  \n".join(insight_lines))
    else:
        st.success("No repeat breakdowns or high-cost repairs flagged this month.")


    # ---------- breakdown details dropdown ----------
    with st.expander(f"View {len(this_month_breakdowns)} baler breakdown(s) this month"):
        breakdown_display = this_month_breakdowns[[
            "Invoice Number", "Invoice Date", "Store Reference", "Store Name",
            "Asset Serial Number", "Service Description", "Amount (AUD)"
        ]].sort_values("Invoice Date").copy()
        breakdown_display["Invoice Date"] = breakdown_display["Invoice Date"].dt.date
        st.dataframe(breakdown_display)

    st.write("")
    st.write("")
    st.write("")

    colA, colSpacer, colB = st.columns([4, 1, 5])

    # ---------- breakdowns by state bar chart ----------
    with colA:
        state_fig = px.bar(
            this_month_breakdowns.groupby("State").size().reset_index(name="Breakdowns"),
            x="State", y="Breakdowns", title="Breakdowns by State (This Month)"
        )
        state_fig.update_yaxes(dtick=1)
        state_fig.update_layout(height=300, margin={"l":0,"r":0,"t":40,"b":0}, xaxis_title=None, yaxis_title=None)
        st.plotly_chart(state_fig, use_container_width=True)

# ---------- spend by state per month stacked bar ----------
    with colB:
        heatmap_df = type_breakdown_df.copy()
        heatmap_df["YearMonth"] = heatmap_df["Invoice Date"].dt.strftime("%Y-%m")
        heatmap_df = heatmap_df[heatmap_df["YearMonth"].isin([str(period) for period in period_range])]

        state_month_df = heatmap_df.groupby(["YearMonth", "State"])["Amount (AUD)"].sum().reset_index()
        state_month_df = state_month_df.sort_values("YearMonth")

        state_order = [s for s in STATE_ORDER if s in state_month_df["State"].unique()]

        stacked_fig = px.bar(
            state_month_df, x="YearMonth", y="Amount (AUD)", color="State",
            category_orders={"State": state_order},
            color_discrete_map=STATE_COLORS,
            title="Breakdown Spend by State - Last 2 Years"
        )

        stacked_fig.update_yaxes(tickprefix="$")
        stacked_fig.update_xaxes(tickangle=-45)
        stacked_fig.update_layout(
            height=300,
            margin={"l": 0, "r": 0, "t": 40, "b": 90},
            xaxis_title=None, yaxis_title=None,
            legend=dict(
                orientation="h", traceorder="normal",
                yanchor="top", y=-0.45, xanchor="center", x=0.5
            )
        )
        st.plotly_chart(stacked_fig, use_container_width=True)

    st.divider()

    # ---------- map of breakdown locations ----------
    map_fig = px.scatter_geo(
        this_month_breakdowns, lat="lat", lon="lon",
        hover_name="Store Name",
        hover_data={"Asset Serial Number": True, "Amount (AUD)": True, "lat": False, "lon": False},
        scope="world",
    )
    map_fig.update_traces(marker=dict(size=10, color="red"))
    map_fig.update_geos(
        lataxis_range=[-45, -9], lonaxis_range=[108, 156],
        showland=True, landcolor="rgb(235,235,230)", showcountries=True,
    )
    map_fig.update_layout(
        title=dict(text="This Month's Baler Breakdowns - Locations", x=0.5, xanchor="center"),
        margin={"r":40,"t":50,"l":0,"b":0}, height=450,
    )
    style_map(map_fig, dark_maps)
    st.plotly_chart(map_fig, use_container_width=True)






# ============================================================
# 13. TAB - BREAKDOWNS-COMPACTORS
# ============================================================
elif section == "Breakdowns-Compactors":

    st.write("")

    st.markdown("Tracks unplanned compactor breakdown repairs - frequency, cost and location this month versus the 2-year average.")

    st.write("")

    with st.expander("More Info"):
        st.markdown(
            "- Breakdowns are unplanned and unbudgeted, unlike preventative servicing\n"
            "- Can signal a specific unit needing escalation (repeat failures, a major fault) rather than routine wear and tear\n"
            "- Helps separate one-off repair costs from patterns worth investigating further with Facility Managers"
        )

    st.divider()

    # ---------- data prep ----------
    serial_to_type = dict(zip(nsc_df["Serial Number"], nsc_df["Asset Type"]))
    store_to_state = dict(zip(nsc_df["Store #"], nsc_df["State"]))
    store_to_lat = dict(zip(nsc_df["Store #"], nsc_df["lat"]))
    store_to_lon = dict(zip(nsc_df["Store #"], nsc_df["lon"]))
    serial_to_install_date = dict(zip(nsc_df["Serial Number"], nsc_df["Installation Date"]))

    breakdown_df = aroflo_df[aroflo_df["Job Type"] == "Breakdown Repair"].copy()
    breakdown_df["Asset Type"] = breakdown_df["Asset Serial Number"].map(serial_to_type)
    breakdown_df["State"] = breakdown_df["Store Reference"].map(store_to_state)
    breakdown_df["lat"] = breakdown_df["Store Reference"].map(store_to_lat)
    breakdown_df["lon"] = breakdown_df["Store Reference"].map(store_to_lon)

    type_breakdown_df = breakdown_df[breakdown_df["Asset Type"] == "Compactor"]

    target_year_month = AS_OF_DATE.strftime("%Y-%m")
    this_month_breakdowns = type_breakdown_df[
        type_breakdown_df["Invoice Date"].dt.strftime("%Y-%m") == target_year_month
    ]

    # ---------- 2yr trend & averages ----------
    end_period = AS_OF_DATE.to_period("M")
    start_period = end_period - 23
    period_range = pd.period_range(start_period, end_period, freq="M")

    trend_rows = []
    for period in period_range:
        year_month = str(period)
        period_df = type_breakdown_df[type_breakdown_df["Invoice Date"].dt.strftime("%Y-%m") == year_month]
        trend_rows.append({
            "YearMonth": year_month,
            "Breakdowns": len(period_df),
            "Spend": period_df["Amount (AUD)"].sum()
        })
    trend_df = pd.DataFrame(trend_rows)
    breakdowns_2yr_avg = trend_df["Breakdowns"].mean()
    spend_2yr_avg = trend_df["Spend"].mean()

    breakdowns_count = len(this_month_breakdowns)
    spend_this_month = this_month_breakdowns["Amount (AUD)"].sum()

    count_delta = ((breakdowns_count - breakdowns_2yr_avg) / breakdowns_2yr_avg * 100) if breakdowns_2yr_avg else 0
    spend_delta = ((spend_this_month - spend_2yr_avg) / spend_2yr_avg * 100) if spend_2yr_avg else 0

    # ---------- metrics row ----------
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Breakdowns this month", breakdowns_count, delta=f"{count_delta:+.0f}% vs 2yr avg", delta_color="off")
    col2.metric("2yr avg breakdowns", f"{breakdowns_2yr_avg:.1f}")
    col3.metric("Spend this month", f"${spend_this_month:,.0f}", delta=f"{spend_delta:+.0f}% vs 2yr avg", delta_color="off")
    col4.metric("2yr avg spend", f"${spend_2yr_avg:,.0f}")

    st.divider()

    # ---------- data-driven insight ----------
    repeat_counts = this_month_breakdowns["Asset Serial Number"].value_counts()
    repeat_offenders = repeat_counts[repeat_counts > 1]

    serial_to_store = dict(zip(this_month_breakdowns["Asset Serial Number"], this_month_breakdowns["Store Name"]))
    serial_to_assettype = dict(zip(this_month_breakdowns["Asset Serial Number"], this_month_breakdowns["Asset Type"]))

    young_repeat_serials = []
    young_repeat_labels = []
    older_repeat_serials = []
    older_repeat_labels = []
    for serial, count in repeat_offenders.items():
        install_date = serial_to_install_date.get(serial)
        age_years = (AS_OF_DATE - install_date).days / 365.25 if pd.notna(install_date) else None
        label = f"{serial} - {serial_to_store.get(serial)} ({serial_to_assettype.get(serial)}, {count}x)"
        if age_years is not None and age_years <= 3:
            young_repeat_serials.append(serial)
            young_repeat_labels.append(label)
        else:
            older_repeat_serials.append(serial)
            older_repeat_labels.append(label)

    if young_repeat_serials:
        young_spend = this_month_breakdowns[this_month_breakdowns["Asset Serial Number"].isin(young_repeat_serials)]["Amount (AUD)"].sum()
        young_result = f"{', '.join(young_repeat_labels)} (${young_spend:,.0f})"
    else:
        young_result = None

    if older_repeat_serials:
        older_spend = this_month_breakdowns[this_month_breakdowns["Asset Serial Number"].isin(older_repeat_serials)]["Amount (AUD)"].sum()
        older_result = f"{', '.join(older_repeat_labels)} (${older_spend:,.0f})"
    else:
        older_result = None

    avg_repair_cost = type_breakdown_df["Amount (AUD)"].mean()
    high_cost_repairs = this_month_breakdowns[
        (this_month_breakdowns["Amount (AUD)"] > avg_repair_cost * 2) &
        (~this_month_breakdowns["Asset Serial Number"].isin(repeat_offenders.index))
    ]
    if len(high_cost_repairs) > 0:
        high_cost_result = ", ".join(
            f"{row['Asset Serial Number']} - {row['Store Name']} ({row['Asset Type']}, ${row['Amount (AUD)']:,.0f})"
            for index, row in high_cost_repairs.iterrows()
        )
    else:
        high_cost_result = None

    insight_lines = []
    if young_result:
        insight_lines.append(f"**Repeat breakdowns, 3yrs old or less (warranty candidates):** {young_result}")
    if older_result:
        insight_lines.append(f"**Repeat breakdowns, over 3yrs old (fault-finding/wear parts):** {older_result}")
    if high_cost_result:
        insight_lines.append(f"**Repairs costing over 2x the average (${avg_repair_cost:,.0f}):** {high_cost_result}")

    if insight_lines:
        st.warning("⚠️ " + "  \n".join(insight_lines))
    else:
        st.success("No repeat breakdowns or high-cost repairs flagged this month.")

    # ---------- breakdown details dropdown ----------
    with st.expander(f"View {len(this_month_breakdowns)} compactor breakdown(s) this month"):
        breakdown_display = this_month_breakdowns[[
            "Invoice Number", "Invoice Date", "Store Reference", "Store Name",
            "Asset Serial Number", "Service Description", "Amount (AUD)"
        ]].sort_values("Invoice Date").copy()
        breakdown_display["Invoice Date"] = breakdown_display["Invoice Date"].dt.date
        st.dataframe(breakdown_display)

    st.write("")
    st.write("")
    st.write("")

    colA, colSpacer, colB = st.columns([4, 1, 5])

    # ---------- breakdowns by state bar chart ----------
    with colA:
        state_fig = px.bar(
            this_month_breakdowns.groupby("State").size().reset_index(name="Breakdowns"),
            x="State", y="Breakdowns", title="Breakdowns by State (This Month)"
        )
        state_fig.update_yaxes(dtick=1)
        state_fig.update_layout(height=300, margin={"l":0,"r":0,"t":40,"b":0}, xaxis_title=None, yaxis_title=None)
        st.plotly_chart(state_fig, use_container_width=True)

# ---------- spend by state per month stacked bar ----------
    with colB:
        heatmap_df = type_breakdown_df.copy()
        heatmap_df["YearMonth"] = heatmap_df["Invoice Date"].dt.strftime("%Y-%m")
        heatmap_df = heatmap_df[heatmap_df["YearMonth"].isin([str(period) for period in period_range])]

        state_month_df = heatmap_df.groupby(["YearMonth", "State"])["Amount (AUD)"].sum().reset_index()
        state_month_df = state_month_df.sort_values("YearMonth")

        state_order = [s for s in STATE_ORDER if s in state_month_df["State"].unique()]

        stacked_fig = px.bar(
            state_month_df, x="YearMonth", y="Amount (AUD)", color="State",
            category_orders={"State": state_order},
            color_discrete_map=STATE_COLORS,
            title="Breakdown Spend by State - Last 2 Years"
        )

        stacked_fig.update_yaxes(tickprefix="$")
        stacked_fig.update_xaxes(tickangle=-45)
        stacked_fig.update_layout(
            height=300,
            margin={"l": 0, "r": 0, "t": 40, "b": 90},
            xaxis_title=None, yaxis_title=None,
            legend=dict(
                orientation="h", traceorder="normal",
                yanchor="top", y=-0.45, xanchor="center", x=0.5
            )
        )
        st.plotly_chart(stacked_fig, use_container_width=True)

    st.divider()

    # ---------- map of breakdown locations ----------
    map_fig = px.scatter_geo(
        this_month_breakdowns, lat="lat", lon="lon",
        hover_name="Store Name",
        hover_data={"Asset Serial Number": True, "Amount (AUD)": True, "lat": False, "lon": False},
        scope="world",
    )
    map_fig.update_traces(marker=dict(size=10, color="red"))
    map_fig.update_geos(
        lataxis_range=[-45, -9], lonaxis_range=[108, 156],
        showland=True, landcolor="rgb(235,235,230)", showcountries=True,
    )
    map_fig.update_layout(
        title=dict(text="This Month's Compactor Breakdowns - Locations", x=0.5, xanchor="center"),
        margin={"r":40,"t":50,"l":0,"b":0}, height=450,
    )
    style_map(map_fig, dark_maps)
    st.plotly_chart(map_fig, use_container_width=True)






# ============================================================
# 14. TAB - PREDICTIVE CAPEX
# ============================================================
elif section == "Predictive Capex":

    st.write("")

    st.markdown("Forecasts capex needs for the next 12 months, flagging units likely to need replacement.")

    st.write("")

    with st.expander("More Info"):
        st.markdown(
            "- Ageing or high-maintenance assets are a known cost risk, so it helps to plan replacement ahead of a major breakdown\n"
            "- Forecasts both proactive planned replacements and reactive unplanned breakdown spend for the next 12 months\n"
            "- Units are flagged as high risk based on their age, location and breakdown history"
        )

    # ---------- how this is calculated explainer ----------
    with st.expander("How this forecast is calculated"):
        st.markdown("""
        **Reactive (unplanned)** - predicts next year's breakdown spend per asset, based on:
        - Age and asset type
        - Location (metro vs regional)
        - Recent breakdown history

        **Proactive (planned)** - flags assets for replacement when **both**:
        - Age is near/past typical design life
        - Total lifetime breakdown spend to date has reached 50%+ of what a new unit would cost

        Also catches young "lemons" - flagged separately, since these usually need a
        warranty conversation, not a routine replacement.
        """)

    st.divider()

    # ---------- reactive model (regression) ----------
    from sklearn.linear_model import LinearRegression

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

    # ---------- proactive model (classification) ----------
    from sklearn.linear_model import LogisticRegression

    TYPICAL_LIFE = {"Baler": 10, "Compactor": 17.5}

    def calculate_life_ratio(row):
        typical_life = TYPICAL_LIFE[row["Asset Type"]]
        return row["Age at Year"] / typical_life

    lifetime_df["Life Ratio"] = lifetime_df.apply(calculate_life_ratio, axis=1)

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

    predict_df["Current Age"] = predict_df["Age at Year"] - 1
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

    col1, col2 = st.columns(2)


    # ---------- proactive/reactive metrics + recommended replacements dropdown ----------
    col1.metric("Proactive (planned)", f"${proactive_capex_forecast:,.0f}")

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

    st.divider()

    young_high_spend = high_risk_display[high_risk_display["Age (yrs)"] < 5]
    if len(young_high_spend) > 0:
        flagged_list = ", ".join(
            f"{row['Serial Number']} ({row['Asset Type']}, {row['Store Name']})"
            for _, row in young_high_spend.iterrows()
        )
        st.warning(
            f"⚠️ {len(young_high_spend)} unit(s) flagged as under 5 years old (young lemon) - likely chronic reliability issues rather than routine end-of-life,  \n"
            "worth escalating separately (e.g. manufacturer warranty claim) rather than routine replacement.\n\n"
            f"Flagged: {flagged_list}"
        )

    st.divider()

    with st.expander(f"View {len(high_risk_display)} recommended replacement(s)"):
        st.dataframe(high_risk_display)
    col2.metric("Reactive (unplanned)", f"${reactive_capex_forecast:,.0f}")

    # ---------- capex by state bar chart ----------
    st.write("")
    st.write("")
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

    st.divider()

    # ---------- recommended replacements map ----------
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
    capex_map_fig.update_traces(marker=dict(size=10))
    style_map(capex_map_fig, dark_maps)
    st.plotly_chart(capex_map_fig, use_container_width=True)
