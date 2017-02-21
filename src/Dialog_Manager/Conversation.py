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
                    our_str_response = our_str_response.decode("ascii")
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
        depts = self.getDepartmentStringFromLuis(input, luisAI, luis_intent, luis_entities)
        for dept in depts:
            self.student_profile.concentration.add(dept)
        return [self.decision_tree.get_next_node()]


    def handleStudentMajorRequest(self, input, luisAI, luis_intent, luis_entities):
        # takes the Luis query, and lowers any word in the sequence so long as
        # the word isn't I. NLTK will be able to recognize the majors as nouns if
        # they are lowercase, but will also think i is a noun. Therefore, to
        # prevent problems in the common case, we check for the presence of I.
        # sidenote: we collect proper nouns "NNP" along with nouns "NN" down below...
        updated = False
        if luis_entities:
            for entity in luis_entities:
                if entity.type == "department":
                    tm_major = self.task_manager_department_match(entity.entity)
                    if tm_major is None:
                        return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.clarify)]
                    print("tm major: ", format(tm_major))
                    updated = True
                    self.student_profile.major.add(tm_major)
        if not updated:
            major_list = self.getDepartmentStringFromLuis(input, luisAI, luis_intent, luis_entities)
            print("major: ", major_list)
            for major in major_list:
                self.student_profile.major.add(major)
        return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.student_info_major_res),
                self.decision_tree.get_next_node()]


    def handleRemoveMajor(self, input, luisAI, luis_intent, luis_entities):
        # removes a major
        major_list = self.getDepartmentStringFromLuis(input, luisAI, luis_intent, luis_entities)
        for major in major_list:
            if major in self.student_profile.major:
                self.student_profile.major.remove(major)
        if luis_entities:
            if format(luis_intent) != "student_info_concentration":
                for entity in luis_entities:
                    if entity.type == "department":
                        if entity.entity in self.student_profile.major:
                            self.student_profile.major.remove(entity.entity)
                        else:
                            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.tm_clarify)]
            else:
                for entity in luis_entities:
                    if entity.type == "department":
                        if entity.entity in self.student_profile.major:
                            self.student_profile.concentration.remove(entity.entity)
                        else:
                            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.tm_clarify)]
        return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.student_info_major_res), self.decision_tree.get_next_node()]


    def getDepartmentStringFromLuis(self, input, luisAI, luis_intent, luis_entities):
        # takes the Luis query, and lowers any word in the sequence so long as
        # the word isn't I. NLTK will be able to recognize the majors as nouns if
        # they are lowercase, but will also think i is a noun. Therefore, to
        # prevent problems in the common case, we check for the presence of I.
        # sidenote: we collect proper nouns "NNP" along with nouns "NN" down below...
        # tokenizes the query that has been adjusted by the code above
        # returns a list
        pot_query = luisAI.query
        dept = []
        double = False
        if "and" in luisAI.query:
            if "women and gender" in pot_query:
                self.student_profile.major.add(self.task_manager_department_match("wgst"))
                pot_query = pot_query.replace("women and gender", "")
            elif "cinema and media" in pot_query:
                self.student_profile.major.add(self.task_manager_department_match("cams"))
                pot_query = pot_query.replace("cinema and media", "")

            else:
                double = True
        else:
            double = False
        if double:
            majors = luisAI.query.split("and")
            print("major split: ", majors)
            for maj in majors:
                dept.append(self.nluu.find_departments(maj))
        else:
            major = self.nluu.find_departments(pot_query)
            print("single major: " + str(major))
            for word in major:
                if word != "major" and word != "concentration" and word != "studies":
                    dept.append(self.task_manager_department_match(word))
        return dept


    def handleStudentMajorResponse(self, input, luisAI, luis_intent, luis_entities):
        return self.handleStudentMajorRequest(input, luisAI, luis_intent, luis_entities)

    def handleScheduleClass(self, input, luisAI, luis_intent, luis_entities):
        index = self.nluu.get_number_from_ordinal_str(input)
        tm_courses = None
        if len(self.student_profile.potential_courses) != 0 and index is not None:
            index = index - 1 if index != float('inf') else len(self.student_profile.potential_courses) - 1
            tm_courses = [self.student_profile.potential_courses[index]]
        tm_courses = tm_courses or self.getCoursesFromLuis(input, luisAI, luis_intent, luis_entities,specific=True)
        tm_courses = tm_courses or [self.student_profile.potential_courses[0]] if len(self.student_profile.potential_courses) > 0 else [None]
        if tm_courses[0] is None:
            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.tm_course_clarify)]
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

    def handleStudentInfoYear(self, input, luisAI, luis_intent, luis_entities):
        cur_term = "fall"
        if datetime.datetime.now().month < 4:
            cur_term = "winter"
        elif datetime.datetime.now().month < 9:
            cur_term = "spring"

        freshYear = str(datetime.datetime.now().year + 3)
        sophYear = str(datetime.datetime.now().year + 2)
        juniorYear = str(datetime.datetime.now().year + 1)
        seniorYear = str(datetime.datetime.now().year)
        query = luisAI.query.lower()
        updated = False
        if "fresh" in query or "frosh" in query or (freshYear[2:] + " ") in (
            query + " ") or "first" in query:
            updated = True
            self.student_profile.major.add("undeclared")
            self.student_profile.terms_left = 11
            if cur_term == "fall":
                self.student_profile.terms_left = 11
            elif cur_term == "winter":
                self.student_profile.terms_left = 10
        elif "soph" in query or "second" in query or (sophYear[2:] + " ") in (query + " "):
            updated = True
            self.student_profile.terms_left = 8
            if cur_term == "fall":
                self.student_profile.terms_left = 7
                self.student_profile.major.add("undeclared")
            elif cur_term == "winter":
                self.student_profile.terms_left = 6
                self.student_profile.major.add("undeclared")

        elif "junior" in query or "third" in query or (juniorYear[2:] + " ") in (query + " "):
            updated = True
            self.student_profile.terms_left = 5
            if cur_term == "fall":
                self.student_profile.terms_left = 4
            elif cur_term == "winter":
                self.student_profile.terms_left = 3
        elif "senior" in query or "fourth" in query or seniorYear[2:] in query or "final" in query or "last" in query:
            updated = True
            self.student_profile.terms_left = 0
            if cur_term == "fall":
                self.student_profile.terms_left = 2
            elif cur_term == "winter":
                self.student_profile.terms_left = 1
        if updated:
            return [self.decision_tree.get_next_node()]
        else:
            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.clarify)]


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
        try:
            print(interests)
            tm_courses = self.task_manager_keyword(interests)
            if tm_courses is None or len(tm_courses) < 1:
                raise
            if set(self.student_profile.interests).issuperset(set(interests)): #need to implement no repeated courses
                print("in same length")
                self.student_profile.potential_courses = tm_courses
                return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.student_info_interests_res),self.decision_tree.get_next_node()]
            else:
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
            to_remove = self.student_profile.relevant_class
            if to_remove in self.student_profile.current_classes:
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

        return self.handleStudentInfoYear(input, luisAI, luis_intent, luis_entities)
        #return self.decision_tree.get_next_node()

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
        if len(self.last_query.split(" ")) < 2:
            responseSentiment = self.sentimentAnalyzer.polarity_scores(self.last_query)
            if responseSentiment["neg"] > responseSentiment["pos"] or "nothing" in self.last_query:
                return [self.decision_tree.get_next_node()]
            courses = self.getCoursesFromLuis(input, luisAI, luis_intent, luis_entities, specific=False)
            if courses is None or len(courses) == 0:
                return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.specify)]
            self.student_profile.major_classes_needed.extend(courses)
        if luis_entities:
            for entity in luis_entities:
                if entity.type == "class":
                    self.student_profile.major_classes_needed.append(Course.Course(entity.entity))
            if len(self.student_profile.major_classes_needed) != 0:
                return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.student_info_major_requirements_res), self.decision_tree.get_next_node()]
        if ',' in self.last_query:
            listOfWords = self.last_query.split(",")
            for word in listOfWords:
                if len(word.split()) < 4:
                    self.student_profile.major_classes_needed.append(Course.Course(word))
            if len(self.student_profile.major_classes_needed) != 0:
                return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.student_info_major_requirements_res), self.decision_tree.get_next_node()]
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
        self.handleClassDescriptionRequest(input, luisAI, luis_intent, luis_entities)

    def handle_new_class_time(self, input, luisAI, luis_intent, luis_entities):  # 35
        self.handleClassDescriptionRequest(input, luisAI, luis_intent, luis_entities)

    def handle_new_class_description(self, input, luisAI, luis_intent, luis_entities):  # 36
        self.handleClassDescriptionRequest(input, luisAI, luis_intent, luis_entities)

    def handle_new_class_request(self, input, luisAI, luis_intent, luis_entities):  # 37
        if " ok" in self.last_query or "sure" == self.last_query or "recommend" in self.last_query:
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
                tm_courses = self.task_manager_keyword(possibilities)
                if tm_courses is None:
                    return None
                elif not type(tm_courses) is list:
                    toReturn = [tm_courses]
                else:
                    toReturn = tm_courses
            if specific: #for schedule class
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
        #returns a list
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

    def task_manager_keyword(self, keywords):
        #returns a list
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
        #returns a course object
        tm_class_match = TaskManager.query_by_title(class_string, department)
        if type(tm_class_match) is list:
            if len(tm_class_match) > 0:
                return tm_class_match[0]
            else:
                return None
        else:
            return tm_class_match
