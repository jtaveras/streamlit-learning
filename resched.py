
# import siuba
# from siuba import _, group_by, summarize
# Testing 


st.set_page_config(page_title = "Dashboard") #, layout = "wide")
# {
#     page_title = "Dashboard",
# page_icon = "Active",
# layout = "wide",
# }


# Title of the app
st.title("Cancellation Tracker")



# Or even better, call Streamlit functions inside a "with" block:
# with right_column:
#     chosen = st.radio(
#         'Sorting hat',
#         ("Gryffindor", "Ravenclaw", "Hufflepuff", "Slytherin"))
#     st.write(f"You are in {chosen} house!")


# File uploader
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
# uploaded_file = "/Users/johntaveras/Downloads/cancel_dash_data.csv"
df = pd.read_csv(uploaded_file)


if df is not None:
    # Read the CSV file into a DataFrame
    
    
    # df["resched_created"] = [0 if df["orig_id"].isnull() else 1]
    df['resched_created'] = np.where(df['orig_id'].isnull(), 0, 1)
    df["resched_booked"] = np.where(df["resched_was_booked"] == True, 1,0)
    df["resched_visited"] = np.where(df["resched_was_visited"] == True, 1,0)

    # df["date1"] = pd.to_datetime(df["min_closed_date"][0:10])
    df['date'] = pd.to_datetime(df['min_closed_date'].str.slice(0,10))
    df['week'] = df['date'] - pd.to_timedelta(df['date'].dt.weekday, unit='d')
    df['week_str'] = df['week'].astype(str)
    df["is_last_minute"] = np.where(df["reason_for_loss_category"].isin(["Cancelled - DAY OF","Cancelled - PATIENT NO-SHOW"]), 1, 0)
    


    filter_left, filter_right = st.columns(2)

    select_partner = filter_left.selectbox(
            'Partner',
            ['All Partners'] + df['owner_partner_name'].unique().tolist())
            # [df['owner_partner_name'].unique()].extend("All Partners"))
            # ["All Partners"].extend(df['owner_partner_name'].unique()))
            # ["All Partners"] + [df['owner_partner_name'].unique().tolist()])


    # filter_left.file_uploader("Upload a CSV file", type=["csv"])
    with filter_right:
        # dates = st.select_slider("Dates", )
        select_date_from = st.date_input("From", value = df['week'].max() - timedelta(days=70), min_value = df['week'].min(), max_value = df['week'].max())
        select_date_to = st.date_input("To", min_value = df['week'].min(), max_value = df['week'].max())




    # select_date_from = select_date_from - pd.to_timedelta(select_date_from.dt.weekday, unit='d')
    # select_date_to = select_date_from - pd.to_timedelta(select_date_to.dt.weekday, unit='d')


    df = df[select_date_from <= df["week"].dt.date] # <= select_date_to]
    if select_partner != "All Partners":
        df = df[df["owner_partner_name"] == select_partner]






    summary_data = pd.DataFrame(
        df.groupby(["week_str"]).agg(
            n_cancelled =("cancelled_id", 'count'),
            pct_created =('resched_created', 'mean'),
            n_created = ('resched_created', 'sum'),
            n_resched_booked =('resched_booked', 'sum'),
            # pct_resched_booked = ('resched_booked', 'sum') / ('resched_created', 'sum'),
            # pct_resched_booked = ('resched_booked', 'mean'),
            # n_visited = ("resched_visited", 'sum'),
            # pct_resched_visited = ("resched_visited", 'mean')
        )
    )
    summary_data["week_str"] = summary_data.index
    # summary_data["week"] = summary_data["week"].astype(str)

    summary_data["pct_resched_booked"] = summary_data["n_resched_booked"] / summary_data["n_created"]
    summary_data["pct_booked_of_cancelled"] = summary_data["n_resched_booked"] / summary_data["n_cancelled"]


    tab1, tab2 = st.tabs(["Chart", "Data"])

    with tab1:
        tab1_1, tab1_2 = st.columns(2)

        tab1_1.write("###### " + select_partner)
        tab1_1.line_chart(summary_data[['pct_created',"pct_resched_booked","pct_booked_of_cancelled"]],
                      x_label = "Cancellation Week", )

        tab1_2.write("###### "+select_partner + " - Number of Cancelled Visits")
        summary_data.set_index("week_str")
        tab1_2.bar_chart(summary_data[["week_str","n_cancelled"]], x = "week_str")

    with tab2:
        # st.header("Data")
        st.write(summary_data)
        st.image("https://static.streamlit.io/examples/owl.jpg", width=200)


    st.divider()
    

    last_minute = df.groupby(["is_last_minute"]).agg(
            n_cancelled =("cancelled_id", 'count'),
            pct_created =('resched_created', 'mean'),
            n_created = ('resched_created', 'sum'),
            n_resched_booked =('resched_booked', 'sum'),
            # pct_resched_booked = ('resched_booked', 'sum') / ('resched_created', 'sum'),
            # pct_resched_booked = ('resched_booked', 'mean'),
            # n_visited = ("resched_visited", 'sum'),
            # pct_resched_visited = ("resched_visited", 'mean')
        )
    last_minute["is_last_minute"] = last_minute.index

    st.header("Last-Minute Cancellations")

    kpi1, kpi2, kpi3 = st.columns(3)

    kpi1.metric("# of Last-Minute Cancels", '{:,}'.format(last_minute.loc[1]["n_cancelled"]), border = True)
    kpi2.metric("% Cancelled Last-Minute", '{:.1%}'.format(last_minute.loc[1]["n_cancelled"] / last_minute["n_cancelled"].sum()), border = True)
    kpi3.metric("% Resched Created", '{:.1%}'.format(last_minute.loc[1]["pct_created"]), border = True)


    last_minute = duckdb.sql("SELECT week_str, \
                             COUNT(CASE WHEN is_last_minute = 1 THEN 1 END) as num_last_minute,\
                             COUNT(CASE WHEN is_last_minute = 0 THEN 1 END) as num_not_last_minute, \
                             COUNT(CASE WHEN is_last_minute = 1 THEN 1 END) / COUNT(1) as pct_last_minute,\
                             AVG(CASE WHEN is_last_minute = 1 THEN resched_created END) as pct_resched_created \
                             FROM df \
                             GROUP BY 1 ORDER BY 1").df()
    
    lastmin_tab1, lastmin_tab2 = st.tabs(["Chart", "Data"])

    with lastmin_tab1:
        lastmin_tab1_1, lastmin_tab1_2 = st.columns(2)

        lastmin_tab1_1.write("###### "+select_partner)
        lastmin_tab1_1.line_chart(last_minute[["pct_last_minute", "pct_resched_created"]],
                      x_label = "Cancellation Week", )

        lastmin_tab1_2.write("###### "+select_partner + " - Number of Last-Minute Cancelled Visits")
        summary_data.set_index("week_str")
        lastmin_tab1_2.bar_chart(last_minute[["week_str","num_last_minute", "num_not_last_minute"]], x = "week_str", stack = True)

    with lastmin_tab2:
        # st.header("Data")
        st.write(last_minute)






    # last_minute_ts = (
    #     df >>
    #     group_by("week") >>
    #     summarize(num_lm_cancelled = ())
    # )
    
    # df.groupby(["week"]).agg(
    #     num_lm_cancelled = 
    # )
    # st.write(last_minute.head())

    st.divider()

    # Basic Data Processing
    st.subheader("Summary")
    select_summary_dim = st.selectbox('Dimension',
            ("reason_for_loss_category","cancelled_by"),)
    summary = duckdb.sql("SELECT " + select_summary_dim + ", \
                         COUNT(1) as num_cancels, \
                         SUM(resched_created) as rescheds_created, \
                         SUM(resched_booked) as rescheds_booked,\
                         SUM(resched_visited) as rescheds_visited,\
                         AVG(resched_created) as pct_resched_created,\
                         AVG(resched_booked) as pct_resched_booked,\
                         AVG(resched_visited) as pct_resched_visited\
                         FROM df \
                         GROUP BY 1 ORDER BY 2 DESC").df()
    
    st.write(summary)



    st.divider()
    st.write(df.head())


else:
    st.write("Please upload a CSV file to get started.")
