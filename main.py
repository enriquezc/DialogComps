import json
import sys
from src.Dialog_Manager import Conversation
import profile

def start_comps(debug):
    config_file = open("./config.json")
    config = json.load(config_file)
    conversation = Conversation.Conversation(config["luisurl"], debug)
    conversation.welcome(debug)


if __name__ == "__main__":
    debug = False
    for arg in sys.argv:
        if arg == "-d" or arg == "--debug":
            debug = True

    start_comps(debug)
