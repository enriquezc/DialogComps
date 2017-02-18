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
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer


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
        self.student_profile.current_class = Course.Course()
        self.last_query = 0
        self.last_user_query = []
        self.head_node = DecisionTree.NodeObject(User_Query.UserQuery(None, User_Query.QueryType.welcome), [], [])
        self.current_node = self.head_node
        self.current_class = Course.Course()
        self.decision_tree = DecisionTree.DecisionTree(self.student_profile)
        self.queries = []
        self.conversing = False
        self.nluu = nluu.nLUU(luis_url)
        self.utterancesStack = []
        self.mapOfIntents = {}
        self.sentimentAnalyzer = SentimentIntensityAnalyzer()

        TaskManager.init()

    def start_conversation(self):
        self.conversing = True
        our_response = [self.get_current_node()[0], User_Query.UserQuery(self.student_profile, User_Query.QueryType.student_info_name)]
        our_str_response = self.nluu.create_response(our_response[0].type) + "\n" + self.nluu.create_response(our_response[1])
        self.utterancesStack.append(our_response)
        print(our_str_response)
        while self.conversing:

            client_response = input()
            if "goodbye" in client_response.lower() or " bye" in (" " + client_response.lower()):
                print("Smell ya later! Thanks for chatting.")
                return
            if client_response != "" and client_response != "\n":
                luis_analysis = self.nluu.get_luis(client_response)
                self.utterancesStack.append(luis_analysis)
                userQueries = self.get_next_response(client_response, luis_analysis) or User_Query.UserQuery(self.student_profile, User_Query.QueryType.clarify) # tuple containing response type as first argument, and data to format for other arguments
                print("luis: {}".format(luis_analysis))
                our_str_response = ""
                if type(userQueries) is list:
                    for userQuery in userQueries:
                        ###
                        if User_Query.QueryType.full_schedule_check == userQuery.type:
                            print (self.nluu.create_response(userQuery) + '\n')
                            responseToCredits = input()

                            responseSentiment = self.sentimentAnalyzer.polarity_scores(responseToCredits)
                            if responseSentiment["neg"] > responseSentiment["pos"]:
                                print("Smell ya later! Thanks for chatting.")
                                return
                        else:

                        ###
                            self.utterancesStack.append(userQuery)
                            self.last_user_query.append(userQuery)
                            if userQuery.type == User_Query.QueryType.goodbye:
                                print("Goodbye")
                                self.conversing = False
                                break
                            our_str_response += self.nluu.create_response(userQuery) + '\n'
                    # This mess of code stops descriptions with accents from
                    # throwing an error
                    our_str_response = our_str_response.encode("ascii", "ignore")
                    our_str_response =  our_str_response.decode("ascii")
                    print(str(our_str_response))
                else:
                    self.utterancesStack.append(userQueries)
                    self.last_user_query.append(userQueries)
                    print("userQuery: {}".format(userQueries.type))
                    if userQueries.type == User_Query.QueryType.goodbye:
                        print("Goodbye")
                        self.conversing = False
                        break
                    our_str_response += self.nluu.create_response(userQueries) + '\n'
                    print(our_str_response)

    # @params
    # @return
    def classify_intent(self, luis_input):
        # input is a luis dictionary
        if luis_input.intents[0] == "None" and luis_input.intents[0].score > .6:
            return luis_input.intents[0]
        for intent in luis_input.intents:
            if intent.score >= .15 and intent.intent != "None":
                return intent.intent
            else:
                return luis_input.intents[0]
        return luis_input

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

    def handleStudentConcentration(self, input, luisAI, luis_intent, luis_entities):
        dept = self.getDepartmentStringFromLuis(input, luisAI, luis_intent, luis_entities)
        for dep in dept:
            if dep not in self.student_profile.concentration:
                self.student_profile.concentration.append(dept)
                return [self.decision_tree.get_next_node()]

    def handleStudentMajorRequest(self, input, luisAI, luis_intent, luis_entities):
        # takes the Luis query, and lowers any word in the sequence so long as
        # the word isn't I. NLTK will be able to recognize the majors as nouns if
        # they are lowercase, but will also think i is a noun. Therefore, to
        # prevent problems in the common case, we check for the presence of I.
        # sidenote: we collect proper nouns "NNP" along with nouns "NN" down below...
        if luis_entities:
            for entity in luis_entities:
                if entity.type == "department":
                    tm_major = self.task_manager_department_match(entity.entity)
                    print("tm major: ", format(tm_major))
                    self.student_profile.major.add(tm_major)
                else:
                    return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.tm_clarify)]

        major_list = self.getDepartmentStringFromLuis(input, luisAI, luis_intent, luis_entities)
        print("major: ", major_list)

        if major_list is None:  # making sure we actually query on something
            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.tm_clarify)]
        else:
            self.student_profile.major.add(major_string)
        return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.student_info_major_res),
                self.decision_tree.get_next_node()]

    def remove_concentration(self, input, luisAI, luis_intent, luis_entities):
        pass

    def handleRemoveMajor(self, input, luisAI, luis_intent, luis_entities):
        # removes a major
        major_string = self.getDepartmentStringFromLuis(input, luisAI, luis_intent, luis_entities)
        if luis_entities:
            if format(luis_intent) != "student_info_concentration":
                for entity in luis_entities:
                    if entity.type == "department":
                        try:
                            tm_major = TaskManager.department_match(entity.entity)
                            print("tm major: ", format(tm_major))
                            if tm_major in self.student_profile.major:
                                self.student_profile.major.remove(tm_major)
                        except:
                            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.tm_clarify)]

            else:
                for entity in luis_entities:
                    if entity.type == "department":
                            tm_major = TaskManager.department_match(entity.entity)
                            print("tm major: ", format(tm_major))
                            if tm_major in self.student_profile.concentration:
                                self.student_profile.concentration.remove(tm_major)
                            else:
                                return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.tm_clarify)]
        if format(luis_intent) != "student_info_concentration":
            if major_string != "":
                self.student_profile.major.remove(major)
                return [self.decision_tree.get_next_node()]
            else:
                return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.tm_clarify)]
        else:
            if major_string != "":
                if major_string in self.student_profile.concentration:
                    self.student_profile.concentration.remove(major)
                    return [self.decision_tree.get_next_node()]
            else:
                return [self.decision_tree.get_next_node()]

    def getDepartmentStringFromLuis(self, input, luisAI, luis_intent, luis_entities):
        # takes the Luis query, and lowers any word in the sequence so long as
        # the word isn't I. NLTK will be able to recognize the majors as nouns if
        # they are lowercase, but will also think i is a noun. Therefore, to
        # prevent problems in the common case, we check for the presence of I.
        # sidenote: we collect proper nouns "NNP" along with nouns "NN" down below...
        # tokenizes the query that has been adjusted by the code above
        # @return a list of departments from NLUU
        string = " "
        major_list = []
        dept = []
        major = self.nluu.find_departments(luisAI.query)
        for word in major:
            if word != "major" and word != "concentration":
                dept.append(TaskManager.department_match(word))
        return dept

    def handleStudentMajorResponse(self, input, luisAI, luis_intent, luis_entities):
        return self.handleStudentMajorRequest(input, luisAI, luis_intent, luis_entities)

    def handleScheduleClass(self, input, luisAI, luis_intent, luis_entities):
        tm_courses = self.getCoursesFromLuis(input, luisAI, luis_intent, luis_entities)
        if tm_courses is None:
            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.tm_course_clarify)]
        else:
            tm_course = tm_courses[0]
            if tm_course is None:
                return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.tm_course_clarify)]
            if tm_course in self.student_profile.current_classes:
                return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.schedule_class_res),
                        self.decision_tree.get_next_node()]
            self.student_profile.relevant_class = tm_course
            self.student_profile.current_classes.append(tm_course)
            newCredits = 6 if tm_course.credits is None else tm_course.credits
            self.student_profile.current_credits += newCredits
            self.student_profile.total_credits += newCredits
            if self.student_profile.current_credits >= 18:
                return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.full_schedule_check),
                        self.decision_tree.get_next_node()]
            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.schedule_class_res)
                    , self.decision_tree.get_next_node()]

    def handleClassDescriptionRequest(self, input, luisAI, luis_intent, luis_entities):
        if "interest" in input:
            return self.handleStudentInterests(input, luisAI, luis_intent, luis_entities)
        tm_courses = self.getCoursesFromLuis(input, luisAI, luis_intent, luis_entities)
        if tm_courses is None:
            return self.handleStudentInterests(input, luisAI, luis_intent, luis_entities) #if we do not get a course back, lets try interests?
        else:
            self.student_profile.potential_courses = tm_courses
            self.student_profile.current_class, self.decision_tree.current_course = tm_courses[0], tm_courses[0]
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
        return [self.decision_tree.get_next_node()]


    def handleClassDescriptionResponse(self, input, luisAI, luis_intent, luis_entities):
        course = Course.Course()
        self.task_manager_information(course)

    def handleClassProfessorRequest(self, input, luisAI, luis_intent, luis_entities):
        return self.handleClassProfessorResponse(input, luisAI, luis_intent, luis_entities)

    def handleClassProfessorResponse(self, input, luisAI, luis_intent, luis_entities):
        tm_courses = self.getCoursesFromLuis(input, luisAI, luis_intent, luis_entities)
        if tm_courses is None:
            return [self.decision_tree.get_next_node()]
        else:
            self.student_profile.current_classes.append(tm_courses[0])
            return [self.decision_tree.get_next_node()]

    def handleStudentRequirementRequest(self, input, luisAI, luis_intent, luis_entities):
        course = Course.Course()
        self.task_manager_information(course)
        return [self.decision_tree.get_next_node()]

    def handleStudentRequirementResponse(self, input, luisAI, luis_intent, luis_entities):
        course = Course.Course()
        self.task_manager_information(course)
        return [self.decision_tree.get_next_node()]


    # done
    def handleClassTimeResponse(self, input, luisAI, luis_intent, luis_entities):
        for entity in luis_entities:
            for course in self.student_profile.all_classes:
                if entity == course:
                    return [User_Query.UserQuery(course, User_Query.QueryType.class_info_description)]


    def handleClassTimeRequest(self, input, luisAI, luis_intent, luis_entities):
        course = Course.Course()
        self.task_manager_information(course)
        return [self.decision_tree.get_next_node()]

    def handleClassTermResponse(self, input, luisAI, luis_intent, luis_entities):
        return [self.decision_tree.get_next_node()]

    def handleClassTermRequest(self, input, luisAI, luis_intent, luis_entities):
        return [self.decision_tree.get_next_node()]

    # done
    def handleStudentInterests(self, input, luisAI, luis_intent, luis_entities):
        print("in interests")
        #if len(luis_entities) < 10:
        i = 0
        interests = self.nluu.find_interests(luisAI.query)
        new_interests = []
        for interest in interests:
            if "interest" in interest or "class" in interest:
                pass
            else:
                print(interest)
                new_interests.append(interest)
                self.student_profile.interests.add(interest)
        interests = new_interests

        '''else:
            interests = []
            for entity in luis_entities:
                print(entity)
                if entity.type == "class" or entity.type == "department" or entity.type == "sentiment":
                    interests.append(entity.entity)
                    self.student_profile.interests.add(entity.entity)'''
        try:
            print(interests)
            tm_courses = TaskManager.query_by_keywords(interests)[0:9]
            if set(self.student_profile.interests).issuperset(set(interests)): #need to implement no repeated courses
                print("in same length")
                self.student_profile.potential_courses = tm_courses
                return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.student_info_interests_res),self.decision_tree.get_next_node()]
            else:
                self.student_profile.all_classes.add(tm_courses)
                self.student_profile.potential_courses = tm_courses
                return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.student_info_interests_res),self.decision_tree.get_next_node()]
        except:
            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.tm_clarify)]


    def handleUnregisterRequest(self, input, luisAI, luis_intent, luis_entities):
        tm_courses = self.getCoursesFromLuis(input, luisAI, luis_intent, luis_entities)
        if not tm_courses is None and len(tm_courses) > 0: # We got returned a list
            for tm_course in tm_courses:
                for stud_course in self.student_profile.current_classes:
                    if tm_course == stud_course:
                        try:
                            self.student_profile.current_classes.remove(stud_course)
                        except:
                            pass
            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.schedule_class_res)]
        if tm_courses is None:
            self.student_profile.current_classes.remove(self.student_profile.relevant_class)
            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.schedule_class_res)]
        else:
            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.tm_clarify)]


    def handle_student_info_name(self, input, luisAI, luis_intent, luis_entities): #10
        return self.handleStudentNameInfo(input, luisAI, luis_intent, luis_entities)

    def handle_student_info_major(self, input, luisAI, luis_intent, luis_entities): #11
        return self.handleStudentMajorRequest(input, luisAI, luis_intent, luis_entities)

    def handle_student_info_interests(self, input, luisAI, luis_intent, luis_entities): #13
        return self.handleStudentInterests(input, luisAI, luis_intent, luis_entities)

    def handle_student_info_time_left(self, input, luisAI, luis_intent, luis_entities): #14
        cur_term = "fall"
        if datetime.now().month < 4:
            cur_term = "winter"
        elif datetime.now().month < 9:
            cur_term = "spring"
        freshYear = str(datetime.now().year + 3)
        sophYear = str(datetime.now().year + 2)
        juniorYear = str(datetime.now().year + 1)
        seniorYear = str(datetime.now().year)

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
            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.clarify)]
        return self.decision_tree.get_next_node()

    def handle_student_info_requirements(self, input, luisAI, luis_intent, luis_entities): #16
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

    def handle_student_info_major_requirements(self, input, luisAI, luis_intent, luis_entities):  # 17
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
        return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.clarify)]

    def handle_student_info_concentration(self, input, luisAI, luis_intent, luis_entities): #18
        return self.handleStudentConcentration(input, luisAI, luis_intent, luis_entities)

    def handle_class_info_name(self, input, luisAI, luis_intent, luis_entities): #20
        self.handleClassDescriptionRequest(input, luisAI, luis_intent, luis_entities)

    def handle_class_info_prof(self, input, luisAI, luis_intent, luis_entities):  # 21
        self.handleClassProfessorRequest(input, luisAI, luis_intent, luis_entities)


    def handle_new_class_name(self, input, luisAI, luis_intent, luis_entities):  # 30
        return self.handleClassDescriptionRequest(input, luisAI, luis_intent, luis_entities)

    def handle_new_class_prof(self, input, luisAI, luis_intent, luis_entities):  # 31
        if luis_entities:
            for entity in luis_entities:
                if entity.type == 'personname':
                    c = Course.Course()
                    c.faculty_name = entity.entity
                    self.student_profile.potential_courses.append(c)
                if self.student_profile.potential_courses != []:
                    return self.decision_tree.get_next_node()
        elif len(self.last_query.split()) < 3:
            c = Course.Course()
            c.faculty_name = self.last_query
            self.student_profile.potential_courses.append(c)
            return self.decision_tree.get_next_node()
        else:
            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.clarify)]

    def handle_new_class_dept(self, input, luisAI, luis_intent, luis_entities):  # 32
        if luis_entities:
            for entity in luis_entities:
                if entity.type == "department":
                    c = Course.Course()
                    c.department = entity.entity
                    self.student_profile.potential_courses.append(c)
            if self.student_profile.potential_courses != []:
                return [self.decision_tree.get_next_node()]
            else:
                return [self.decision_tree.get_next_node()]
        if len(self.last_query.split()) < 3:
            c = Course.Course()
            c.department = self.nluu.find_course(input)
            self.student_profile.potential_courses.append(c)
            return [self.decision_tree.get_next_node()]
        return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.clarify)]

    def handle_new_class_requirements(self, input, luisAI, luis_intent, luis_entities): #34
        pass

    def handle_new_class_time(self, input, luisAI, luis_intent, luis_entities):  # 35
        pass

    def handle_new_class_description(self, input, luisAI, luis_intent, luis_entities):  # 36
        self.handleClassDescriptionRequest(input, luisAI, luis_intent, luis_entities)

    def handle_new_class_request(self, input, luisAI, luis_intent, luis_entities):  # 37
        if " ok" in self.last_query or "sure" == self.last_query or "reccommend" in self.last_query:
            print("they have gotten to the point where they want a course from us")
            print("Lets fix this later")
        if "no " in self.last_query or "I don" in self.last_query or "I've" in self.last_query or "know" in self.last_query or "I'm" in self.last_query:
            return [self.decision_tree.get_next_node()]
        return [self.decision_tree.get_next_node()]

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
            new_intent = format(self.decision_tree.current_node.userQuery).split(".")[1]
            print(new_intent)
            eval_fn = None
            try:
                eval_fn = eval("self.handle_{}".format(new_intent))
            except:
                eval_fn = None
            if eval_fn:
                return eval_fn(input, luisAI, format(new_intent), luis_entities)
            else:
                return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.clarify)]



    def getCoursesFromLuis(self, input, luisAI, luis_intent, luis_entities, specific=True):
        """
        Helper function that is used for handleClassDescriptionRequest, handleRegisterClass(Course?), etc.
        that takes luis input and returns a list of courses using the TM in a centralized way.

        :param input:
        :param luisAI:
        :param luis_intent:
        :param luis_entities:
        :return None if no entities and no help from TM else list of courses that might be of interest:
        """
        toReturn = None
        if len(luis_entities) == 0:
            possibilities = self.nluu.find_course(luisAI.query)
            if len(possibilities) == 0:
                return None
            if not specific: #return to potential courses not relavent class (for class description)
                tm_courses = self.task_manager_keyword(possibilities)[0:4]  # type checked in tm keyword
                if tm_courses is None:
                    return None
                elif not type(tm_courses) is list:
                    toReturn = [tm_courses]
                else:
                    toReturn = tm_courses
            else: #for schedule class
                tm_courses = self.task_manager_class_title_match(possibilities)  # type checked in tm keyword
                if tm_courses is None:
                    return None
                elif not type(tm_courses) is list:
                    toReturn = [tm_courses]
                else:
                    toReturn = tm_courses
        for entity in luis_entities:
            course = Course.Course()
            if entity.type == 'class':
                course_name = re.search("([A-Za-z]{2,4}) ?(\d{3})", input)
                course.user_description = luisAI.query
                if course_name:
                    course.id = course_name.group(0)
                    course.course_num = course_name.group(2)
                    course.department = course_name.group(1)
                    tm_course = self.task_manager_information(course)
                    if tm_course is None:
                        return None
                    if not type(tm_course) is list:
                        toReturn = [tm_course]
                    else:
                        toReturn = tm_course
                else:
                    tm_course = self.task_manager_class_title_match(
                        entity.entity)  # type checking done in class title match
                    # should always return one class, if no classes, should have already returned tm_clarify
                    if tm_course is None:
                        return None
                    if not type(tm_course) is list:
                        toReturn = [tm_course]
                    else:
                        toReturn = tm_course

            if entity.type == "department":
                course.department = entity.entity
                tm_course = self.task_manager_information(course)  # type checking is done in tm informaiton
                if not type(tm_course) is list:
                    toReturn = [tm_course]
                else:
                    toReturn = tm_course
        if toReturn is None:
            return toReturn
        for course in toReturn:
            self.student_profile.all_classes.add(course)
        return toReturn


    def task_manager_information(self, course):
        print("We here")
        tm_courses = TaskManager.query_courses(course)
        print("We done")
        if type(tm_courses) is list:
            if len(tm_courses) > 0:
                return tm_courses
            else:
                return None
        else:
            return [tm_courses]

    # @params course to add to student classes
    # @return 0 for added successfully, 1 for not added
    def task_manager_keyword(self, keywords):
        tm_courses = TaskManager.query_by_keywords(keywords)
        if type(tm_courses) is list:
            if len(tm_courses) > 0:
                return tm_courses
            else:
                return None
        else:
            return [tm_courses]


    def task_manager_department_match(self, dept):
        tm_department = TaskManager.department_match(dept)
        if type(tm_department) is list:
            if len(tm_department) > 0:
                return tm_department[0]
            else:
                return None
        else:
            return tm_department

    def task_manager_class_title_match(self, class_string, department = None):
        tm_class_match = TaskManager.query_by_title(class_string, department)
        if type(tm_class_match) is list:
            if len(tm_class_match) > 0:
                return tm_class_match[0]
            else:
                return None
        else:
            return tm_class_match

    def remove_dupe_classes(self, courses):
        returned_courses = []
        for course in courses:
            if course not in self.student_profile.all_classes:
                returned_courses.append(course)
        return returned_courses

