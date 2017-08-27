from pymongo import MongoClient
import pymongo
class operations():
    def __init__(self):
        self.client=MongoClient("localhost",27017,maxPoolSize=50)

    def create_database(self,db_name=None):
        if db_name:
           db=self.client[db_name]
           return db
        raise Exception("Database Not Found")

    def insert(self,db,data,table_name=None):
        if table_name and db and data:
            table=db[table_name]
            table_id=table.insert(data)
            return table_id

    def create_index(self,db,collection_name,field):
        db[collection_name].create_index([(field, pymongo.ALL)],unique=True,dropDups=True)

    def get_collection(self,db,collection_name,find_by):
        collection=db[collection_name]
        return collection.find_one(find_by)

    def get_all_collections(self,db,collection_name):
        collection=db[collection_name]
        return collection.find()

    def update_collection(self,db,collection_name,update_by,doc):
        collection=db[collection_name]
        collection.save(doc)
        return "Updated"

    def drop(self,db,collection_name):
        collection=db[collection_name]
        collection.drop()



