import os
from tqdm import tqdm
from pymongo import MongoClient



client = MongoClient("mongodb+srv://zach:G8GqPsUgP6b9VUvc@cluster0-svcn3.gcp.mongodb.net/test?retryWrites=true")
db = client["ocr_db"]


def mongo_writer(file):
	with open (file, "r") as f:
		lines = f.readlines()
	f.close()

	for line in tqdm(lines):
		obj = eval(line)

		collection_name = obj["College Code"].upper()
		collection = db[collection_name]

		collection.insert_one(obj)



if __name__ == '__main__':

	files = ["ForkPoolWorker-1.txt", "ForkPoolWorker-2.txt", "ForkPoolWorker-3.txt", "ForkPoolWorker-4.txt"]

	for file in files:
		mongo_writer(file)