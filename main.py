import json
from src.NLUU import nluu
from src.Dialog_Manager import *

def start_comps():
    config_file = open("./config.json")
    config = json.load(config_file)
    nluu_obj = nluu.nLUU(config["luisurl"])
    nluu_obj.start_conversation()


if __name__ == "__main__":
    start_comps()