#import nltk
#import pyluis
from src.Dialog_Manager import Student, Conversation

class nLUU: 
    def __init__(self, luisurl):
        self.luis = Luis(luisurl)

    def start_conversation(self):
        ''' 
            Starts conversation through command line interface. 
            To be called as first interaction with client.
        ''' 
        student = Student()
        conversation = Conversation()
        conversing = True
        our_response = "Hello. Welcome to my lair. How can I be of service?"
        while conversing:
            client_response = input(our_response)
            luis_analysis = get_luis(client_response)
            tree = create_syntax_tree(client_response)
            our_response_nebulous = dialog_manager.create_response(tree, luis_analysis)
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


    def get_luis(self, s):
        '''
            Calls  pyluis to get intent analysis
        '''
        return self.luis.analyze(s)


    def create_response_string(self, res):
        '''
            Takes whatever response from backend and converts to readable string
        '''