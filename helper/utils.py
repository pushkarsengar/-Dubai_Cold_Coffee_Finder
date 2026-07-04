from geopy.distance import geodesic
from datetime import datetime

def  calucalate_distance(user_location,row):
    lat = row['lat']
    lng = row['lng']
    spot_location=lat,lng
    dis = geodesic(user_location,spot_location).km
    return round(dis,2)

def is_open_spot(row):
    
        now = datetime.now().strftime("%H:%M")

        open_t = row["opening_time"]
        close_t = row["closing_time"]

        
        if open_t <= now <= close_t :
              return"open"
        
        else:
            return "closed"