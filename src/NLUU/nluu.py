import nltk
import luis
from src.Dialog_Manager import Student, Conversation, Course
from src.utils import constants
import random

class nLUU: 
    def __init__(self, luisurl):
        self.luis = luis.Luis(luisurl)
        #Requires a local copy of atis.cfg
        #atis_grammar = nltk.data.load("atis.cfg")
        #self.parser = nltk.ChartParser(atis_grammar)

    def start_conversation(self):
        ''' 
            Starts conversation through command line interface. 
            To be called as first interaction with client.
        ''' 
        conversation = Conversation.Conversation()
        conversing = True
        our_response = "Hello. Welcome to my lair. How can I be of service?"
        while conversing:
            client_response = input(our_response + "\n")
            luis_analysis = self.get_luis(client_response)
            #tree = self.create_syntax_tree(client_response)
            userQuery = conversation.get_next_response(client_response, luis_analysis) # tuple containing response type as first argument, and data to format for other arguments
            if userQuery.type == 1:
                print("Goodbye")
                conversing = False
                break
            our_response = self.create_response_string(userQuery)



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


    def create_response_string(self, userQuery):
        '''
            Takes whatever response from backend and converts to readable string
        '''
        if type(userQuery.object) == Course.Course:
            s = 'Here\'s some data about your course:\n'
            d = userQuery.object.__dict__
            print(d)
            for k, v in d.items():
                if v != None and v != 0 and not (type(v) == list and len(v) == 0):
                    s += k + ':' + v + '\n'
        elif type(userQuery.object) == Student:
            s = 'Please ask me about a course.'
        else:
            s = 'Please ask me about a course'
        '''rand = random.randint(0, len(res_type))
        res_type[0].format(res[0], res[1])'''
        return s