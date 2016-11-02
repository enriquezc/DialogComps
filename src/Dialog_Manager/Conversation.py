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
        #self.add_to_PriorityQueue(input)
        luis_entities = self.classify_entities(luisAI)
        luis_intent = self.classify_intent(luisAI)


        #entity_information = self.task_manager_information(luis_entities)
        if luis_intent == "ClassRequest":
            course = Course()
            for entity in luis_entities:
                if entity.type == "Course": #add more if's for different types
                    if length(entity) < 8 and entity[-4:-1].isnumeric():
                        course.id = entity
                        course.user_description = input

                    else:
                        course.name = entity
                        course.user_description = input

            #information_type = self.new_information(entity_information)
            course = self.add_to_student(entity_information)
            task_manager_information(course)
            return UserQuery(course, QueryType.new_class_description)
        else:



    # @params
    # @return
    def task_manager_information(self, course):


    #query the task manager with the entity given by luis
        return 0

    # @params intent / entities from the luisAI
    # @return which value in student the information refers to
    def new_information(self, intent, entity):
        return "interests"

    # @params course to add to student classes
    # @return 0 for added successfully, 1 for not added
    def schedule_course(self, new_course):

        for (course in self.student.previous_classes):
            if (new_course.id == course.id):
                return course
        for (course in self.student.current_classes):
            if (new_course.id == course.id):
                return course
        else:
            self.student.current_classes.append(new_course)
            return new_course


    # @return location in student to store information / check if information is stored
    # @params information (entity) that we are looking to store
    def add_to_student(self, new_course, type):
        for (course in self.student.previous_classes):
            if (new_course.id == course.id):
                return course
        for (course in self.student.current_classes):
            if (new_course.id == course.id):
                return course
        else:
            self.student.current_classes.append(new_course)
            return new_course

    def course_interest(self, course):
        return 0



