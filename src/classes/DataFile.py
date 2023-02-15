# Imports
import os

# Handles datcs format files
class DataFile:

    # Constructor
    def __init__(self, path):

        self.data = {}
        self.path = path

        # Fetches existing file data
        if os.path.exists(self.path):
            with open(self.path, "r") as file:
                for line in file:
                    
                    # Line is reading a string
                    if "\"" in line:
                        line = line.split("\"")
                        self.data[line[0].strip().split("::")[0]] = f"{line[1]}"

                    else:

                        # Cleans up line of data
                        line = "".join(line.split())
                        line = line.split("#")[0]
                        info = line.split("::")

                        # If line is valid, add it to data
                        if line != "" and len(info) == 2:
                            self.data[info[0]] = eval(info[1])

    # Saves current data
    def save(self):

        with open(self.path, "w") as file:
            for key in self.data.keys():

                # Saves formatted value
                value = self.data[key]
                if type(value) == str:
                    value = f"\"{value}\""
                file.write(f"{key}::{value}\n")

    # Deletes a given key value pair
    def delete(self, key): del self.data[key]

    # Gets a data value
    def get(self, key): return self.data[key]

    # Sets a data value
    def set(self, key, value): self.data[key] = value
