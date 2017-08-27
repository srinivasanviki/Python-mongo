from bson.objectid import ObjectId
user_profile={
    "u_id":"181CC3724DE5E6AC535C5559EB31BB64",
    "details":{
        "profile_name":"viki",
        "travel_style":"Beach Goer,Family Holiday Maker",
        "from":"From Helensburgh, United Kingdom",
        "helpful":24,
        "total_cities_visited":12,
        "level":2,
        "contributions":50,
        "Since": 15,
        "cities":["Sentosa Island"]
    },
    "similarity":{
        "UID":[],
        "sim_score":[],
        "credibility_score":0
    },
    "reviews":["Very nice place and awesome bars near USS"]
}

from mongodb.operations import operations
import json
from tabulate import tabulate
mongo_client=operations()
db=mongo_client.create_database("user_profiling")

def get_profile(user_profile):
    user_profiles=[profile for profile in  mongo_client.get_all_collections(db,"Users")]
    user_profiles.append(user_profile)
    return json.dumps(user_profile)

def insert_dummy_profile(user_profile):
    user_profiles=json.loads(get_profile(user_profile))
    try:
        id=mongo_client.insert(db,user_profiles,"Users")
    except Exception as e:
        print(e)

def sort_dict_by_value(dict):
        import operator
        sorted_x = sorted(dict.items(), key=operator.itemgetter(1),reverse=True)
        return sorted_x

def get_top_users():
    users=mongo_client.get_all_collections(db,"Users")
    profile={}
    for user in users:
        profile[user.get("u_id")]=user.get("similarity").get("credibility_score")
    top_profiles=sort_dict_by_value(profile)
    range=int(0.15*(len(top_profiles)))
    return top_profiles[0:range]

def count(top_profiles):
    places_visited=[]
    for profile in top_profiles:
        for key,values in profile.iteritems():
            for value in values:
                places_visited.append(value)
    places=remove_duplicates(places_visited)
    place_count={}
    sorted_places={}
    for place in places:
        count=0
        for profile in top_profiles:
            for key,values in profile.iteritems():
                if place in values:
                   count=count+1
        if count >5:
           if place.strip() !="Universal Studios Singapore":
              place_count[place]=count
    sorted_place=sort_dict_by_value(place_count)
    return sorted_place



def remove_duplicates(list):
        newlist=[]
        for l in list:
            if l not in newlist:
                newlist.append(l)
        return newlist

def group_by_location():
    reviews =mongo_client.get_all_collections(db,"Reviews")
    top_users=get_top_users()
    top_profiles=[]
    for review in reviews:
        for user in top_users:
            if review.get("u_id")==user[0]:
                places_visited=[]
                for detail in review.get("details"):
                    places_visited.append(detail.get("place"))
                top_profiles.append({user[0]:places_visited})
    return count(top_profiles)

def get_top_user_reviews():
    user=mongo_client.get_collection(db,"Users_Output",{"u_id":"782998D5E1D36246E1D716B1CA024285"})
    reviews=[]
    top_reviews=user.get("Top_Reviews")
    reviews.append({
        user.get("u_id"):{
        "Place":user.get("Place"),
        "reviews":top_reviews}})
    return reviews

def draw_table(top_profile_reviews):
    import plotly.plotly as py
    import plotly.figure_factory as ff
    clust_data =[]
    for review in top_profile_reviews:
        for u_id,values in review.iteritems():
             reviews=values.get("reviews")
             place=values.get("Place")
             for category,review_text in reviews.iteritems():
                 if category=="Attractions":
                    attraction_reviews=",".join(review_text)
                 elif category=="Restaurant":
                     restaurant_reviews=",".join(review_text)
                 else:
                     hotel_reviews=",".join(review_text)
             if attraction_reviews and restaurant_reviews and hotel_reviews:
                clust_data.append([u_id,place,truncate_string(attraction_reviews),truncate_string(restaurant_reviews),truncate_string(hotel_reviews)])

    print(tabulate(clust_data,headers=["Users","Place","Atrraction", "Restaurant", "Hotels"]))

def truncate_string(string):
    info = (string[:100] + '..') if len(string) > 1 else string
    return info

def draw_bar_chart(top_location_visits):
    import matplotlib.pyplot as plt; plt.rcdefaults()
    import numpy as np
    import matplotlib.pyplot as plt
    from textwrap import wrap,fill

    objects =[place[0] for place in top_location_visits]
    y_pos = np.arange(len(objects))
    performance = [place[1] for place in top_location_visits]
    plt.rcdefaults()
    fig, ax = plt.subplots()

    error = np.random.rand(len(objects))

    ax.barh(y_pos, performance, xerr=error, align='center',
            color='blue', ecolor='black')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(objects)
    ax.invert_yaxis()  # labels read top-to-bottom
    ax.set_title('Most places visited')
    plt.show()

print("Top Users------------------------")
print(draw_bar_chart(group_by_location()))

print("Top reviews----------------------")
print(draw_table(get_top_user_reviews()))
