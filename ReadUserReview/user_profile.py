import csv

import pandas as pd
from mongodb.operations import operations
from bson.objectid import ObjectId
from bson.code import Code
import pymongo
import json
import bson
import os
class user_profiling():

    def __init__(self):
        self.profile=open("./csv/profile.csv","rb")
        self.reviews=open("./csv/reviews.csv","rb")
        self.universal_reviews=open("./csv/universal.csv","rb")
        self.mongo_client=operations()
        self.db=self.mongo_client.create_database("user_profiling")



    def get_value_from_string(self,arg):
        import re
        if arg:
            match=re.compile(r'\d+')
            if arg != "None":
                value=match.findall(arg)
                return value.__getitem__(0)
        return 0

    def remove_duplicates(self,list):
        newlist=[]
        for l in list:
            if l not in newlist:
                newlist.append(l)
        return newlist

    def read_profile(self):
        profile = pd.read_csv("./csv/profile.csv")
        profiles=[]
        for index,row in profile.iterrows():
            profiles.append({"UID":row["UID"],
                             "UserName":row["Username"],
                             "Travelstyle":row["Travelstyle"],
                             "From":row["From"],
                             "Helpful":row["Helpful"],
                             "Cities_visited":row["Cities Visited"],
                             "Badge":row["Badge"],
                             "Contribution":row["Contributions"]
                             })
        return profiles


    def read_reviews(self):
        reviews_csv = pd.read_csv("./csv/reviews.csv")
        reviews=[]
        for index,row in reviews_csv.iterrows():
            reviews.append({ "UID":row["UID"],
                             "review_id":row["review ID"],
                             "reviewCategory":row["reviewCategory"],
                             "where":row[" where"],
                             "title":row["title"],
                             "Content":row["Content"],
                             "Rating":row["rating"]
                             })
        return reviews

    def read_universal_reviews(self,u_id):
        universal_reviews_csv = pd.read_csv("./csv/universal.csv")
        universal_reviews=[]
        for index,row in universal_reviews_csv.iterrows():

            if row["UID"]==u_id:
                universal_reviews.append(row["Review Text"])
        return universal_reviews


    def get_user_document(self):
        import json
        users=self.read_profile()
        reviews=self.read_reviews()
        profiles=[]
        for user in users:
            universal_reviews=self.read_universal_reviews(user.get("UID"))
            doc={
                "u_id":user.get("UID"),
                "details":{
                    "profile_name":user.get("UserName"),
                    "travel_style":user.get("Travelstyle"),
                    "from":user.get("From"),
                    "helpful":self.get_value_from_string(user.get("Helpful")),
                    "total_cities_visited":self.get_value_from_string(user.get("Cities_visited")),
                    "level":self.get_value_from_string(user.get("Badge")),
                    "contributions":self.get_value_from_string(user.get("Contributions")),
                    "Since":abs(self.total_years(self.get_value_from_string(user.get("Since"))))
                },
                "similarity":{
                    "UID":[],
                    "sim_score":[],
                    "credibility_score":0
                },
                "reviews":universal_reviews
            }
            cities_visited=[]
            for review in reviews:
                if user.get("UID")==review.get("UID"):
                    place=review.get("where").split(":")[1] if ":" in review.get("where") else review.get("where")
                    if place:
                        cities_visited.append(place)
            doc.get("details")["cities"]=self.remove_duplicates(cities_visited)
            profiles.append(doc)
        return profiles

    def insert_profile(self):
        import json
        profiles=self.get_user_document()
        self.mongo_client.insert(self.db,profiles,"Users")
        self.mongo_client.create_index(self.db,"Users","u_id")

    def normalize_value(self,values):
        max_value=max(values)
        min_value=min(values)
        normalized=[]
        for value in values:
            if value !=None:
                numerator=(int(value)-min_value)
                denominator=(max_value-min_value)
                normalized_value=float(numerator)/denominator if numerator !=0 else 0
                normalized.append(round(normalized_value))
            else:
                normalized.append(0)
        return normalized

    def calculate_credibility_score(self,uid,levels,contributions,helpful,visited_cities,since):
        weights={"level":40,"contribution":17.5,"helpful":25,"visited_cities":12.5,"since":5}
        credibility_score={}
        for i in range(0,len(uid)):
            u_id=uid[i]
            level=levels[i]*weights.get("level")
            contribution=contributions[i]*weights.get("contribution")
            helpful_votes=helpful[i]*weights.get("helpful")
            total_cities_visited=visited_cities[i]*weights.get("visited_cities")
            member_since=since[i]*weights.get("since")
            total_score=level+contribution+helpful_votes+total_cities_visited+member_since
            credibility_score[u_id]=total_score
        return credibility_score

    def get_reviews_table(self):
        try:
           reviews= self.read_reviews()
           profiles=self.mongo_client.get_all_collections(self.db,"Users")
           review_docs=[]

           for profile in profiles:
               review_doc={}
               review_doc["u_id"]=profile.get("u_id")
               review_doc["details"]=[]
               for review in reviews:
                   if review.get("UID")==profile.get("u_id"):
                       review_doc.get("details").append({
                           "place":review.get("where").split(":")[1]  if ":" in review.get("where") else review.get("where"),
                           "Rating":review.get("Rating"),
                           "Text":review.get("Content"),
                           "Category":review.get("reviewCategory")
                       })

               review_docs.append(review_doc)
           return  json.dumps(review_docs)
        except Exception as e:
               message=e.message

    def create_reviews_table(self):
        reviews= json.loads(self.get_reviews_table())
        self.mongo_client.insert(self.db, reviews,"Reviews")
        self.mongo_client.create_index(self.db,"Reviews","u_id")

    def calculate_score(self,current_index,profiles):
        current_user=profiles[current_index]
        currentuser_travel_style=current_user.get("details").get("travel_style").split(",")
        currentuser_cities_visited=current_user.get("details").get("cities")
        similarity_score=[]
        users={}
        level_values=[]
        contribution_values=[]
        helpful_values=[]
        visited_cities=[]
        since=[]
        uid=[]
        for user in profiles:
            details=user.get("details")
            uid.append(user.get("u_id"))
            level_values.append(int(details.get("level")))
            contribution_values.append(int(details.get("contributions")))
            helpful_values.append(int(details.get("helpful")))
            visited_cities.append(int(details.get("total_cities_visited")))
            since.append(int(details.get("Since")))
            if user.get("u_id")!=current_user.get("u_id"):
                travel_styles=user.get("details").get("travel_style").split(",")
                cities=user.get("details").get("cities")
                match_travel_styles=0
                match_cities_visited=0
                total_travel_style=len(currentuser_travel_style)
                total_cities_visited=len(currentuser_cities_visited)
                for travel_style in travel_styles:
                    if travel_style in currentuser_travel_style:
                        match_travel_styles=match_travel_styles+1

                for city in cities:
                    if city in currentuser_cities_visited:
                        match_cities_visited=match_cities_visited+1

                users[user.get("u_id")]=round((float(match_travel_styles)/total_travel_style)*60)+round((float(match_cities_visited)/total_cities_visited)*40)
        import operator
        sorted_users = sorted(users.items(), key=operator.itemgetter(1),reverse=True)
        credibility_scores=self.calculate_credibility_score(uid,self.normalize_value(level_values),
                                         self.normalize_value(contribution_values),self.normalize_value(helpful_values),
                                         self.normalize_value(visited_cities),self.normalize_value(since))
        u_id=[]
        count=0
        for user in sorted_users:
            if count !=3:
                 u_id.append(user[0])
                 similarity_score.append(user[1])
                 count=count+1
            else:
                count=0
                break

        return u_id,similarity_score,credibility_scores

    def update_scores(self):
        profiles=[profile for profile in self.mongo_client.get_all_collections(self.db,"Users")]
        current_index=0

        for profile in profiles:
            users,similarity_score,credibility_scores=self.calculate_score(current_index,profiles)
            _id=profile.get("u_id")
            profile.get("similarity")["sim_score"]=similarity_score
            profile.get("similarity")["UID"]=users
            profile.get("similarity")["credibility_score"]=credibility_scores.get(profile.get("u_id"))
            self.mongo_client.update_collection(self.db,"Users",{"u_id":_id},profile)
            current_index=current_index+1

    def drop_collection(self):
        self.mongo_client.drop(self.db,"Users")
        self.mongo_client.drop(self.db,"Reviews")
        self.mongo_client.drop(self.db,"Users_Output")

    def get_reviews(self,user_id):
        reviews=self.mongo_client.get_collection(self.db,"Reviews",{"u_id":user_id})
        details=reviews.get("details")
        top_reviews={"Attractions":{},"Restaurant":{},"Hotel":{}}
        for detail in details:
            category=detail.get("Category")
            if category !="None":
               top_reviews[category]["Place:%s"%(detail.get("place"))]=detail.get("Rating")
               top_reviews[category][detail.get("Text")]=detail.get("Rating")
        return top_reviews

    def sort_dict_by_value(self,dict):
        import operator
        sorted_x = sorted(dict.items(), key=operator.itemgetter(1))
        return sorted_x

    def get_match_count(self,user_id):
        count=0
        profiles=self.mongo_client.get_all_collections(self.db,"Users")
        for profile in profiles:
            top_similar_user=profile.get("similarity").get("UID")
            if user_id in top_similar_user:
                count=count+1
        return count


    def create_output_user_table(self):
        users=self.mongo_client.get_all_collections(self.db,"Users")
        for profile in  users:
            user_doc={}
            details=profile.get("similarity")
            user_info=profile.get("details")
            users_score={}
            user_doc["u_id"]=profile.get("u_id")
            for u_id in details.get("UID"):
                user=self.mongo_client.get_collection(self.db,"Users",{"u_id":u_id})
                _id=u_id
                credibility_score=user.get("similarity").get("credibility_score")
                users_score[_id]=credibility_score
            sorted_x = self.sort_dict_by_value(users_score)
            user_id=sorted_x[len(sorted_x)-1][0]
            credibility_score=sorted_x[len(sorted_x)-1][1]
            reviews=self.get_reviews(user_id)

            categories={}
            place=[]
            for key,values in reviews.iteritems():
                top_reviews=[]
                sorted_values=self.sort_dict_by_value(values)
                length=len(sorted_values)-1
                range_length=length-2
                count=0
                while length>=range_length and length >=0:
                    if "Place:" in sorted_values[length][0]:
                        place.append(sorted_values[length][0].split(":")[1])
                    else:
                        top_reviews.append(sorted_values[length][0])
                    length=length-1
                    count=count+1

                categories[key]=top_reviews
            user_doc["Place"]=place
            user_doc["Top_Reviews"]=categories
            user_doc["Credible_user_match"]=user_id
            user_doc["Credibility_score"]=credibility_score
            user_doc["count"]=self.get_match_count(profile.get("u_id"))
            user_doc["places_visited"]=user_info.get("cities")
            self.mongo_client.insert(self.db,user_doc,"Users_Output")
            self.mongo_client.create_index(self.db,"Users_Output","u_id")

    def get_profile(self):
        import json
        from Test.Jsonencoder import JSONEncoder
        profile=self.mongo_client.get_collection(self.db,"Users",{"u_id":"5DB3C5FB75F7EB06896E73E6A1757C66"})
        output=self.mongo_client.get_collection(self.db,"Users_Output",{"u_id":"5DB3C5FB75F7EB06896E73E6A1757C66"})
        reviews=self.mongo_client.get_collection(self.db,"Reviews",{"u_id":"5DB3C5FB75F7EB06896E73E6A1757C66"})
        print(JSONEncoder().encode(output))

    def total_years(self,years):
        import datetime
        now = datetime.datetime.now()
        return (int(years)-now.year)



