import os
import sys
from tqdm import tqdm
from pymongo import MongoClient

# Define the ocr_db to write to in Mongo
db = client[str(sys.argv[1])]

def mongo_writer(file):
	with open (file, "r") as f:
		lines = f.readlines()
	f.close()

	for line in tqdm(lines):
		obj = eval(line)
		# Collections are named by College Code
		collection_name = obj["College Code"]
		collection = db[collection_name]
		collection.insert_one(obj)

if __name__ == '__main__':

	files = ["ForkPoolWorker-1.txt", "ForkPoolWorker-2.txt", "ForkPoolWorker-3.txt", "ForkPoolWorker-4.txt"]

	for file in files:
		mongo_writer(file)
