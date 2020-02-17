import pandas as pd
import altair as alt
import streamlit as st
from mortgage import Loan


app = st.sidebar.selectbox(
    "Select app",
    ("Market Dashboard", "Payment Dashboard")
)



if app == "Market Dashboard":
    st.title("Market Dashboard\n")


    @st.cache
    def get_data(type, source):
        if source == "Local":
            root = "data/"
        elif source == "Online":
            root = "http://files.zillowstatic.com/research/public/Neighborhood/"
        if type == "1 Bedroom":        
            buy_path = "Neighborhood_Zhvi_1bedroom.csv"
            rent_path = "Neighborhood_MedianRentalPrice_1Bedroom.csv"
        elif type == "2 Bedrooms":
            buy_path = "Neighborhood_Zhvi_2bedroom.csv"
            rent_path = "Neighborhood_MedianRentalPrice_2Bedroom.csv"
        elif type == "3 Bedrooms":
            buy_path = "Neighborhood_Zhvi_3bedroom.csv"
            rent_path = "Neighborhood_MedianRentalPrice_3Bedroom.csv"
            path = "Neighborhood_Zhvi_3bedroom.csv"
        elif type == "Single Family Homes":
            buy_path = "Neighborhood_Zhvi_SingleFamilyResidence.csv"
            rent_path = "Neighborhood_MedianRentalPrice_Sfr.csv"
        buy_path = root + buy_path
        rent_path = root + rent_path
        return pd.read_csv(buy_path), pd.read_csv(rent_path)
    source = st.sidebar.selectbox("Select data source", ("Local", "Online"))
    type = st.sidebar.selectbox("Select home type", ("1 Bedroom", "2 Bedrooms", "3 Bedrooms", "Single Family Homes"))
    df_buy, df_rent = get_data(type, source)

    
    states_all = sorted(list(pd.unique(df_buy["State"])))
    states = st.sidebar.multiselect("Select state", states_all, ["NJ"])
    if len(states) == 0:
        states = states_all
    cities_all = sorted(list(pd.unique(df_buy.loc[df_buy["State"].isin(states), "City"])))
    cities = st.sidebar.multiselect("Select city", cities_all, [cities_all[0]])
    if len(cities) == 0:
        cities = cities_all
    nbrs_all = sorted(list(pd.unique(df_buy.loc[(df_buy["State"].isin(states)) & (df_buy["City"].isin(cities)), "RegionName"])))
    nbrs = st.sidebar.multiselect("Select neighborhood", nbrs_all, nbrs_all)
    if len(nbrs) == 0:
        nbrs = nbrs_all
    months = list(df_buy.columns[7:])
    start_time = st.sidebar.selectbox("Select start time", months, 0)
    end_time = st.sidebar.selectbox("Select end time", months, len(months) - 1)   

    
    @st.cache
    def transform_data(df, states, cities, nbrs, start_time, end_time):
        df = df.loc[(df["State"].isin(states)) & (df["City"].isin(cities)) & (df["RegionName"].isin(nbrs))]
        df.rename({"RegionName": "Neigborhood"}, axis=1, inplace=True)
        df = df.drop([col for col in ["RegionID", "City", "State", "Metro", "CountyName", "SizeRank"] if col in df.columns], axis=1).set_index("Neigborhood").sort_index()
        cols = [col for col in df.columns if col >= start_time and col <= end_time]
        df = df[cols]
        return df.round(0)

    def plot_data(df, index_name, nbrs):
        df = df.T.reset_index()
        df = pd.melt(df, id_vars=["index"], value_vars=df.columns[1:])
        df.columns = ["Time", "Neigborhood", index_name]
        chart = (
            alt.Chart(df)
            .mark_area(opacity=0.3)
            .encode(
                x="Time:T",
                y=alt.Y("{}:Q".format(index_name), stack=None),
                color="Neigborhood:N",
            )
            #.properties(
            #    width=600,
            #    height=400
            #)
        )
        st.altair_chart(chart, use_container_width=True)


    # home value index
    st.header("Zillow Home Value Index\n")
    df_buy = transform_data(df_buy, states, cities, nbrs, start_time, end_time)
    if len(df_buy) == 0:
        st.text("Empty data for selected neighborhoods.")
    else:
        st.dataframe(df_buy)    
        st.header("\n")
        plot_data(df_buy, "Zillow Home Value Index", nbrs)


    # median rent list price
    st.header("Zillow Median Rent List Price\n")
    df_rent = transform_data(df_rent, states, cities, nbrs, start_time, end_time)
    if len(df_rent) == 0:
        st.text("Empty data for selected neighborhoods.")
    else:
        st.dataframe(df_rent)    
        st.header("\n")
        plot_data(df_rent, "Zillow Median Rent List Price", nbrs)


elif app == "Payment Dashboard":
    st.title("Payment Dashboard\n")


    st.header("Monthly Payment Summary\n")    
    price = st.sidebar.number_input("Your purchase price ($)", value=800000)
    other = st.sidebar.number_input("Your other one-time expense (mansion tax, attorney fee, etc.) ($)", value=0)
    downpay = st.sidebar.number_input("Your down payment ($)", value=200000)    
    rate = st.sidebar.number_input("Your loan rate (%)", value=3.25)
    term = int(st.sidebar.number_input("Your loan term (y)", value=30))
    hoa_monthly = st.sidebar.number_input("Your monthly HOA ($)", value=500)
    tax_monthly = st.sidebar.number_input("Your monthly property tax ($)", value=1000)
    other_monthly = st.sidebar.number_input("Your other monthly expense (home insurance, etc.) ($)", value=0)
    loan = price + other - downpay
    loan_monthly = int(Loan(principal=loan, interest=rate / 100, term=term).monthly_payment)    
    total_monthly = loan_monthly + tax_monthly + hoa_monthly + other_monthly
    df_pay = pd.DataFrame({"Payment": [loan_monthly, tax_monthly, hoa_monthly, other_monthly, total_monthly]}, 
        index=["Loan", "Tax", "HOA", "Other", "Total"])
    st.write(df_pay)

    
    st.header("Monthly Payment Explained\n")        
    st.subheader("Remaining Principal Balance")    
    rent_monthly = st.number_input("Your current rent price ($)", value=4000)
    rent_growth_rate = st.number_input("Your yearly rent growth rate (%)", value=2.00)
    resell_cost_rate = st.number_input("Your resell cost rate (%)", value=6.00)
    end_principal = loan
    df_principal = []
    df_pay_detailed = []
    for i in list(range(1, term * 12 + 1)):
        month = i
        start_principal = end_principal
        interest_monthly = start_principal * rate / 1200
        principal_monthly = loan_monthly - interest_monthly
        end_principal = start_principal - principal_monthly
        if (i - 1) % 12 == 0 and i > 1:
            rent_monthly *= (1 + rent_growth_rate / 100)
        df_principal.append([month, start_principal, end_principal])
        df_pay_detailed.append([month, tax_monthly, hoa_monthly, other_monthly, tax_monthly + hoa_monthly + other_monthly, interest_monthly, tax_monthly + hoa_monthly + other_monthly + interest_monthly, principal_monthly, total_monthly, rent_monthly])
    df_principal = pd.DataFrame(df_principal, columns=["Month", "Starting Balance", "Ending Balance"]).set_index("Month").round(0).T
    df_pay_detailed = pd.DataFrame(df_pay_detailed, columns=["Month", "Tax", "HOA", "Other", "Carry", "Interest", "Interest & Carry", "Principal", "Total", "Rent"]).set_index("Month").round(0).T
    df_pay_cum = df_pay_detailed.cumsum(axis=1)    
    st.dataframe(df_principal)
    

    st.subheader("Monthly Payment")
    st.dataframe(df_pay_detailed)
    

    st.subheader("Cumulative Monthly Payment")
    st.dataframe(df_pay_cum)


    st.subheader("Buy or Rent")
    hold_breakeven_point = 1
    resell_cost = price * resell_cost_rate / 100 
    for i in range(df_pay_cum.shape[1]):
        if i == 0 and df_pay_cum.loc["Interest & Carry", i + 1] <= df_pay_cum.loc["Rent", i + 1]:
            break
        if (i == df_pay_cum.shape[1] - 1) or (df_pay_cum.loc["Interest & Carry", i + 1] > df_pay_cum.loc["Rent", i + 1] and df_pay_cum.loc["Interest & Carry", i + 2] <= df_pay_cum.loc["Rent", i + 2]):
            hold_breakeven_point = i + 1
            break
    for i in range(df_pay_cum.shape[1]):
        if i == df_pay_cum.shape[1] - 1 or (df_pay_cum.loc["Interest & Carry", i + 1] + resell_cost > df_pay_cum.loc["Rent", i + 1] and df_pay_cum.loc["Interest & Carry", i + 2]  + resell_cost <= df_pay_cum.loc["Rent", i + 2]):
            resell_breakeven_point = i + 1
            break    
    msg = ""
    if hold_breakeven_point <= df_pay_cum.shape[1]:
        msg += "* You cumulative rent cost will exceed interest & carry cost in *{}* month(s)\n".format(hold_breakeven_point)
    else:
        msg += "* You cumulative rent cost won't exceed interest & carry cost in {} year(s)\n.".format(term)
    if resell_breakeven_point < df_pay_cum.shape[1]:
        msg += "* You cumulative rent cost will exceed interest & carry cost plus {}% resell cost in *{}* month(s).\n".format(resell_cost_rate, resell_breakeven_point)
    else:
        msg += "* You cumulative rent cost will not exceed interest & carry cost plus {}% resell cost in {} years.\n\n".format(resell_cost_rate, term)
    msg += "\n **Note**: Both assume your house value stays the same as the purchase price over time."
    st.markdown(msg)