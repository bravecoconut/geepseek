from datetime import datetime
import json
def log(string):
    with open("logs/log.txt", 'a') as file:
        log = f"**{datetime.now()}\n  {string} \n\n\n"
        file.write(log)


def list_to_string(data):

    data_str = repr(data)
    return data_str


list_dt=["a","b", "c"]
print(list_to_string(list_dt))