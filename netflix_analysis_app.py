import streamlit as st
import pandas as pd
from zipfile import ZipFile
import plotly.express as px
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
from PIL import Image


# APP UI MODULES
##########################################################################################

#title
st.title('Netflix Analysis GDPR')  #Title of the webapp

#tmdb logo 
tmdb_logo = Image.open('tmdb_logo.jpeg')
st.image(tmdb_logo, caption='Powered by')

#text
st.markdown('Every online service that you use will store a surprising amount of data about you. \
 This is my hobby project to make your personal data on the internet truly accessible to you!\
Netflix is one of the companies who give you easy access to your own data. You can download your own data here: **_netflix.com/youraccount_**')

st.markdown('This Project is work in progress. Next goals are to integrate it with The Movie DB to get more exiting insights such as favorite movie genres and movie ratings.\
    If you have any suggestions on what to add to the analysis or want to talk about this project, feel free to reach out to me on **_linkedin.com/in/sebastian-ten-berge/_**')

## !!! next goal is to create option to upload own netflix file. 

interaction_df = pd.read_csv('Files/ViewingActivity.csv')
df_billing = pd.read_csv('Files/BillingHistory.csv')
# IP Adress locations - where movies were watched
streaming_locations_df = pd.read_csv('Files/IpAddressesStreaming.csv')

# Sidebar 
##########################################################################################

# create file import botton
uploaded_file = st.sidebar.file_uploader("upload file", type="zip")

st.sidebar.markdown('**What happens to my netflix data if I upload it?** :thinking_face:')
st.sidebar.markdown('In short, files are stored in memory, they get deleted immediately as soon as they’re not needed anymore. \
        You can find more on streamlits own documentation:\
         [where-file-uploader-store-when-deleted](https://docs.streamlit.io/knowledge-base/using-streamlit/where-file-uploader-store-when-deleted)', unsafe_allow_html=False )


# Data import processing
##########################################################################################

# analyse zip file
if uploaded_file is not None:
    with ZipFile(uploaded_file, 'r') as zip:
        zip.extractall()
        # # creates df from upload
        interaction_df = pd.read_csv('./CONTENT_INTERACTION/ViewingActivity.csv')
        df_billing = pd.read_csv('./PAYMENT_AND_BILLING/BillingHistory.csv')
        # # IP Adress locations - where movies were watched
        streaming_locations_df = pd.read_csv('./IP_ADDRESSES/IpAddressesStreaming.csv')

# ISO Codes converter
iso_df =pd.read_csv('Files/iso_codes.csv', header=None, names=['Country', 'iso_2', 'iso_3', 'UN_Code'])

# adding all dataframes into a list
alldfs = [interaction_df, streaming_locations_df]
#add replace all spaces in column titles with underscore
for column_titles in (alldfs):
    column_titles.columns = column_titles.columns.str.replace(' ', '_')


### Removing all none movie or serie titles
watched_df = interaction_df[interaction_df['Supplemental_Video_Type'].isnull()]
### Removing all unwanted autoplays by filtering out all where Duration watched is less than 1 minute 30 seconds
watched_df = watched_df[(watched_df['Duration'] > '00:01:00')]

### calculating total amount billed
costs = df_billing.loc[(df_billing['Pmt Status'] == 'APPROVED') & (df_billing['Final Invoice Result'] == 'SETTLED'), "Gross Sale Amt"].sum()
currency = df_billing['Currency'].iloc[0:1, ]

# Basic Statistic on data
##########################################################################################
#viewing_statistics = [(interaction_df.Title.nunique(), interaction_df.Device_Type.nunique(), interaction_df.Country.nunique())]
#df_viewing_statistics = pd.DataFrame(viewing_statistics, columns=['Titles', 'Devices', 'Country']).reset_index(drop=True)
col1, col2, col3, col4 = st.columns(4)
col1.metric('Titles Watched', watched_df.Title.nunique())
col2.metric('Unique Devices', watched_df.Device_Type.nunique())
col3.metric('Countries Logged in from', watched_df.Country.nunique())
col4.metric('Paid for Netflix', (list(currency)[0] + " " + str(np.round_(costs.astype(int), decimals=0))))



# Duration watched Netflix

##########################################################################################

watched_df['watched_minutes'] = watched_df['Duration'].str.split(':').apply(lambda x: int(x[0]) * 60 + int(x[1]))
watched_df['duration_minutes'] = watched_df['Bookmark'].str.split(':').apply(lambda x: int(x[0]) * 60 + int(x[1]))
watched_df['watched_hours'] = watched_df['watched_minutes'] / 60
watched_df['percent_watched'] = watched_df['watched_minutes'] / watched_df['duration_minutes'] *100
watched_df['percent_watched2'] = 5 * round(watched_df['percent_watched']/5)
total_watchtime_df =  watched_df.groupby(['Profile_Name'],as_index=False).sum().sort_values('watched_hours')

fig3 = px.bar(total_watchtime_df, x= 'Profile_Name',  y="watched_hours",
             color="watched_hours",
             color_continuous_scale=["rgb(1,1,1)", "rgb(86,77,77)", "rgb(131,16,16)", "rgb(219,0,0)"],
             title="Hours Spent Watching Netflix")
st.plotly_chart(fig3, use_container_width=True)


# defining movie and series
#########################################################################################
watched_df["Show_Title"] = [s.partition(":")[0] for s in watched_df.Title]

# filtering out seasons with the word Säsong, season, series, serie
watched_df["temporary_brackets_removed_title"] = watched_df['Title'].str.replace('(', '')
watched_df["Film_Type"] = np.where(watched_df.temporary_brackets_removed_title.astype(str).str.contains(pat = 'Season | Säsong | Series | Serie | Episode | Episod | Avsnitt', case = False), 'Series', 'Movie')
watched_df = watched_df.drop('temporary_brackets_removed_title', 1)

# Users Multi Select Button
##########################################################################################

users = watched_df.Profile_Name.unique()

user_radio_button_1 = st.sidebar.multiselect("Netflix Account", users, users)

# Most watched Movies
##########################################################################################

film_type = ['Movie', 'Series']

film_type_radio_button_1 = st.radio("Movies or Series", film_type)

if film_type_radio_button_1 == 'Movie':
    df_Movies_watched_cleaned_1 = watched_df[(watched_df["Film_Type"] == 'Movie') & (watched_df["percent_watched2"] > 85)]
    df_Movies_watched_frequency = df_Movies_watched_cleaned_1[['Profile_Name', 'Title', 'Film_Type']].groupby(['Profile_Name', 'Title'])['Film_Type'].count().reset_index()
    df_Movies_watched_frequency.rename(columns = {'Film_Type':'Count'}, inplace = True)
    df_Movies_watched_frequency = df_Movies_watched_frequency.sort_values('Count', ascending=False)
    fig5 = px.bar(df_Movies_watched_frequency[df_Movies_watched_frequency['Profile_Name'].isin(user_radio_button_1)].head(10),
                         x='Title',
                         y = 'Count', 
                         color = 'Profile_Name',
                         color_discrete_sequence=["rgb(1,1,1)", "rgb(219,0,0)", "rgb(86,77,77)", "rgb(131,16,16)"],
                         title="Movies"
                         )
    fig5.update_layout(xaxis={'categoryorder':'total descending'})
    st.plotly_chart(fig5, use_container_width=True)

# Most watched Series
##########################################################################################
if film_type_radio_button_1 == 'Series':
    df_series_watched_cleaned_1 = watched_df[(watched_df["Film_Type"] == 'Series') & (watched_df["percent_watched2"] > 85)]
    df_series_watched_frequency = df_series_watched_cleaned_1[['Profile_Name', 'Show_Title', 'Film_Type']].groupby(['Profile_Name', 'Show_Title'])['Film_Type'].count().reset_index().sort_values('Film_Type', ascending=False)
    df_series_watched_frequency.rename(columns = {'Film_Type':'Count'}, inplace = True)
    fig6 = px.bar(df_series_watched_frequency[df_series_watched_frequency['Profile_Name'].isin(user_radio_button_1)].head(10), 
                        x='Show_Title', 
                        y = 'Count', 
                        color = 'Profile_Name',
                        color_discrete_sequence=["rgb(1,1,1)", "rgb(219,0,0)", "rgb(86,77,77)", "rgb(131,16,16)"],
                        title="Series")
    fig6.update_layout(xaxis={'categoryorder':'total descending'})
    st.plotly_chart(fig6, use_container_width=True)


# Viewing geo location
##########################################################################################


streaming_country_df = watched_df[watched_df['Profile_Name'].isin(user_radio_button_1)].groupby(by='Country', as_index=False).agg({'Start_Time': pd.Series.nunique})
streaming_country_df['Country'] = streaming_country_df['Country'].astype(str).str[0:2]
streaming_country_df = streaming_country_df.merge(iso_df,how='inner',left_on=['Country'],right_on=['iso_2'])


fig = px.choropleth(streaming_country_df,                            # Input Dataframe
                         locations='iso_3',           # identify country code column
                         color= 'Start_Time',                     # identify representing column
                         color_continuous_scale=["rgb(1,1,1)", "rgb(86,77,77)", "rgb(131,16,16)", "rgb(219,0,0)"],
                         hover_name= 'Country_y',              # identify hover name
                         projection= 'natural earth',        # select projection
                         range_color=[0,streaming_country_df['Start_Time'].max()],
                         labels={'Start_Time':'Hours Series/Movies Watched'},
                         title= 'Countries viewed from')
st.plotly_chart(fig)
fig.write_html("example_map.html")


# Devices Used to Watch Netflix

##########################################################################################

word_count_device = watched_df[watched_df['Profile_Name'].isin(user_radio_button_1)].Device_Type.str.split(expand=True).stack().value_counts()
df_word_count_device = word_count_device.to_frame()
df_word_count_device.reset_index(inplace=True)
df_word_count_device = df_word_count_device.rename(columns = {'index':'sub_device', 0:'Count'})

devices = ['tv', 'phone', 'ipad', 'tablet', 'pc', 'mac', 'vr', 'iphone', 'chromecast'] 

# selecting rows based on condition 
df_devices_count = df_word_count_device[df_word_count_device['sub_device'].str.lower().isin(devices)] 

device_and_categories = {'TV': 'TV','iPad': 'Tablet', 'PC': 'PC', 'Chromecast': 'TV', 
                        'MAC': 'PC', 'iPhone': 'Phone', 'Tablet': 'Tablet', 'Phone':'Phone', 'VR': 'VR'}

df_devices_count['Device'] = df_devices_count['sub_device'].map(device_and_categories)
df_devices_count.reset_index(drop=True, inplace=True)
df_devices_count = df_devices_count.drop(['sub_device'], axis = 1)

df_devices_count = df_devices_count.groupby(['Device']).sum(['Count']).reset_index().sort_values(['Count'])

fig4 = px.bar(df_devices_count, x= 'Device',  y="Count",
             title="Most Popular Device to Watch from",
             color='Count',
             color_continuous_scale=["rgb(1,1,1)", "rgb(86,77,77)", "rgb(131,16,16)", "rgb(219,0,0)"])
st.plotly_chart(fig4, use_container_width=True)



# Most Common Times to Watch Netflix

##########################################################################################

## preparing the data for the heatmap

#filtering for only messages sent by myself
weekday_df = watched_df

#transformting the date type to 'datetime'
weekday_df['Date'] = pd.to_datetime(watched_df['Start_Time'])

#selecting only the needed columns
weekday_df = weekday_df[['Date', 'Profile_Name', 'Start_Time']]

#creating the day of the week column 'Weekday'
weekday_df['Weekday'] = weekday_df['Date'].dt.day_name()
weekday_hour_df = weekday_df

#creating the hour of the week column 'Hour'
weekday_hour_df['Hour'] = weekday_hour_df['Date'].dt.hour

#count the messages per day and hour
heatmap_total_df = weekday_hour_df.groupby(['Weekday', 'Hour', 'Profile_Name']).size().reset_index(name='Counts')

weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
heatmap_total_df['Weekday'] = pd.Categorical(heatmap_total_df['Weekday'], weekdays)  # set a fixed order
heatmap_df = heatmap_total_df.pivot_table(values='Counts', index=['Hour', 'Profile_Name'], columns=['Weekday'])

## Visualizing the heatmap

users2 = heatmap_df.index.get_level_values('Profile_Name').unique()

user_radio_button_2 = st.radio("Netflix Account", users2)


fig2, ax = plt.subplots(figsize=(15, 10))
black_red = LinearSegmentedColormap.from_list('black_red', ['white', 'darkgrey', 'darkred', 'red'])
sns.heatmap(heatmap_df[heatmap_df.index.get_level_values('Profile_Name').isin([user_radio_button_2])].droplevel(1, axis=0),
            annot=True, fmt='g', cmap=black_red, ax=ax)
ax.set_title(user_radio_button_2 + "'s" + " Netflix Log in Times", fontsize=20)
ax.set_xlabel('Weekday', fontsize=15)  
ax.set_ylabel('Time', fontsize=15) 
# ax.set_yticklabels(range(0,24), rotation=0)
st.pyplot(fig2)

