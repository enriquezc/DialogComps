import json
from src.NLUU import nluu
from src.Dialog_Manager import Conversation


def start_comps():
    config_file = open("./config.json")
    config = json.load(config_file)
    conversation = Conversation.Conversation(config["luisurl"])
    conversation.start_conversation()


if __name__ == "__main__":
    start_comps()