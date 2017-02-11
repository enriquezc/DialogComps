import json
from src.NLUU import nluu
from src.Dialog_Manager import Conversation
import profile

def start_comps():
    print("Starting comps")
    config_file = open("./config.json")
    config = json.load(config_file)
    conversation = Conversation.Conversation(config["luisurl"])
    conversation.start_conversation()


if __name__ == "__main__":

    profile.run('start_comps()')

