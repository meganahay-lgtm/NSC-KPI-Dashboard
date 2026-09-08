import streamlit as st
import pandas as pd

st.title("NSC KPI Dashboard")

tab0, tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Upload Files", "Asset Accuracy", "Planned Servicing", "Breakdowns", "Spend",
    "Pricing", "Compliance", "Predictive Capex"
])

with tab0:
    st.subheader("Upload this month's files")
    st.write("Drop in the latest export from each system to refresh the dashboard")

    asset_file = st.file_uploader("Asset register", type=["xlsx"])
    coretex_file = st.file_uploader("Coretex equipment records", type=["xlsx"])
    aroflo_file = st.file_uploader("Aroflo invoicing report", type=["xlsx"])
    verified_file = st.file_uploader("Verified sign-in records", type=["xlsx"])
    lifetime_file = st.file_uploader("Lifetime maintenance spend", type=["xlsx"])

    if all([asset_file, coretex_file, aroflo_file, verified_file, lifetime_file]):
        st.success("All 5 files uploaded")
    else:
        st.info("Upload all 5 files to refresh the dashboard")

with tab1:
    st.subheader("Asset register accuracy")
    col1, col2 = st.columns(2)
    col1.metric("This month", "96%", delta="+1% vs 2yr avg")
    col2.metric("2yr average", "95%")
    dummy_assets = pd.DataFrame({"Status": ["New this month", "Removed this month"], "Count": [8, 0]})
    st.table(dummy_assets)

    st.write("All unit locations")
    import plotly.express as px

    locations = pd.DataFrame({
        "Store": ["Parramatta", "Chatswood", "Newcastle", "Wollongong",
                  "Box Hill", "Geelong", "Bendigo", "Brisbane City",
                  "Cairns", "Toowoomba", "Perth", "Bunbury",
                  "Adelaide", "Mount Gambier", "Hobart", "Launceston",
                  "Canberra", "Darwin", "Alice Springs"],
        "State": ["NSW", "NSW", "NSW", "NSW", "VIC", "VIC", "VIC", "QLD",
                  "QLD", "QLD", "WA", "WA", "SA", "SA", "TAS", "TAS", "ACT", "NT", "NT"],
        "Asset Type": ["Baler", "Baler", "Baler", "Compactor", "Baler", "Baler",
                       "Compactor", "Baler", "Baler", "Baler", "Baler", "Baler",
                       "Compactor", "Baler", "Baler", "Baler", "Baler", "Compactor", "Baler"],
        "lat": [-33.81, -33.80, -32.93, -34.43, -37.82, -38.15, -36.76, -27.47,
                -16.92, -27.56, -31.95, -33.33, -34.93, -37.83, -42.88, -41.43,
                -35.28, -12.46, -23.70],
        "lon": [151.00, 151.18, 151.78, 150.89, 145.12, 144.36, 144.28, 153.03,
                145.77, 151.95, 115.86, 115.64, 138.60, 140.78, 147.33, 147.14,
                149.13, 130.85, 133.88]
    })

    fig = px.scatter_geo(
        locations,
        lat="lat", lon="lon",
        hover_name="Store",
        hover_data={"State": True, "Asset Type": True, "lat": False, "lon": False},
        color="Asset Type",
        scope="world",
    )
    fig.update_geos(
        lataxis_range=[-45, -9],
        lonaxis_range=[108, 156],
        showland=True, landcolor="rgb(235,235,230)",
        showcountries=True,
    )
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=450)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Planned servicing")
    col1, col2 = st.columns(2)
    col1.metric("This month", "92%", delta="-3% vs 2yr avg")
    col2.metric("2yr average", "95%")

    col3, col4 = st.columns(2)
    col3.metric("Completed", "115 stores")
    col4.metric("Outstanding", "9 stores")

    st.write("Outstanding services by state")
    outstanding_state = pd.DataFrame({
        "State": ["NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT"],
        "Outstanding": [3, 2, 1, 1, 1, 1, 0, 0]
    })
    st.bar_chart(outstanding_state.set_index("State"))

    st.write("Where the outstanding stores are")
    map_data = pd.DataFrame({"lat": [-32.73, -36.76], "lon": [151.55, 144.28]})
    st.map(map_data)

with tab3:
    st.subheader("Breakdowns")
    col1, col2 = st.columns(2)
    col1.metric("This month", "14", delta="+21% vs 2yr avg")
    col2.metric("2yr average", "11.6")

    st.write("Breakdowns by state")
    breakdown_state = pd.DataFrame({
        "State": ["NSW", "VIC", "QLD", "WA", "SA", "TAS", "ACT", "NT"],
        "Breakdowns": [4, 3, 2, 2, 1, 1, 0, 1]
    })
    st.bar_chart(breakdown_state.set_index("State"))

    st.write("Where breakdowns happened")
    breakdown_map = pd.DataFrame({"lat": [-33.87, -37.81, -27.47], "lon": [151.21, 144.96, 153.02]})
    st.map(breakdown_map)

with tab4:
    st.subheader("Spend")
    col1, col2 = st.columns(2)
    col1.metric("This month", "$22.3k", delta="+21% vs 2yr avg")
    col2.metric("2yr average", "$17.9k")

    st.write("Monthly spend trend")
    spend_trend = pd.DataFrame({
        "Month": ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "Spend": [16800, 18200, 15900, 19500, 17300, 22300]
    })
    st.line_chart(spend_trend.set_index("Month"))

with tab5:
    st.subheader("Pricing vs contract")
    st.metric("Invoices flagged", "2")
    flagged = pd.DataFrame({
        "Invoice": ["AF-40009", "AF-40713"],
        "Charged": ["$358", "$340"],
        "Expected": ["$408", "$490"]
    })
    st.table(flagged)

with tab6:
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

with tab7:
    st.subheader("Predictive capex - next 12 months")
    col1, col2 = st.columns(2)
    col1.metric("Proactive (planned)", "$184k")
    col2.metric("Reactive (unplanned)", "$96k")

    capex_split = pd.DataFrame({
        "Type": ["Proactive", "Reactive"],
        "Forecast": [184000, 96000]
    })
    st.bar_chart(capex_split.set_index("Type"))
