import pandas as pd
import altair as alt
import streamlit as st
import datetime as dt

@st.cache
def get_zillow_data(type):
    if type == "1 Bedroom":
        path= "data/Neighborhood_Zhvi_1bedroom.csv"
    elif type == "2 Bedrooms":
        path = "data/Neighborhood_Zhvi_2bedroom.csv"
    elif type == "3 Bedrooms":
        path = "data/Neighborhood_Zhvi_3bedroom.csv"
    elif type == "Single Family Homes":
        path = "data/Neighborhood_Zhvi_SingleFamilyResidence.csv"
    elif type == "All Homes (SFR, Condo/Co-op)":
        path = "data/Neighborhood_Zhvi_AllHomes.csv"
    return pd.read_csv(path)

type = st.sidebar.selectbox(
    "Select home type",
    ("1 Bedroom", "2 Bedrooms", "3 Bedrooms", "Single Family Homes", "All Homes (SFR, Condo/Co-op)")
)


# select data
df = get_zillow_data(type)
states_all = sorted(list(pd.unique(df["State"])))
states = st.sidebar.multiselect("Select state", states_all, ["NJ"])
if len(states) == 0:
    states = states_all

cities_all = sorted(list(pd.unique(df.loc[df["State"].isin(states), "City"])))
cities = st.sidebar.multiselect("Select city", cities_all, ["Jersey City"])
if len(cities) == 0:
    cities = cities_all

nbrs_all = sorted(list(pd.unique(df.loc[(df["State"].isin(states)) & (df["City"].isin(cities)), "RegionName"])))
nbrs = st.sidebar.multiselect("Select neighborhood", nbrs_all)
if len(nbrs) == 0:
    nbrs = nbrs_all

df = df.loc[(df["State"].isin(states)) & (df["City"].isin(cities)) & (df["RegionName"].isin(nbrs))]
df.rename({"RegionName": "Neigborhood"}, axis=1, inplace=True)
df = df.drop(["RegionID", "City", "State", "Metro", "CountyName", "SizeRank"], axis=1).set_index("Neigborhood").sort_index()

months = list(df.columns)
start_time = st.sidebar.selectbox("Select start time", months, 0)
end_time = st.sidebar.selectbox("Select end time", months, len(months) - 1)
cols = [col for col in months if col >= start_time and col <= end_time]
df = df[cols]


# time series data
st.title("Zillow Home Value Index\n")
st.header("Time Series Data")
st.write("", df)


# time series plot
st.header("\n\n\nTime Series Plot")
df = pd.melt(df.T.reset_index(), id_vars=["index"], value_vars=nbrs)
df.columns = ["Time", "Neigborhood", "ZHVI"]
chart = (
    alt.Chart(df)
    .mark_area(opacity=0.3)
    .encode(
        x="Time:T",
        y=alt.Y("ZHVI:Q", stack=None),
        color="Neigborhood:N",
    )
)
st.altair_chart(chart, use_container_width=True)
