import queue
from nltk.tree import Tree
from src.Dialog_Manager import Student


class Conversation:

    nltk_PoS_codes = {"CC": "Coordinating conjunction",
    "CD": "Cardinal number", "DT": "Determiner", "EX": "Existential there",
    "FW": "Foreign word", "IN": "Preposition", # or subordinating conjunction
    "JJ": "Adjective", "JJR": "Adjective, comparative", "JJS": "Adjective, superlative",
    "LS": "List item marker", "MD": "Modal", "NN": "Noun, singular",# or mass
    "NNS": "Noun, plural", "NNP": "Proper noun, singular", "NNPS": "Proper noun, plural",
    "PDT": "Predeterminer", "POS": "Possessive ending", "PRP": "Personal pronoun",
    "PRP$":"Possessive pronoun", "RB": "Adverb", "RBR": "Adverb, comparative",
    "RBS": "Adverb, superlative", 'RP': "Particle", "SYM": "Symbol", "TO": "to",
    "UH": "Interjection", "VB": "Verb, base form", "VBD" :"Verb, past tense",
    "VBG": "Verb, gerund or present participle", "VBN": "Verb, past participle",
    "VBP": "Verb, non-3rd person singular present", "VBZ": "Verb, 3rd person singular present",
    "WDT": "Wh-determiner", "WP": "Wh-pronoun", "WP$": "Possessive wh-pronoun",
    "WRB": "Wh-adverb"}

    def __init__(self):
        self.priority_queue = queue.PriorityQueue()
        self.student = Student()
        self.last_query = 0

    # @params
    # @return
    def classify_intent(self, luis_input):
            #input is a luis dictionary
        if luis_input.intents[0].score >= .5:
            return luis_input.intents[0].intent
        return "unknown"

    # @params
    # @return
    def classify_entities(self, luis_input):
        CUTOFF = .3
        entities = {}
        for key in luis_input.keys():
            if luis_input.entities[key].score > CUTOFF:
                entities[luis_input.entities[key].type] = luis_input.entities[key].score
        return entities

    # @params
    # @return
    def add_to_PriorityQueue(self, input):
        self.priority_queue.put(input)

    # @params
    # @return
    def get_next_response(self, input, luisAI):
        self.add_to_PriorityQueue(input)
        luis_entities = self.classify_entities(luisAI)
        luis_intent = self.classify_intent(luisAI)
        entity_information = self.task_manager_information(luis_entities)
        if luis_intent == "ClassRequest":
            information_type = self.new_information(entity_information)
            student_value = self.add_to_student(entity_information, information_type)
        else:
            self.schedule_course(entity_information)



    # @params
    # @return
    def task_manager_information(self, entities):

    #query the task manager with the entity given by luis
        return 0

    # @params intent / entities from the luisAI
    # @return which value in student the information refers to
    def new_information(self, intent, entity):
        return "interests"

    # @params course to add to student classes
    # @return 0 for added successfully, 1 for not added
    def schedule_course(self, course):
        if course in self.student.current_classes:
            return 1
        else:
            self.student.current_classes.append(course)
            return 0

    # @return location in student to store information / check if information is stored
    # @params information (entity) that we are looking to store
    def add_to_student(self, information, type):
        return 0

    def course_interest(self, course):
        return 0



