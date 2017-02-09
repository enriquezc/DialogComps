import queue
import re
import sys
from nltk.tree import Tree
from src.NLUU import nluu
import nltk
import luis
from src.Task_Manager import TaskManager
from src.Dialog_Manager import Student, Course, User_Query, DecisionTree
import datetime


class Conversation:
    nltk_PoS_codes = {"CC": "Coordinating conjunction",
                      "CD": "Cardinal number", "DT": "Determiner", "EX": "Existential there",
                      "FW": "Foreign word", "IN": "Preposition",  # or subordinating conjunction
                      "JJ": "Adjective", "JJR": "Adjective, comparative", "JJS": "Adjective, superlative",
                      "LS": "List item marker", "MD": "Modal", "NN": "Noun, singular",  # or mass
                      "NNS": "Noun, plural", "NNP": "Proper noun, singular", "NNPS": "Proper noun, plural",
                      "PDT": "Predeterminer", "POS": "Possessive ending", "PRP": "Personal pronoun",
                      "PRP$": "Possessive pronoun", "RB": "Adverb", "RBR": "Adverb, comparative",
                      "RBS": "Adverb, superlative", 'RP': "Particle", "SYM": "Symbol", "TO": "to",
                      "UH": "Interjection", "VB": "Verb, base form", "VBD": "Verb, past tense",
                      "VBG": "Verb, gerund or present participle", "VBN": "Verb, past participle",
                      "VBP": "Verb, non-3rd person singular present", "VBZ": "Verb, 3rd person singular present",
                      "WDT": "Wh-determiner", "WP": "Wh-pronoun", "WP$": "Possessive wh-pronoun",
                      "WRB": "Wh-adverb"}

    def __init__(self, luis_url):
        self.student_profile = Student.Student()
        self.last_query = 0
        self.last_user_query = []
        self.head_node = DecisionTree.NodeObject(User_Query.UserQuery(None, User_Query.QueryType.welcome), [], [])
        self.current_node = self.head_node
        self.current_class = None
        self.decision_tree = DecisionTree.DecisionTree(self.student_profile)
        self.queries = []
        self.conversing = False
        self.nluu = nluu.nLUU(luis_url)
        self.utterancesStack = []
        self.mapOfIntents = {}

        TaskManager.init()

    def start_conversation(self):
        self.conversing = True
        our_response = self.get_current_node()[0]
        our_str_response = self.nluu.create_response(our_response.type)
        self.utterancesStack.append(our_response)
        while self.conversing:
            print(our_str_response)
            client_response = input()
            luis_analysis = self.nluu.get_luis(client_response)
            self.utterancesStack.append(luis_analysis)
            print("luis: {}".format(luis_analysis))
            userQueries = self.get_next_response(client_response, luis_analysis) or User_Query.UserQuery(self.student_profile, User_Query.QueryType.clarify) # tuple containing response type as first argument, and data to format for other arguments
            self.last_user_query = userQueries
            our_str_response = ""
            if type(userQueries) is list:
                for userQuery in userQueries:
                    self.utterancesStack.append(userQuery)
                    print("userQuery: {}".format(userQuery.type))
                    if userQuery.type == User_Query.QueryType.goodbye:
                        print("Goodbye")
                        self.conversing = False
                        break
                    our_str_response += self.nluu.create_response(userQuery) + "\n"
            else:
                self.utterancesStack.append(userQueries)
                print("userQuery: {}".format(userQueries.type))
                if userQueries.type == User_Query.QueryType.goodbye:
                    print("Goodbye")
                    self.conversing = False
                    break
                our_str_response += self.nluu.create_response(userQueries) + "\n"

    # @params
    # @return
    def classify_intent(self, luis_input):
        # input is a luis dictionary
        for intent in luis_input.intents:
            if intent.score >= .15 and intent.intent != "None":
                return intent.intent
            else:
                pass
        return "None"

    # @params
    # @return
    def classify_entities(self, luis_input):
        CUTOFF = .05
        entities = {}
        for key in range(len(luis_input.entities)):
            if luis_input.entities[key].score > CUTOFF:
                entities[luis_input.entities[key].type] = luis_input.entities[key].score
        return entities


    def get_current_node(self):
        return [User_Query.UserQuery(self.student_profile, self.current_node.userQuery)]


    def handleStudentMajorRequest(self, input, luisAI, luis_intent, luis_entities):
        if len(luis_entities) == 0:
            print("no entity")
            tokens = nltk.word_tokenize(luisAI.query)
            pos = nltk.pos_tag(tokens)
            major = [word for word, p in pos if p in ['JJ','NN']]

            if len(major) == 0:
                return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.clarify)]
            print("major ", major)
            #tm_major = TaskManager.smart_department_search(major)
            #print("tm major: ", tm_major)
            self.student_profile.major = major[0]

            self.last_query = 11
            print(self.student_profile.major)
            return [self.decision_tree.get_next_node()]
        for entity in luis_entities:
            if entity.type == "department":
                self.student_profile.major.append(entity.entity)
            print(self.student_profile.major)
        return [self.decision_tree.get_next_node()]

    def handleStudentMajorResponse(self, input, luisAI, luis_intent, luis_entities):
        return self.handleStudentMajorRequest(input, luisAI, luis_intent, luis_entities)

    def handleScheduleClass(self, input, luisAI, luis_intent, luis_entities):
        # if entity.type == "class":  # add more if's for different types
        course = Course.Course()
        if len(luis_entities) == 0:
            print("We're here")
            possibilities = self.nluu.find_course(luisAI.query)
            possibilities_str = " ".join(possibilities)
            tm_courses = self.task_manager_keyword(possibilities)
            print("tm_courses: {}".format(tm_courses))
            self.student_profile.relevant_class = tm_courses
            if self.student_profile.current_credits < 18:
                return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.schedule_class_res)
                    , self.decision_tree.get_next_node()]
            else:
                return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.full_schedule_check)
                    , self.decision_tree.get_next_node()]
        for entity in luis_entities:
            if entity.type == 'class':
                course_name = re.search("([A-Za-z]{2,4}) ?(\d{3})", input)
                course.user_description = luisAI.query
                if course_name:
                    course.id = course_name.group(0)
                    course.course_num = course_name.group(2)
                    course.department = course_name.group(1)
                else:
                    course.name = entity.entity

                tm_courses = self.task_manager_information(course)
                if type(tm_courses) == list:
                    tm_courses = tm_courses[0]
                self.student_profile.relevant_class = tm_courses
                self.student_profile.current_classes.append(tm_courses)
                self.student_profile.current_credits = + 6
                self.student_profile.total_credits += tm_courses.credits
                print(self.student_profile.current_credits)
                if self.student_profile.current_credits < 12:
                    self.current_class, self.decision_tree.current_course = course, course
                    return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.schedule_class_res)
                        , self.decision_tree.get_next_node()]
                else:
                    self.current_class, self.decision_tree.current_course = course, course
                    return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.full_schedule_check)
                        , self.decision_tree.get_next_node()]

            if entity.type == "personname":
                course.prof = entity.entity
                tm_courses = self.task_manager_information(course)
                self.student_profile.potential_courses = tm_courses
                if not tm_courses:
                    return [User_Query.UserQuery(None, User_Query.QueryType.clarify)]
                else:
                    for pot_course in self.student_profile.potential_courses:
                        if pot_course.name or pot_course.id:
                            self.student_profile.current_classes.append(tm_courses)
                            self.student_profile.current_credits += 6
                            self.student_profile.total_credits += tm_courses.credits
                            if self.student_profile.current_credits < 12:
                                self.current_class, self.decision_tree.current_course = course, course
                                return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.schedule_class_res)
                                    , self.decision_tree.get_next_node()]
                            else:
                                self.current_class, self.decision_tree.current_course = course, course
                                return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.full_schedule_check)
                                    , self.decision_tree.get_next_node()]
            if entity.type == "time":  # time object is a list of lists, first is M-F, second is len 2,
                pass  # with start/end time that day?
            # want a parse tree / relation extraction because we do not know
            # whether it is during, before, or after without context.
            if entity.type == "department":
                course.department = entity.entity
                tm_courses = self.task_manager_information(course)
                self.student_profile.potential_courses = tm_courses
                self.current_class, self.decision_tree.current_course = course, course
                return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.schedule_class_res)
                    , self.decision_tree.get_next_node()]

    def handleClassDescriptionRequest(self, input, luisAI, luis_intent, luis_entities):
        course = Course.Course()
        if len(luis_entities) == 0:
            print("Class description no entity")
            tokens = nltk.word_tokenize(luisAI.query)
            pos = nltk.pos_tag(tokens)
            verbs = [word for word,p in pos if p == 'NNP']
            if "interested" in verbs:
                self.handleStudentInterests(input, luisAI, luis_intent, luis_entities)
            possibilities = self.nluu.find_course(luisAI.query)
            if len(possibilities) == 0:
                return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.clarify)
                    , self.decision_tree.get_next_node()]
            tm_courses = self.task_manager_keyword(possibilities)
            print("tm_courses: {}".format(tm_courses))
            self.student_profile.relevant_class = tm_courses
            self.student_profile.current_classes.append(tm_courses)
            self.student_profile.current_class, self.decision_tree.current_course = course, course
            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.new_class_description)
                , self.decision_tree.get_next_node()]
        for entity in luis_entities:
            print(entity.type)
            tm_courses = None
            if entity.type == 'class':
                course_name = re.search("([A-Za-z]{2,4}) ?(\d{3})", input)
                course.user_description = luisAI.query
                if course_name:
                    course.id = course_name.group(0)
                    course.course_num = course_name.group(2)
                    course.department = course_name.group(1)
                    tm_courses = self.task_manager_information(course)
                else:
                    tm_courses = self.task_manager_class_title_match(entity.entity)

                if not tm_courses:
                    return self.decision_tree.get_next_node(2)

                else:
                    if type(tm_courses) is list:
                        self.student_profile.relevant_class = tm_courses
                    else:
                        self.student_profile.relevant_class.append(tm_courses)

                    self.student_profile.current_classes.append(tm_courses)
                    self.student_profile.current_class, self.decision_tree.current_course = course, course
                    return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.new_class_description)
,self.decision_tree.get_next_node()]
            if entity.type == "personname":
                course.prof = entity.entity
                # query on previous courses with professors
            if entity.type == "time":  # time object is a list of lists, first is M-F, second is len 2,
                pass  # with start/end time that day?
                # want a parse tree / relation extraction because we do not know
                # whether it is during, before, or after without context.
            if entity.type == "department":
                course.department = entity.entity
                tm_courses = self.task_manager_information(course)
                self.student_profile.potential_courses = tm_courses
                course = tm_courses
                self.student_profile.all_classes.append(course)
                self.current_class, self.decision_tree.current_course = course, course
                return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.new_class_description)
                    , self.decision_tree.get_next_node()]


    def handleStudentNameInfo(self, input, luisAI, luis_intent, luis_entities):
        if len(luis_entities) == 0:
            name = self.nluu.find_name(luisAI.query)
            self.student_profile.name = name
            return [self.decision_tree.get_next_node()]

        for entity in luis_entities:
            if entity.type == "personname":
                self.student_profile.name = entity.entity
        if self.student_profile.name:
            return [self.decision_tree.get_next_node()]

        else:
            return [self.decision_tree.get_next_node()]


    def handleClassSentiment(self, input, luisAI, luis_intent, luis_entities):
        '''prev_course = None
        if self.student_profile.all_classes:
            if prev_course in self.student_profile.all_classes:

        else:
            return [User_Query.UserQuery(None, User_Query.QueryType.clarify)]

        return [User_Query.UserQuery(prev_course, User_Query.QueryType.class_info_sentiment)]'''


    def handleWelcomeResponse(self, input, luisAI, luis_intent, luis_entities):
        return [User_Query.UserQuery(None, User_Query.QueryType.name)]


    def handleClassDescriptionResponse(self, input, luisAI, luis_intent, luis_entities):
        course = Course.Course()
        self.task_manager_information(course)

    def handleClassProfessorRequest(self, input, luisAI, luis_intent, luis_entities):
        course = Course.Course()
        for entity in luis_entities:
            print(entity.type)
            if entity.type == 'class':
                course_name = re.search("([A-Za-z]{2,4}) ?(\d{3})", input)
                course.user_description = luisAI.query
                if course_name:
                    course.id = course_name.group(0)
                    course.course_num = course_name.group(2)
                    course.department = course_name.group(1)
                else:
                    course.name = entity.entity

                tm_courses = self.task_manager_information(course)
                if not tm_courses:
                    return [User_Query.UserQuery(None, User_Query.QueryType.clarify)]
                else:
                    self.student_profile.current_classes.append(tm_courses)
                    return [User_Query.UserQuery(tm_courses, User_Query.QueryType.new_class_prof)]

    def handleClassProfessorResponse(self, input, luisAI, luis_intent, luis_entities):
        course = Course.Course()
        for entity in luis_entities:
            print(entity.type)
            if entity.type == 'class':
                course_name = re.search("([A-Za-z]{2,4}) ?(\d{3})", input)
                course.user_description = luisAI.query
                if course_name:
                    course.id = course_name.group(0)
                    course.course_num = course_name.group(2)
                    course.department = course_name.group(1)
                else:
                    course.name = entity.entity

                tm_courses = self.task_manager_information(course)
                if not tm_courses:
                    return [User_Query.UserQuery(None, User_Query.QueryType.clarify)]
                else:
                    self.student_profile.current_classes.append(tm_courses)
                    return [User_Query.UserQuery(tm_courses, User_Query.QueryType.new_class_prof)]

    def handleStudentRequirementRequest(self, input, luisAI, luis_intent, luis_entities):
        course = Course.Course()
        self.task_manager_information(course)
        return [User_Query.UserQuery(course, User_Query.QueryType.class_info_description)]

    def handleStudentRequirementResponse(self, input, luisAI, luis_intent, luis_entities):
        course = Course.Course()
        self.task_manager_information(course)
        return [User_Query.UserQuery(course, User_Query.QueryType.class_info_description)]


    # done
    def handleClassTimeResponse(self, input, luisAI, luis_intent, luis_entities):
        for entity in luis_entities:
            for course in self.student_profile.all_classes:
                if entity == course:
                    return [User_Query.UserQuery(course, User_Query.QueryType.class_info_description)]


    def handleClassTimeRequest(self, input, luisAI, luis_intent, luis_entities):
        course = Course.Course()
        self.task_manager_information(course)
        return [User_Query.UserQuery(course, User_Query.QueryType.class_info_description)]

    def handleClassTermResponse(self, input, luisAI, luis_intent, luis_entities):
        course = Course.Course()
        self.task_manager_information(course)
        return [User_Query.UserQuery(course, User_Query.QueryType.class_info_description)]

    def handleClassTermRequest(self, input, luisAI, luis_intent, luis_entities):
        pass

    # done
    def handleStudentInterests(self, input, luisAI, luis_intent, luis_entities):
        if len(luis_entities) == 0:
            tokens = nltk.word_tokenize(luisAI.query)
            pos = nltk.pos_tag(tokens)
            interests = [word for word,p in pos if p in ['NNP','NNS','JJ','VBG']]
            
            self.student_profile.interests.add(interests)
            print("Interest")
            print(self.student_profile.interests[0])

            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.student_info_interests_res)
                , self.decision_tree.get_next_node()]
        for entity in luis_entities:
            print(entity)
            if entity.type == "u'CLASS" or entity.type == "u'DEPARTMENT" or entity.type == "u'SENTIMENT":
                self.student_profile.interests.append(entity.entity)
        return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.student_info_interests_res)
            , self.decision_tree.get_next_node()]


        # @params
    # @return
    def get_next_response(self, input, luisAI):
        self.last_query = input
        luis_entities = luisAI.entities
        luis_intent = self.classify_intent(luisAI)

        eval_fn = None
        try:
            eval_fn = eval("self.handle{}".format(luis_intent))
        except:
            eval_fn = None

        if eval_fn:
            return eval_fn(input, luisAI, luis_intent, luis_entities)
        # else statement will ask for more information
        else:
            luis_intent = self.decision_tree.current_node.userQuery
            eval_fn = None
            try:
                eval_fn = eval("self.handle{}".format(luis_intent))
            except:
                eval_fn = None
            if eval_fn:
                return eval_fn(input, luisAI, luis_intent, luis_entities)

            # if entity.type == "class":  # add more if's for different types
            if self.decision_tree.current_node.userQuery.value == 10: #student info name
                if luis_entities:
                    for entity in luis_entities:
                        if entity.type == 'personname':
                            self.student_profile.name = entity.entity
                            return self.decision_tree.get_next_node() #also would ideally say greet user by name
                elif len(self.last_query.split()) < 3:
                    self.student_profile.name = self.last_query
                    return self.decision_tree.get_next_node()
                else:
                    return [User_Query.UserQuery(None, User_Query.QueryType.clarify)]

            elif self.decision_tree.current_node.userQuery.value == 11: #student info major
                if luis_entities:
                    for entity in luis_entities:
                        if entity.type == "department":
                            self.student_profile.major = entity.entity
                            return self.decision_tree.get_next_node()
                if "undecided" in self.last_query or "undeclared" in self.last_query:
                    self.student_profile.major = "undeclared"
                    return self.decision_tree.get_next_node()
                if len(self.last_query.split()) < 4:
                    self.student_profile.major = self.last_query
                    print(self.student_profile.major)
                    return [self.decision_tree.get_next_node()]
                else:
                    return [User_Query.UserQuery(None, User_Query.QueryType.clarify)]

            elif self.decision_tree.current_node.userQuery.value == 13:
                return self.handleStudentInterests(self, input, luisAI, luis_intent, luis_entities)

            elif self.decision_tree.current_node.userQuery.value == 14:
                cur_term = "fall"
                if datetime.now().month < 4:
                    cur_term = "winter"
                elif datetime.now().month < 9:
                    cur_term = "spring"
                freshYear = str(datetime.now().year + 3)
                sophYear =  str(datetime.now().year + 2)
                juniorYear = str(datetime.now().year + 1)
                seniorYear =  str(datetime.now().year)

                if "fresh" in self.last_query or "frosh" in self.last_query or freshYear in self.last_query or "first" in self.last_query:
                    self.student_profile.major = "undeclared"
                    self.student_profile.terms_left = 11
                    if cur_term == "fall":
                        self.student_profile.terms_left = 11
                    elif cur_term == "winter":
                        self.student_profile.terms_left = 10
                elif "soph" in self.last_query or "second" in self.last_query or sophYear in self.last_query:
                    self.student_profile.terms_left = 8
                    if cur_term == "fall":
                        self.student_profile.terms_left = 7
                        self.student_profile.major = "undeclared"
                    elif cur_term == "winter":
                        self.student_profile.terms_left = 6
                        self.student_profile.major = "undeclared"
                elif "junior" in self.last_query or "third" in self.last_query or juniorYear in self.last_query:
                    self.student_profile.terms_left = 5
                    if cur_term == "fall":
                        self.student_profile.terms_left = 4
                    elif cur_term == "winter":
                        self.student_profile.terms_left = 3
                elif "senior" in self.last_query or "fourth" in self.last_query or seniorYear in self.last_query or "final" in self.last_query or "last" in self.last_query:
                    self.student_profile.terms_left = 2
                    if cur_term == "fall":
                        self.student_profile.terms_left = 1
                    elif cur_term == "winter":
                        self.student_profile.terms_left = 3
                else:
                    return [User_Query.UserQuery(None, User_Query.QueryType.clarify)]
                return self.decision_tree.get_next_node()

            elif self.decision_tree.current_node.userQuery.value == 16:
                if "nothing" in self.last_query or "none" in self.last_query:
                    self.decision_tree.current_node.answered = True
                    return self.decision_tree.get_next_node()
                if luis_entities:
                    for entity in luis_entities:
                        if entity.type == "class":
                            self.student_profile.distributions_needed.append(Course.Course(entity.entity))
                    if len(self.student_profile.distributions_needed) != 0:
                        return self.decision_tree.get_next_node()
                if ',' in self.last_query:
                    listOfWords = self.last_query.split(",")
                    for word in listOfWords:
                        if len(word.split()) < 4:
                            self.student_profile.distributions_needed.append(Course.Course(word))
                    if len(self.student_profile.distributions_needed) != 0:
                        return self.decision_tree.get_next_node()
                return [User_Query.UserQuery(None, User_Query.QueryType.clarify)]

            elif self.decision_tree.current_node.userQuery.value == 17:
                if "nothing" in self.last_query or "none" in self.last_query:
                    self.decision_tree.current_node.answered = True
                    return self.decision_tree.get_next_node()
                if luis_entities:
                    for entity in luis_entities:
                        if entity.type == "class":
                            self.student_profile.major_classes_needed.append(Course.Course(entity.entity))
                    if len(self.student_profile.major_classes_needed) != 0:
                        return self.decision_tree.get_next_node()
                if ',' in self.last_query:
                    listOfWords = self.last_query.split(",")
                    for word in listOfWords:
                        if len(word.split()) < 4:
                            self.student_profile.major_classes_needed.append(Course.Course(word))
                    if len(self.student_profile.major_classes_needed) != 0:
                        return self.decision_tree.get_next_node()

                return [User_Query.UserQuery(None, User_Query.QueryType.clarify)]

            elif self.decision_tree.current_node.userQuery.value == 31:
                if luis_entities:
                    for entity in luis_entities:
                        if entity.type == 'personname':
                            c = Course.Course()
                            c.prof = entity.entity
                            self.student_profile.potential_courses.append(c)
                        if self.student_profile.potential_courses != []:
                            return self.decision_tree.get_next_node()
                elif len(self.last_query.split()) < 3:
                    c = Course.Course()
                    c.prof = self.last_query
                    self.student_profile.potential_courses.append(c)
                    return self.decision_tree.get_next_node()
                else:
                    return [User_Query.UserQuery(None, User_Query.QueryType.clarify)]
            elif self.decision_tree.current_node.userQuery.value == 32:
                if luis_entities:
                    for entity in luis_entities:
                        if entity.type == "department":
                            c = Course.Course()
                            c.department = entity.entity
                            self.student_profile.potential_courses.append(c)
                    if self.student_profile.potential_courses != []:
                        return self.decision_tree.get_next_node()
                if len(self.last_query.split()) < 3:
                    c = Course.Course()
                    c.department = self.last_query
                    self.student_profile.potential_courses.append(c)
                    return self.decision_tree.get_next_node()
                return [User_Query.UserQuery(None, User_Query.QueryType.clarify)]
            elif self.decision_tree.current_node.userQuery.value == 37:
                if " ok" in self.last_query or "sure" == self.last_query or "reccommend" in self.last_query:
                    print("they have gotten to the point where they want a course from us")
                    print("Lets fix this later")
                if "no " in self.last_query or "I don" in self.last_query or "I've" in self.last_query or "know" in self.last_query or "I'm" in self.last_query:
                    return self.decision_tree.get_next_node()
                return [User_Query.UserQuery(None, User_Query.QueryType.clarify)]

    def task_manager_information(self, course):
        print("We here")
        tm_courses = TaskManager.query_courses(course)
        print("We done")
        if tm_courses:
            if len(tm_courses) == 1:
                return tm_courses
            else:
                return tm_courses[0]
        if not tm_courses:
            return [User_Query.UserQuery(None, User_Query.QueryType.clarify)]
            # @params course to add to student classes
            # @return 0 for added successfully, 1 for not added

    def task_manager_keyword(self, keywords):
        tm_courses = TaskManager.smart_department_search(keywords)
        if tm_courses:
            return tm_courses
        if not tm_courses:
            return self.decision_tree.get_next_node(2)


    def task_manager_department_match(self, dept):
        tm_department = TaskManager.deparment_match(dept)
        if tm_department:
            return tm_department
        if not tm_department:
            return self.decision_tree.get_next_node(2)

    def task_manager_class_title_match(self, class_string, department = None):
        tm_class_match = TaskManager.query_by_title(class_string, department)
        if tm_class_match:
            return tm_class_match
        if not tm_class_match:
            return self.decision_tree.get_next_node(2)

    def schedule_course(self, new_course):
        for course in self.student_profile.previous_classes:
            if new_course.id == course.id:
                return course
        for course in self.student_profile.current_classes:
            if new_course.id == course.id:
                return course
        else:
            self.student_profile.current_classes.append(new_course)
            return new_course


            # @return location in student to store information / check if information is stored
            # @params information (entity) that we are looking to store

    def add_to_student(self, new_course, type):
        for course in self.student_profile.previous_classes:
            if new_course.id == course.id:
                return course
        for course in self.student_profile.current_classes:
            if new_course.id == course.id:
                return course
        else:
            self.student_profile.current_classes.append(new_course)
            return new_course
