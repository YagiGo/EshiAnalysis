#  coding: utf-8
#  负责数据库的交互
from pymongo import MongoClient

def getDBClient(ADDR, PORT):
    return MongoClient(ADDR, PORT)

