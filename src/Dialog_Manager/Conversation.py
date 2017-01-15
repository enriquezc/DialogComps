import queue
import re
import sys
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
        self.student = Student.Student()
        self.last_query = 0
        self.head_node = self.NodeObject(User_Query.UserQuery(None, User_Query.QueryType.clarify),[],[])
        self.current_node = self.head_node
        self.current_class = None


    def build_Tree(self):
        listOfEnums = [0, 1, 2, 3, 4, 5, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 24, 25, 26, 30, 31, 32, 33, 34,
                       35, 36, 37]
        numNodes = len(listOfEnums)
        listOfNodes = []
        for i in range(numNodes):
            listOfNodes.append(NodeObject(None, None, [], []))

        #here we go...
        for i in range(len(listOfEnums)):
            currentNode = listOfNodes[i]
            currentNode.userQuery = User_Query.QueryType(listOfEnums[i])
        listOfNodes[0].required_questions.append(listOfNodes[6]) #name
        listOfNodes[6].required_questions.append(listOfNodes[10])#time left / year
        listOfNodes[10].potential_next_questions.extend([listOfNodes[7], listOfNodes[14], listOfNodes[12], listOfNodes[9]]) #major, concentration, distros, interests
        listOfNodes[7].required_questions.extend([listOfNodes[14], listOfNodes[13]]) #concentration, major requirements
        listOfNodes[7].potential_next_questions.append(listOfNodes[12]) #distros
        listOfNodes[14].potential_next_questions.extend([listOfNodes[13],listOfNodes[12], listOfNodes[9]]) #major reqs, distros, interests
        listOfNodes[12].potential_next_questions.append(listOfNodes[9]) #interests
        listOfNodes[12].required_questions.append(listOfNodes[24]) #ask if they want to take a course that fills these reqs
        listOfNodes[13].required_questions.append(listOfNodes[24])  #Ask if they want to take a course that fills these reqs
        listOfNodes[13].potential_next_questions.append(listOfNodes[9]) #interests
        listOfNodes[24].potential_next_questions.extend([listOfNodes[9], listOfNodes[27]]) #interests, should we reccomend something?
        listOfNodes[27].potential_next_questions.append(listOfNodes[20]) #what class would they want to take?
        listOfNodes[9].potential_next_questions.extend([listOfNodes[22], listOfNodes[21], listOfNodes[27]]) #department, prof, reccomend
        listOfNodes[22].potential_next_questions.extend([listOfNodes[21], listOfNodes[27]]) #prof, reccomend
        listOfNodes[21].potential_next_questions.append(listOfNodes[27]) #reccomend


        return
class NodeObject:
    userQuery = None
    asked = False
    answered = False
    required_questions = []
    potential_next_questions = []


    def __init__(self, userQ, requiredQ, potentialQ) -> object:
        self.userQuery = userQ
        self.required_questions.extend(requiredQ)
        self.potential_next_questions.extend(potentialQ)

    def is_answered(self):
        return False

    def answer(self):
        pass

    def relevant_course(*args):
        pass

    def call_database(self):
        pass


class DecisionTree:






    def __init__(self):
        Conversation.build_tree()
        current_node = None

    #@params: the current node of the tree
    #@return: the next node of the tree
    def get_next_node(self, current_node):
        try:
            if current_node.answered == 1:
                for i in range(len(current_node.required_questions)):
                    if current_node.required_questions[i].asked or current_node.required_questions[i].answered:
                        pass
                    else:
                        current_node = current_node.required_questions[i]

                for i in range(len(current_node.potential_next_questions)):
                    if current_node.potential_next_questions[i].asked or current_node.potential_next_questions[i].answered:
                        pass
                    else:
                        current_node = current_node.potential_next_questions[i]

                for i in range(len(current_node.required_questions)):
                    if current_node.required_questions[i].answered:
                        pass
                    else:
                        current_node = current_node.required_questions[i]

                for i in range(len(current_node.required_questions)):
                    if current_node.potential_next_questions[i].answered:
                        pass
                    else:
                        current_node = current_node.potential_next_questions[i]

            if current_node.answered == 0:
                for i in range(len(current_node.potential_next_questions)):
                    if current_node.potential_next_questions[i].asked or current_node.potential_next_questions[i].answered:
                        pass
                    else:
                        current_node = current_node.potential_next_questions[i]

                #have looped through and no node that is asked or answered, now loop to find one that is just not answered
                for i in range(len(current_node.potential_next_questions)):
                    if current_node.potential_next_questions[i].answered:
                        pass
                    else:
                        current_node = current_node.potential_next_questions[i]

            if current_node.userQuery > 10 and current_node.userQuery < 20:
                return User_Query.UserQuery(Conversation.student, current_node.userQuery)
            elif current_node.userQuery > 18:
                return User_Query.UserQuery(Conversation.current_class, current_node.userQuery)
            else:
                return User_Query.UserQuery(None, current_node.userQuery)
        except ValueError:
            print("Unexpected error:", sys.exc_info()[0])
            raise



















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
    def add_to_PriorityQueue(self, importance, user_query):
        self.priority_queue.put(importance, user_query)


        # @params
    # @return
    def get_next_response(self, input, luisAI):
        #luis_entities = self.classify_entities(luisAI)
        #luis_intent = self.classify_intent(luisAI)
        luis_entities = luisAI.entities
        luis_intent = luisAI.intents[0]
        #entity_information = self.task_manager_information(luis_entities)


        if luis_intent.intent == "ScheduleClass":
            # if entity.type == "class":  # add more if's for different types
            course = Course.Course()
            course_name = re.search("([A-Za-z]{2,4}) ?(\d{3})", input)

            course.id = course_name.group(0)
            course.courseNum = course_name.group(2)
            course.department = course_name.group(1)
            course.user_description = luisAI.query

            tm_courses = self.task_manager_information(course)
            if tm_courses == None:
                return User_Query.UserQuery(None, User_Query.QueryType.clarify)
            else:
                self.student.current_classes.append(tm_courses)
                #self.student.total_credits += tm_courses.credits
                #if self.student.total_credits < 12:
                return User_Query.UserQuery(tm_courses, User_Query.QueryType.schedule_class_res)

        elif luis_intent.intent == "ClassSentiment":
            course = Course.Course()
            self.task_manager_information(course)
            self.add_to_PriorityQueue(1, User_Query.UserQuery(course, User_Query.QueryType.class_info_sentiment))

        elif luis_intent.intent == "None":
            self.add_to_PriorityQueue(1, User_Query.UserQuery(None, User_Query.QueryType.clarify))

        elif luis_intent.intent == "ClassDescriptionRequest":
            course = Course.Course()  # for future complicated conditions.
            for entity in luis_entities:
                if entity.type == "class":  # add more if's for different types
                    if len(entity.entity) < 8 and entity.entity[-4:-1].isnumeric():
                        course.id = entity.entity
                        course.department = entity.entity[:-3]
                        course.courseNum = entity.entity[-4:-1]
                        course.user_description = luisAI.query
                    else:
                        course.name = entity.entity
                        course.user_description = luisAI.query
                if entity.type == "personname":
                    course.prof = entity.entity
                if entity.type == "time":  # time object is a list of lists, first is M-F, second is len 2,
                    pass  # with start/end time that day?
                    # want a parse tree / relation extraction because we do not know
                    # whether it is during, before, or after without context.
                if entity.type == "department":
                    course.department = entity.entity
            tm_courses = self.task_manager_information(course)
            self.student.potential_courses = tm_courses
            course = tm_courses
            self.student.all_classes.append(course)
            self.add_to_PriorityQueue(1, User_Query.UserQuery(course, User_Query.QueryType.new_class_description))

        elif luis_intent.intent == "WelcomeResponse":


        elif luis_intent.intent == "ScheduleRequest":
            course = Course.Course()
            for entity in luis_entities:
                if entity.type == "u'CLASS'":
                    for course in self.student.all_classes:
                        if entity.entity == course.name:
                            self.student.current_classes.append(self.student.current_classes(course))
                        else:
                            if len(entity.entity) < 8 and entity.entity[-4:-1].isnumeric():
                                course.id = entity.entity
                                course.department = entity.entity[:-3]
                                course.courseNum = entity.entity[-4:-1]
                                course.user_description = luisAI.query
                            else:
                                course.name = entity.entity
                                course.user_description = luisAI.query
                            tm_courses = self.task_manager_information(course)
                            course = tm_courses
                if entity.type == "u'PERSONNAME'":
                    for course in self.student.all_classes:
                        if entity.entity == course.prof:
                            self.student.current_classes.append(self.student.all_classes(course))
                        else:
                            course.prof = entity.entity
                            tm_courses = self.task_manager_information(course)
                            course = tm_courses
            for current_course in self.student.current_classes:
                if not course.name == current_course.name:
                    self.student.current_classes.append(self.student.current_classes(course))
                else:
                    pass

        elif luis_intent.intent == "ClassDescriptionResponse":
            course = Course.Course()
            self.task_manager_information(course)

        elif luis_intent.intent == "ClassProfessorRequest":
            course = Course.Course()
            for entity in luis_entities:
                if entity.type == "u'CLASS":
                    if len(entity.entity) < 8 and entity.entity[-4:-1].isnumeric():
                        course.id = entity.entity
                        course.department = entity.entity[:-3]
                        course.courseNum = entity.entity[-4:-1]
                        course.user_description = luisAI.query
                    else:
                        course.name = entity.entity
                        course.user_description = luisAI.query
                if entity.type == "u'PERSONNAME":
                    course.prof = entity.entity
            tm_courses = self.task_manager_information(course)
            self.student.potential_courses = tm_courses
            course = tm_courses
            self.student.all_classes.append(course)
            self.add_to_PriorityQueue(1, User_Query.UserQuery(course, User_Query.QueryType.new_class_prof))

        elif luis_intent.intent == "ClassProfessorResponse":
            course = Course.Course()
            self.task_manager_information(course)
            return User_Query.UserQuery(course, User_Query.QueryType.class_info_description)

        elif luis_intent.intent == "StudentRequirementRequest":
            course = Course.Course()
            self.task_manager_information(course)
            return User_Query.UserQuery(course, User_Query.QueryType.class_info_description)

        elif luis_intent.intent == "StudentRequirementResponse":
            course = Course.Course()
            self.task_manager_information(course)
            return User_Query.UserQuery(course, User_Query.QueryType.class_info_description)

        elif luis_intent.intent == "StudentMajorRequest":
            self.add_to_PriorityQueue(1, User_Query.UserQuery(self.student, User_Query.QueryType.student_info_major))

        elif luis_intent.intent == "StudentMajorResponse":
            for entity in luis_entities:
                if entity.type == "u'DEPARTMENT":
                    for major in self.student.major:
                        if entity.entity == major or len(self.student.major) == 2:
                            pass
                        else:
                            self.student.major.append(entity.entity)
            self.add_to_PriorityQueue(1, User_Query.UserQuery(self.student, User_Query.QueryType.student_info_major))

        elif luis_intent.intent == "StudentNameInfo":
            for entity in luis_entities:
                if entity.type == "u'PERSONNAME":
                    self.student.name = entity.entity
                else:
                    self.add_to_PriorityQueue(1, User_Query.UserQuery(self.student, User_Query.QueryType.clarify))

        elif luis_intent.intent == "ClassTimeResponse":
            course = Course.Course()
            self.task_manager_information(course)
            return User_Query.UserQuery(course, User_Query.QueryType.class_info_description)

        elif luis_intent.intent == "ClassTimeRequest":
            course = Course.Course()
            self.task_manager_information(course)
            return User_Query.UserQuery(course, User_Query.QueryType.class_info_description)

        elif luis_intent.intent == "ClassTermResponse":
            course = Course.Course()
            self.task_manager_information(course)
            return User_Query.UserQuery(course, User_Query.QueryType.class_info_description)

        elif luis_intent.intent == "ClassTermRequest":
            pass

        elif luis_intent.intent == "StudentInterests":
            for entity in luis_entities:
                if entity.type == "u'CLASS" or entity.type == "u'DEPARTMENT" or entity.type == "u'SENTIMENT":
                    self.student.interests.append(entity.entity)

        #else statement will ask for more information
        else:
        popped_query = self.pop_priority_queue()
        return popped_query

    # @params
    # @return
    def pop_priority_queue(self):
        if self.priority_queue.empty():
            return User_Query.UserQuery(None, User_Query.QueryType.clarify)  # will fill in in a second
        popped_userQuery = self.priority_queue.get_nowait()
        print(popped_userQuery)
        if popped_userQuery.type < 5:
            return popped_userQuery
        # for 10-17, we may format it so we only ask these questions once.
        userQuery_course = popped_userQuery.object
        userQuery_type = popped_userQuery.type
        if type == 10:
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
            else:
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
    def task_manager_information(self, course):
        tm_courses = TaskManager.query_courses(course)
        if len(tm_courses) == 1:
            return tm_courses
        else:
            return tm_courses[0]

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
