import pandas as pd
import streamlit as st
import numpy as np
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic

# Apne banaye huye helper functions ko import kar rahe hain
from helper.utils import calucalate_distance,is_open_spot


# CSV files se data load kar rahe hain
df = pd.read_csv("./dubai_spots_clean.csv")
Ps = pd.read_csv("./dubai_areas_labels.csv")

# Streamlit ki basic settings (Title aur Icon)
st.set_page_config(page_title=" Dubai Cold Coffee Finder",page_icon="☕",layout="wide")
st.title("☕ Dubai Cold Coffee Finder")
st.write("Find the nearest cold coffee spots around you in Dubai" )
st.write("Explore cafes, carts, and trucks based on distance, rating, and availability")
st.header("📍 Select Your Area")


# Dropdown menu jahan se user apna area select karega
area_labels= list(Ps["label"])
#area_labels.insert(0,"Select Area")
selected_area=st.selectbox("Choose your area",area_labels)


# Sidebar mein Filters ka setup
with st.sidebar:
  st.header("🔍 Search & Filters")
  spot_name=st.text_input("Search by name",placeholder="e.g : Arctic Brew")
  st.divider()
  st.header("⚙️ Filters")
  options = list(df["type"].unique())
  options.insert(0,"All")
  spot_type=st.selectbox("Spot Type",options)
  max_distance = st.slider("Max Distance (km)", 1, 20, 10)
  min_rating = st.slider("Min Rating ", 1.0, 5.0, 3.0,step=0.1)
  show_only_open = st.checkbox("Show only open spots",False)
  sort_by = st.radio("Sort By", ["Distance", "Rating"])


# User ne jo area select kiya hai, uske coordinates (lat, lng) nikal rahe hain
ss = Ps[Ps["label"] == selected_area][["lat","lng"]]
user_location = tuple(ss.iloc[0])

# Har row ke liye distance nikalne ka function
def get_row(row): 
  return calucalate_distance(user_location,row)

# Category ke hisab se icon (emoji) dikhane ke liye
def get_icon(spot_type):
    icons = {
        "cafe": "🏠",
        "cart": "🛒",
        "truck": "🚚"
    }
    return icons.get(spot_type)




# Dataframe mein distance aur open/closed status ke naye columns jod rahe hain
df["distance_km"] = df.apply(get_row,axis=1)
df["is_open"] = df.apply(is_open_spot,axis=1)


# Stats dikhane ke liye main data ki copy bana rahe hain
df2=df.copy()


# --- Filters Apply Karna ---
if spot_type != "All":
    df = df[df["type"] == spot_type]

df = df[df["distance_km"] <= max_distance]  
df = df[df["rating"]>= min_rating]

if show_only_open:
     df = df[df["is_open"] == "open"]


# Sorting logic: Distance ya Rating ke hisab se
if sort_by =="Distance":
   df = df.sort_values(by="distance_km")
else:
   df = df.sort_values(by="rating",ascending=False)

# Naam se search karne ka filter
if spot_name:
   df = df[df["name"].str.contains(spot_name,case=False)]

   
# Dashboard mein Tabs (Map, Stats, aur Leaderboard) banana
tab1,tab2,tab3 = st.tabs(["🗺️ Nearby Spots", "📊 Analytics", "🏆 Leaderboard"])


with tab1:
  st.subheader(f"{len(df)} spot(s) found")

   # Dubai ka map bana rahe hain user ki location par focus karke
  dubai_map = folium.Map(location=user_location,zoom_start=13)

   # User jahan khada hai wahan Orange marker lagana
  marker_icon = folium.Icon(color="orange",icon="user")
  area_marker = folium.Marker(user_location, 
                              icon=marker_icon,
                              tooltip=f"Area: {selected_area}" )
  area_marker.add_to(dubai_map)


# Har coffee shop ke liye map par marker lagana (Open ke liye Green, Closed ke liye Red)
  for data in df.iterrows():
    
    row = data[1]
    type = row['type']
    name = row['name']
    lat = row['lat']
    lng = row['lng']
    is_open = row["is_open"]
    color = "green"
    if is_open == "closed":
       color="red"
    spot_location = (lat,lng)
    icon = folium.Icon(color=color,icon="coffee",prefix="fa")
    maker = folium.Marker(spot_location,
                          icon=icon,
                          tooltip=f"{type.capitalize()}: {name}")
    maker.add_to(dubai_map)
  st_folium(dubai_map,height=300,use_container_width=True)


 # Coffee shops ko cards ke roop mein dikhana (ek line mein 2 cards)
  for i in range(0,len(df),2):
     small_df = df.iloc[i:i+2]
     columns = st.columns(2)
     for j in range(0,len(small_df)):
        with columns[j]:
           with st.container(border=True):
              row = small_df.iloc[j]

              if row["is_open"] == "open":
                   status = "🟢 Open"
              else:
                  status = "🔴 Closed"

              icon = get_icon(row["type"])

              st.subheader(f"{icon} {row['name']}")
              col1,col2 = st.columns(2)
              with col1:
                  st.markdown(f"**Type**:{row['type']}")
                  st.markdown(f"**Distance**: {row['distance_km']} km")

              with col2:
                 rating = row["rating"]
                 st.markdown(f"**status**: {status}")
                 st.markdown(f"**rating**: {'⭐'*int(rating)}({rating})")
              st.caption(f"🕐 {row['opening_time']} - {row['closing_time']}")
  

  #st.dataframe(df)


with tab2:
    # Project ke stats aur charts dikhana
    st.header("📈 Summary Stats")
   
    total_spots = len(df2)
    avg_rating=round(df2["rating"].mean(),2)
    open_now=len(df2[df2["is_open"]=="open"])
    sort_data=df2.sort_values(by="distance_km")
    min_dis=sort_data["distance_km"].iloc[0]
   
    c1,c2,c3,c4= st.columns(4)
    c1.metric("Total Spots",total_spots)
    c2.metric("Avg Rating",avg_rating)
    c3.metric("Open Now",f"{open_now}/{len(df2)}")
    c4.metric("Nearest Spot",f"{min_dis}{" km"}")

    st.divider()

    st.subheader("🏷️ Spots by Type")
    spot_counts=df2["type"].value_counts()
    st.bar_chart(spot_counts)

    st.divider()

    st.subheader("⭐ Average Rating by Type")
    avg_type = df2.groupby("type")["rating"].mean()
    st.bar_chart(avg_type,color="#2E8E7F")



with tab3:
  # Top 10 lists (Best Rated aur Sabse Paas)
  st.subheader( "🏆 Top 10 Rated Spots")

  st.divider()

  top = df2.sort_values(by="rating",ascending=False).head(10).reset_index(drop=True)
  top.index=top.index +1
  st.dataframe(top[["name","type","rating","distance_km"]])

  st.divider()

  st.subheader("📍 Nearest 10 Spots to You")
  spot = df2.sort_values(by="distance_km",ascending=True).head(10).reset_index(drop=True)
  spot.index= spot.index+1
  st.dataframe(spot[["name","type","rating","distance_km"]])


 