import json
import os

def exportToJson(data):
        # Open a file for writing
        with open("config.json", "w+") as outfile:
            # Write the data to the file in JSON format
            print(data)
            json.dump(data, outfile, indent=4)

def loadFromJson(filename="config.json"):
    config = None
    if os.path.exists(filename):
        # Open the file for reading
        with open(filename, "r") as infile:
            # Load the data from the file into a dictionary
            config = json.load(infile)
    else:
        print("File doesn't exists")
    return config