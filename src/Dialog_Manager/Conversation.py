import queue
from nltk.tree import Tree
from src.Dialog_Manager import Student, Course, User_Query
import luis
from src.Task_Manager import TaskManager


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
        self.student = Student.Student()
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
    def add_to_PriorityQueue(self, userQuery, importance):
        self.priority_queue.put(userQuery, importance)

    # @params
    # @return
    def pop_priority_queue(self):
        if self.priority_queue.empty():
            return User_Query.UserQuery(None, User_Query.QueryType.clarify) #will fill in in a second
        popped_userQuery = self.priority_queue.get()
        userQuery_course = popped_userQuery.object
        userQuery_type = popped_userQuery.type
        if type < 5:
            return popped_userQuery
        #for 10-17, we may format it so we only ask these questions once.
        elif type == 10:
            if userQuery_course.name == None:
                return popped_userQuery
            else:
                return self.pop_priority_queue()
        elif type == 11:
            if userQuery_course.major == None:
                return popped_userQuery
            else:
                return self.pop_priority_queue()
        elif type == 12:
            return self.pop_priority_queue()
        elif type == 13:
            return self.pop_priority_queue()
        elif type == 14:
            if userQuery_course.terms_left == 12:
                return popped_userQuery
            else
                return self.pop_priority_queue()
        elif type == 15:
            if userQuery_course.abroad == None:
                return popped_userQuery
            else:
                return self.pop_priority_queue()
        elif type == 16:
            return popped_userQuery
        elif type == 17:
            return popped_userQuery

        elif type == 20 or type == 30:
            if userQuery_course.name == None:
                return popped_userQuery
            else:
                return self.pop_priority_queue()

        elif type == 21 or type == 31:
            if userQuery_course.prof == None:
                return popped_userQuery
            else:
                return self.pop_priority_queue()
        elif type == 22:
            if userQuery_course.term == None:
                return popped_userQuery
            else:
                return self.pop_priority_queue()
        elif type == 23 or type == 24 or type == 33:
            if userQuery_course.sentiment == None:
                return popped_userQuery
            else:
                return self.pop_priority_queue()
        elif type == 25:
            if userQuery_course.scrunch == None:
                return popped_userQuery
            else:
                return self.pop_priority_queue()

        elif type == 26 or type == 35:
            if userQuery_course.time == None:
                return popped_userQuery
            else:
                return self.pop_priority_queue()
        elif type == 32:
            if userQuery_course.dept == None:
                return popped_userQuery
            else:
                return self.pop_priority_queue()
        elif type == 34:
            if userQuery_course.requirements == None:
                return popped_userQuery
            else:
                return self.pop_priority_queue()
        elif type == 36:
            if userQuery_course.prof == "":
                return popped_userQuery
            else:
                return self.pop_priority_queue()

        # @params
    # @return
    def get_next_response(self, input, luisAI):
        #self.add_to_PriorityQueue(input)
        #luis_entities = self.classify_entities(luisAI)
        #luis_intent = self.classify_intent(luisAI)
        luis_entities = luisAI.entities
        luis_intent = luisAI.intents[0]
        #entity_information = self.task_manager_information(luis_entities)
        if luis_intent.intent == "ScheduleClass":
            course = Course.Course()
            self.task_manager_information(course)
            return User_Query.UserQuery(course, User_Query.QueryType.new_class_requirements)

        elif luis_intent.intent == "ClassSentiment":
            course = Course.Course()
            self.task_manager_information(course)
            return User_Query.UserQuery(course, User_Query.QueryType.class_info_sentiment)

        elif luis_intent.intent == "None":
            return User_Query.UserQuery(None, User_Query.QueryType.clarify)

        elif luis_intent.intent == "ClassInfoRequest":
            course = Course.Course()  # for future complicated conditions.
            for entity in luis_entities:
                if entity.type == "u'CLASS'":  # add more if's for different types
                    if len(entity.entity) < 8 and entity.entity[-4:-1].isnumeric():
                        course.id = entity.entity
                        course.department = entity.entity[:-3]
                        course.courseNum = entity.entity[-4:-1]
                        course.user_description = luisAI.query
                    else:
                        course.name = entity.entity
                        course.user_description = luisAI.query
                if entity.type == "u'PERSONNAME'":
                    course.prof = entity.entity
                if entity.type == "u'TIME'":  # time object is a list of lists, first is M-F, second is len 2,
                    pass  # with start/end time that day?
                    # want a parse tree / relation extraction because we do not know
                    # whether it is during, before, or after without context.
                if entity.type == "u'DEPARTMENT'":
                    course.department = entity.entity

            self.task_manager_information(course)

            return User_Query.UserQuery(course, User_Query.QueryType.class_info_term)
        elif luis_intent.intent == "WelcomeResponse":
            return User_Query.UserQuery(None, User_Query.QueryType.welcome)
        elif luis_intent.intent == "ScheduleInfoRequest":
            course = Course.Course()
            self.task_manager_information(course)
            return User_Query.UserQuery(course, User_Query.QueryType.class_info_time)
        elif luis_intent.intent == "ClassInfoResponse":
            course = Course.Course()
            self.task_manager_information(course)
            return User_Query.UserQuery(course, User_Query.QueryType.class_info_description)


        #else statement will ask for more information
        else:
            return User_Query.UserQuery(None, User_Query.QueryType.clarify)



    # @params
    # @return
    def task_manager_information(self, course):
        print("Trying to query courses from Conversation.py")
        return TaskManager.query_courses(course)

    #query the task manager with the entity given by luis

    # @params intent / entities from the luisAI
    # @return which value in student the information refers to
    def new_information(self, intent, entity):
        return "interests"

    # @params course to add to student classes
    # @return 0 for added successfully, 1 for not added
    def schedule_course(self, new_course):

        for course in self.student.previous_classes:
            if new_course.id == course.id:
                return course
        for course in self.student.current_classes:
            if new_course.id == course.id:
                return course
        else:
            self.student.current_classes.append(new_course)
            return new_course


    # @return location in student to store information / check if information is stored
    # @params information (entity) that we are looking to store
    def add_to_student(self, new_course, type):
        for course in self.student.previous_classes :
            if new_course.id == course.id:
                return course
        for course in self.student.current_classes :
            if new_course.id == course.id:
                return course
        else:
            self.student.current_classes.append(new_course)
            return new_course

    def course_interest(self, course):
        return 0
