import nltk
import luis
from src.Dialog_Manager import Student, Conversation
from src.utils import constants
import random

class nLUU: 
    def __init__(self, luisurl):
        self.luis = luis.Luis(luisurl)
        #Requires a local copy of atis.cfg
        atis_grammar = nltk.data.load("atis.cfg")
        self.parser = nltk.ChartParser(atis_grammar)

    def start_conversation(self):
        ''' 
            Starts conversation through command line interface. 
            To be called as first interaction with client.
        ''' 
        #student = Student.Student()
        #conversation = Conversation.Conversation()
        conversing = True
        our_response = "Hello. Welcome to my lair. How can I be of service?"
        while conversing:
            client_response = input(our_response + "\n")
            luis_analysis = self.get_luis(client_response)
            tree = self.create_syntax_tree(client_response)
            our_response_nebulous = dialog_manager.create_response(tree, luis_analysis) # tuple containing response type as first argument, and data to format for other arguments
            our_response = create_response_string(our_response_nebulous)
            if our_response == "STOP":
                conversing = False



    def tokenize(self, s):
        '''
            Tokenizes input from client
        '''
        return nltk.word_tokenize(s)


    def pos_tag(self, s):
        '''
            Part-of-speech taging for str
        '''
        return nltk.pos_tag(s)


    def create_syntax_tree(self, s):
        '''
            Creates a syntax tree from str
        '''
        return self.parser.parse(s)


    def get_luis(self, s):
        '''
            Calls  pyluis to get intent analysis
        '''
        return self.luis.analyze(s)


    def create_response_string(self, res_type, res):
        '''
            Takes whatever response from backend and converts to readable string
        '''
        rand = random.randint(0, len(res_type))
        res_type[0].format(res[0], res[1])