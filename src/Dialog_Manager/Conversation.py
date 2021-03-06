"""
 Conversation.py
 Dialog Management functionality, interfacing between NLUU and Task Manager

"""


import re
from src.NLUU import nluu
from src.Task_Manager import TaskManager
from src.Dialog_Manager import Student, Course, User_Query, DecisionTree
import datetime
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from copy import deepcopy
import src.utils.debug as debug
import pprint
import time


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

    def __init__(self, luis_url, debug=False):
        """
        Initializes Conversation object.

        :param luis_url: url to connect to luis. Used in NLUU for analysis
        :param debug: flag to see if printed output should be actually printed
        """
        self.student_profile = Student.Student()
        self.student_profile.current_class = Course.Course()
        self.last_query = 0
        self.last_user_query = []
        self.head_node = DecisionTree.NodeObject(User_Query.UserQuery(None, User_Query.QueryType.welcome), [], [])
        self.current_node = self.head_node
        self.current_class = Course.Course()
        self.decision_tree = DecisionTree.DecisionTree(self.student_profile, debug)
        self.queries = []
        self.conversing = False
        self.nluu = nluu.nLUU(luis_url)
        self.utterancesStack = []
        self.mapOfIntents = {}
        self.sentimentAnalyzer = SentimentIntensityAnalyzer()
        self.debug = debug
        self.pretty_print = pprint.PrettyPrinter(indent=4)
        TaskManager.init(debug)

    def welcome(self, debug=False):
        self.conversing = True
        self.debug = debug
        our_response = [self.get_current_node()[0],
                        User_Query.UserQuery(self.student_profile, User_Query.QueryType.student_info_name)]
        our_str_response = self.nluu.create_response(our_response[0].type) + "\n" + self.nluu.create_response(
            our_response[1])
        self.utterancesStack.append(our_response)
        print("-" * 100)
        toPrint = our_str_response
        toPrint = toPrint.encode("ascii", "ignore")
        toPrint = toPrint.decode("ascii")
        spaces = " " * (100 - len(toPrint))
        print(spaces + toPrint)
        time.sleep(1)
        self.start_conversation(debug)

    def start_conversation(self, debug=False):
        """
        Starts the conversation with client. Pushes interactions onto stack of utterances that can be looked at down
        the road of the conversation in order to contextualize generic utterances. Passes client utterances on to
        handle functions based on intent/context and prints a string response from NLUU based on what is returned from
        handle function.

        :param debug: Debug for printing
        """
        while self.conversing:
            client_response = input()
            #print('\n')
            #If they only input a space, wait for another input.
            if client_response.isspace():
                continue
            #Let's see if they're done with us.
            if "goodbye" in client_response.lower() or " bye" in (" " + client_response.lower()):
                print("Smell ya later! Thanks for chatting.")
                break
            #Also checks for empty strings.
            if client_response != "" and client_response != "\n":
                luis_analysis = self.nluu.get_luis(client_response)
                self.utterancesStack.append(luis_analysis)
                userQueries = self.get_next_response(client_response, luis_analysis) or User_Query.UserQuery(
                    self.student_profile,
                    User_Query.QueryType.clarify)  # tuple containing response type as first argument, and data to format for other arguments
                self.call_debug_print("luis: {}".format(luis_analysis))
                our_str_response = ""
                if type(userQueries) is list:
                    #Go through each userQuery and formulate a response
                    for userQuery in userQueries:
                        ###
                        #Special case if they just registered for a class and past 18 credits
                        if User_Query.QueryType.full_schedule_check == userQuery.type:
                            our_str_response += self.nluu.create_response(userQuery) + '\n'
                            print(our_str_response)
                            self.check_full_schedule(debug)
                        else:
                            self.utterancesStack.append(userQuery)
                            self.last_user_query.append(userQuery)
                            if userQuery.type == User_Query.QueryType.goodbye:
                                print("Goodbye")
                                self.conversing = False
                                break
                            print("-" * 100)
                            toPrint = self.nluu.create_response(userQuery)
                            toPrint = toPrint.encode("ascii", "ignore")
                            toPrint = toPrint.decode("ascii")
                            spaces = " " * (100 - len(toPrint))
                            print(spaces + toPrint)
                            time.sleep(1)
                    # This mess of code stops descriptions with accents from
                    # throwing an error
                    our_str_response = our_str_response.encode("ascii", "ignore")
                    our_str_response = our_str_response.decode("ascii")

                else:
                    self.utterancesStack.append(userQueries)
                    self.last_user_query.append(userQueries)
                    self.call_debug_print("userQuery: {}".format(userQueries.type))
                    if userQueries.type == User_Query.QueryType.goodbye:
                        print("Goodbye")
                        self.conversing = False
                        break
                    our_str_response += self.nluu.create_response(userQueries) + '\n'
                    spaces = " " * (100 - len(our_str_response) + 1)
                    our_str_response = spaces + our_str_response
                    print("-" * 100)
                    print(our_str_response)
        exit()

    def check_full_schedule(self, debug=False):
        responseToCredits = input()
        responseSentiment = self.sentimentAnalyzer.polarity_scores(responseToCredits)
        if responseSentiment["neg"] > responseSentiment["pos"] or "bye" in responseToCredits:
            print("Smell ya later! Thanks for chatting.")
            self.conversing = False
            self.start_conversation(debug)
        elif responseSentiment["pos"] > responseSentiment["neu"]:
            self.start_conversation(debug)
        elif responseSentiment["neu"] > responseSentiment["pos"]:
            luis_analysis = self.nluu.get_luis(responseToCredits)
            self.utterancesStack.append(luis_analysis)
            uQs = self.get_next_response(responseToCredits,
                                         luis_analysis) or User_Query.UserQuery(self.student_profile,
                                                                                User_Query.QueryType.clarify)[0]
            for uQ in uQs:
                print("-" * 100)
                toPrint = self.nluu.create_response(uQ)
                toPrint = toPrint.encode("ascii", "ignore")
                toPrint = toPrint.decode("ascii")
                spaces = " " * (100 - len(toPrint))
                print(spaces + toPrint)
                time.sleep(1)
                if uQ.type == User_Query.QueryType.goodbye:
                    print("Goodbye")
                    self.conversing = False
                    self.start_conversation(debug)
                time.sleep(1)
            self.start_conversation(debug)

    # @params
    # @return
    def classify_intent(self, luis_input):
        """
        Takes highest non-None intent so long as it is above a threshold of 0.15.
        :param luis_input:
        :return: intent
        """
        if luis_input.intents[0] == "None" and luis_input.intents[0].score > .5:
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

    #Returns the current node of the decision tree
    def get_current_node(self):
        return [User_Query.UserQuery(self.student_profile, self.current_node.userQuery)]

    #Checks for a concentration, adds it to the list of concentrations, and then moves on
    def handleStudentConcentration(self, input, luisAI, luis_intent, luis_entities, unsure=False):
        if "no" in luisAI.query:
            return [self.decision_tree.get_next_node()]
        depts = self.getDepartmentStringFromLuis(input, luisAI, luis_intent, luis_entities, unsure, False)
        for dept in depts:
            self.student_profile.concentration.add(dept)
        return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.student_info_concentration_res), self.decision_tree.get_next_node()]

    def handleStudentMajorRequest(self, input, luisAI, luis_intent, luis_entities, unsure=False):
        """
        takes the Luis query, and lowers any word in the sequence so long as
        the word isn't I. NLTK will be able to recognize the majors as nouns if
        they are lowercase, but will also think i is a noun. Therefore, to
        prevent problems in the common case, we check for the presence of I.
        sidenote: we collect proper nouns "NNP" along with nouns "NN" down below...

        """
        if unsure:
            self.student_profile.major = set(["undeclared"])
            self.student_profile.concentration = set(["undeclared"])
            self.student_profile.major_classes_needed = ["N/A"]
            return [self.decision_tree.get_next_node()]
        if "not" in luisAI.query:
            return self.handleRemoveMajor(input, luisAI, luis_intent, luis_entities)
        if "concentrat" in luisAI.query:
            return self.handleStudentConcentration(input, luisAI, luis_intent, luis_entities)
        major_list = self.getDepartmentStringFromLuis(input, luisAI, luis_intent, luis_entities, False, True)
        self.call_debug_print("major: " + str(major_list))
        if len(luis_entities) == 0 and len(major_list) == 0:
            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.student_info_major_res),
                    self.decision_tree.get_next_node()]
        for major in major_list:
            if type(major) == type([]):
                for m in major:
                    if len(self.student_profile.major) < 2 and not m is None:
                        self.student_profile.major.add(m.title())
            else:
                if len(self.student_profile.major) < 2 and not major is None:
                    self.student_profile.major.add(major.title())
        return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.student_info_major_res),
                self.decision_tree.get_next_node()]

    def handleRemoveMajor(self, input, luisAI, luis_intent, luis_entities, unsure=False):
        # removes a major
        relevant_major = deepcopy(self.student_profile.major)
        major_list = self.getDepartmentStringFromLuis(input, luisAI, luis_intent, luis_entities)
        self.call_debug_print(major_list)
        if luis_entities:
            if format(luis_intent) != "student_info_concentration":
                for entity in luis_entities:
                    if entity.type == "department":
                        dept = self.task_manager_major_match(entity.entity)
                        if dept in relevant_major:
                            try:
                                self.student_profile.major.remove(dept)
                            except KeyError:
                                pass
                        else:
                            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.tm_clarify)]
            else:
                for entity in luis_entities:
                    if entity.type == "department":
                        dept = self.task_manager_concentration_match(entity.entity)
                        if dept in relevant_major:
                            try:
                                self.student_profile.concentration.remove(dept)
                            except KeyError:
                                pass
                        else:
                            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.tm_clarify)]
        else:
            for major in major_list:
                if major in relevant_major:
                    try:
                        self.student_profile.major.remove(major)
                    except KeyError:
                        pass
        return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.student_info_major_res),
                self.decision_tree.get_next_node()]

    def getDepartmentStringFromLuis(self, input, luisAI, luis_intent, luis_entities, unsure=False, is_major=True):
        # takes the Luis query, and lowers any word in the sequence so long as
        # the word isn't I. NLTK will be able to recognize the majors as nouns if
        # they are lowercase, but will also think i is a noun. Therefore, to
        # prevent problems in the common case, we check for the presence of I.
        # sidenote: we collect proper nouns "NNP" along with nouns "NN" down below...
        # tokenizes the query that has been adjusted by the code above
        # returns a list
        pot_query = luisAI.query.lower()
        dept = []
        double = False
        pot_query = re.sub("i ", " ", pot_query)
        pot_query = re.sub("wom[ae]n.*gender (studies)?", "wgst", pot_query)
        pot_query = re.sub("cinema.*media (studies)?", "cams", pot_query)
        pot_query = re.sub("french.*francophone (studies)?", "fren", pot_query)
        if "and" in pot_query:
            double = True
        else:
            double = False
        if is_major:
            if double:
                majors = pot_query.split("and")
                self.call_debug_print("major split: " + str(majors))
                for maj in majors:
                    maj_string = " ".join(self.nluu.find_departments(maj))
                    dept.append(self.task_manager_major_match(maj_string))
            else:
                major = self.nluu.find_departments(pot_query)
                self.call_debug_print("single major: " + str(major))
                major_string = " ".join(major)
                dept.append(self.task_manager_major_match(major_string))
            return dept
        else:
            if double:
                majors = pot_query.split("and")
                self.call_debug_print("major split: " + str(majors))
                for maj in majors:
                    maj_string = " ".join(self.nluu.find_departments(maj))
                    dept.append(self.task_manager_concentration_match(maj_string))
            else:
                major = self.nluu.find_departments(pot_query)
                self.call_debug_print("single major: " + str(major))
                major_string = " ".join(major)
                dept.append(self.task_manager_concentration_match(major_string))
            return dept

    def handleStudentMajorResponse(self, input, luisAI, luis_intent, luis_entities, unsure=False):
        return self.handleStudentMajorRequest(input, luisAI, luis_intent, luis_entities)

    #Schedules a class if they ask for it and they aren't already registered for the class
    #Checks Luis, if Luis doesn't have anything as a course entity try to find it ourself
    #Also handles DEPT123 format using a database query for department
    #Once we think we have a class, we send it over to the TM and get them to return a course
    #Which we then add to our current courses in student
    #And tell them what classes they've signed up for.
    def handleScheduleClass(self, input, luisAI, luis_intent, luis_entities, unsure=False):
        index = self.nluu.get_number_from_ordinal_str(input)
        tm_courses = None
        if self.student_profile.potential_courses is not None and len(self.student_profile.potential_courses) != 0:
            if index is not None:
                index = index - 1 if index != float('inf') else len(self.student_profile.potential_courses) - 1
                if index < len(self.student_profile.potential_courses):
                    tm_courses = [self.student_profile.potential_courses[index]]

        tm_courses = tm_courses or self.getCoursesFromLuis(input, luisAI, luis_intent, luis_entities, specific=True)
        if tm_courses is None:
            if re.search("(\d{3})", input):
                num = re.search("(\d{3})", input).group(0)
                tm_course = None
                for course in self.student_profile.potential_courses:
                    if course.course_num == num:
                        tm_course = course
                        break
                if tm_course is not None:
                    tm_courses = [tm_course]
            elif len(self.student_profile.potential_courses) == 1:
                tm_courses = [self.student_profile.potential_courses[0]]
        if tm_courses is None:
            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.tm_course_clarify)]
        tm_course = tm_courses[0]
        if tm_course is None:
            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.tm_course_clarify)]
        if tm_course in self.student_profile.current_classes:
            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.schedule_class_res),
                    self.decision_tree.get_next_node()]
            #return [self.decision_tree.get_next_node()]
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
        #return [self.decision_tree.get_next_node()]


    '''First off, we check for if you actually meant to check your classes, and handle that
    Then we take their request and search for courses that match
    And then return some and add them to potential courses so we can reference them later
    Also this is weighted for your major and student year
    '''
    def handleClassDescriptionRequest(self, input, luisAI, luis_intent, luis_entities, unsure=False):
        self.call_debug_print("hello" + input)
        if self.nluu.get_history(input):
            self.call_debug_print("hey")
            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.schedule_class_res), User_Query.UserQuery(self.student_profile, self.decision_tree.current_node.userQuery)]
        if unsure:
            course = Course.Course()
            if self.student_profile.major != ["undeclared"]:
                course.department = list(self.student_profile.major)[0]
                if self.student_profile.terms_left >= 9:  # frosh
                    course.course_num = ["100", "200"]
                else:
                    course.course_num = ["200", "300"]
                courses = self.task_manager_query_courses_by_level(course)
                if courses is not None and len(courses) > 0:
                    self.student_profile.potential_courses = courses
                    return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.new_class_description)
                        , self.decision_tree.get_next_node()]
            if self.student_profile.interests != set():
                tm_courses = self.task_manager_keyword(list(self.student_profile.interests))
                if tm_courses is not None and len(tm_courses) > 0:
                    self.student_profile.potential_courses = tm_courses
                    return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.new_class_description)
                        , self.decision_tree.get_next_node()]
            else:
                return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.already_talked_about)]
        if "interest" in input:
            return self.handleStudentInterests(input, luisAI, luis_intent, luis_entities)
        tm_courses = self.getCoursesFromLuis(input, luisAI, luis_intent, luis_entities)
        if tm_courses is None:
            return self.handleStudentInterests(input, luisAI, luis_intent,
                                               luis_entities)  # if we do not get a course back, lets try interests?
        else:
            self.student_profile.potential_courses = tm_courses
            self.student_profile.current_class, self.decision_tree.current_course = tm_courses[0], tm_courses[0]
            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.new_class_description)
                , self.decision_tree.get_next_node()]

    #figures out what year the player is and sets that info, then gets next node
    #currently dependent on current year and month if you give a year (ie 2017)
    #Also sets major if you're too young to have one.
    def handleStudentInfoYear(self, input, luisAI, luis_intent, luis_entities, unsure=False):
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
            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.student_info_time_left_res),
                    self.decision_tree.get_next_node()]
        else:
            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.clarify)]

    #Deals with it if you want to tell us your name
    #We don't really care what your name is though, we don't use it much at all
    #So if we don't get it, ¯\_(ツ)_/¯
    def handleStudentNameInfo(self, input, luisAI, luis_intent, luis_entities, unsure=False):
        if len(luis_entities) == 0:
            name = self.nluu.find_name(luisAI.query)
            self.student_profile.name = name
            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.student_info_name_res),
                    self.decision_tree.get_next_node()]

        for entity in luis_entities:
            if entity.type == "personname":
                self.student_profile.name = entity.entity
        if self.student_profile.name:
            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.student_info_name_res),
                    self.decision_tree.get_next_node()]

        else:
            return [self.decision_tree.get_next_node()]

    #"I said Hey, What's your name." - Avril Lavinge
    def handleWelcomeResponse(self, input, luisAI, luis_intent, luis_entities, unsure=False):
        return [self.decision_tree.get_next_node()]


    def handleClassDescriptionResponse(self, input, luisAI, luis_intent, luis_entities, unsure=False):
        return handleClassDescriptionRequest(input, luisAI, luis_intent, luis_entities, unsure=False)

    def handleClassProfessorRequest(self, input, luisAI, luis_intent, luis_entities, unsure=False):
        return self.handleClassProfessorResponse(input, luisAI, luis_intent, luis_entities)


    #Not trained on, we don't use this yet
    def handleClassProfessorResponse(self, input, luisAI, luis_intent, luis_entities, unsure=False):
        tm_courses = self.getCoursesFromLuis(input, luisAI, luis_intent, luis_entities)
        if tm_courses is None:
            return [self.decision_tree.get_next_node()]
        else:
            self.student_profile.current_classes.append(tm_courses[0])
            return [self.decision_tree.get_next_node()]


    def handleStudentRequirementResponse(self, input, luisAI, luis_intent, luis_entities, unsure=False):
        return [self.decision_tree.get_next_node]

    #Not implemented
    def handleClassTimeRequest(self, input, luisAI, luis_intent, luis_entities, unsure=False):
        course = Course.Course()
        self.task_manager_information(course)
        return [self.decision_tree.get_next_node()]

    def handleClassTermResponse(self, input, luisAI, luis_intent, luis_entities, unsure=False):
        return [self.decision_tree.get_next_node()]

    def handleClassTermRequest(self, input, luisAI, luis_intent, luis_entities, unsure=False):
        return [self.decision_tree.get_next_node()]

    #Takes in a student interest request
    #Uses Luis first, then uses out own guess about interests.
    #Adds those courses to potential courses and prints them out.
    def handleStudentInterests(self, input, luisAI, luis_intent, luis_entities, unsure=False):
        if unsure:
            return [self.decision_tree.get_next_node()]
            # if len(luis_entities) < 10:
        i = 0
        interests = self.nluu.find_interests(luisAI.query)
        if len(interests) == 0:
            interests = list(self.student_profile.interests) if self.student_profile.interests is not None else []
        new_interests = []
        for interest in interests:
            if "interest" in interest or "class" in interest:
                pass
            else:
                self.call_debug_print(interest)
                new_interests.append(interest)
                self.student_profile.interests.add(interest)
        interests = new_interests
        try:
            self.call_debug_print(interests)
            tm_courses = self.task_manager_keyword(interests)
            if tm_courses != None:
                self.student_profile.potential_courses = tm_courses
                return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.student_info_interests_res),
                    self.decision_tree.get_next_node()]
            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.tm_clarify)]
        except:
            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.tm_clarify)]

    def handleUnregisterRequest(self, input, luisAI, luis_intent, luis_entities, unsure=False):
        """
        Handler for unregistration. Queries against database on input to find course they wish to
        unregister for and removes it from the student_profile's current courses
        :param input: string raw input
        :param luisAI: luis analysis of input
        :param luis_intent: luis intents
        :param luis_entities: luis entities
        :param unsure: if response to question was unsure
        :return: returns list of UserQuery's
        """
        tm_courses = self.getCoursesFromLuis(input, luisAI, luis_intent, luis_entities, specific=True)
        if not tm_courses is None and len(tm_courses) > 0:  # We got returned a list
            for tm_course in tm_courses:
                for stud_course in self.student_profile.current_classes:
                    if tm_course == stud_course:
                        try:
                            self.student_profile.current_classes.remove(stud_course)
                            self.student_profile.current_credits -= tm_course.credits
                            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.schedule_class_res), User_Query.UserQuery(self.student_profile, self.decision_tree.current_node.userQuery)]
                        except:
                            pass
            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.schedule_class_res), User_Query.UserQuery(self.student_profile, self.decision_tree.current_node.userQuery)]
        if tm_courses is None:
            to_remove = self.student_profile.relevant_class
            if to_remove in self.student_profile.current_classes:
                self.student_profile.current_classes.remove(self.student_profile.relevant_class)
                self.student_profile.current_credits -= self.student_profile.relevant_class.credits
            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.schedule_class_res), User_Query.UserQuery(self.student_profile, self.decision_tree.current_node.userQuery)]
        else:
            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.tm_clarify)]

    def handleClassDistribution(self, input, luisAI, luis_intent, luis_entities, unsure=False):
        # occurs when the user wants to get courses that satisfy a given distribution
        # returns a list of courses that all satisfy the distribution
        if luis_entities:
            return self.handle_student_info_requirements(input, luisAI, luis_intent, luis_entities, unsure=False)
        else:
            return self.handle_student_info_major_requirements(input, luisAI, luis_intent, luis_entities, unsure=False)


    def handleUncertainResponse(self, input, luisAI, luis_intent, luis_entities):
        """
        If the response from the user was unsure (eg. 'Im not sure', 'I dont know') , we want to look at what we asked them, and then call their handle
        function with the flag unsure=True.

        Uses an eval to pattern-match with functions defined in this file.

        :param input: string raw input
        :param luisAI: luis analysis of input
        :param luis_intent: luis intents
        :param luis_entities: luis entities
        :param unsure: if response to question was unsure
        :return: returns whatever the function called returns
        """
        new_intent = format(self.decision_tree.current_node.userQuery).split(".")[1]
        self.call_debug_print(new_intent)
        eval_fn = None
        try:
            eval_fn = eval("self.handle_{}".format(new_intent))
        except:
            eval_fn = None
        if eval_fn:
            self.call_debug_print("We out here in unsure shit")
            return eval_fn(input, luisAI, format(new_intent), luis_entities, unsure=True)
        else:
            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.clarify)]


    #We ask a yes/no question. If we get a yes no response we deal with it here using Vader.
    #Then calls the handleClassDistro function to deal with it for us.
    def handle_class_info_distributions(self, input, luisAI, luis_intent, luis_entities, unsure=False):
        self.call_debug_print("hey there!")
        responseSentiment = self.sentimentAnalyzer.polarity_scores(input)
        if responseSentiment["neg"] > responseSentiment["pos"]:
            self.call_debug_print("We don't need no distributions")
            return [self.decision_tree.get_next_node]
        self.call_debug_print("we need some distros")
        return self.handleClassDistribution(input, luisAI, luis_intent, luis_entities)

    def handle_student_info_requirements_res(self, input, luisAI, luis_intent, luis_entities, unsure=False):
        return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.schedule_class_res)]

    def handle_student_info_name(self, input, luisAI, luis_intent, luis_entities, unsure=False):  # 10
        return self.handleStudentNameInfo(input, luisAI, luis_intent, luis_entities, unsure)

    def handle_student_info_major(self, input, luisAI, luis_intent, luis_entities, unsure=False):  # 11
        return self.handleStudentMajorRequest(input, luisAI, luis_intent, luis_entities, unsure)

    def handle_student_info_interests(self, input, luisAI, luis_intent, luis_entities, unsure=False):  # 13
        return self.handleStudentInterests(input, luisAI, luis_intent, luis_entities, unsure)

    def handle_student_info_time_left(self, input, luisAI, luis_intent, luis_entities, unsure=False):  # 14
        return self.handleStudentInfoYear(input, luisAI, luis_intent, luis_entities, unsure)
        # return self.decision_tree.get_next_node()

    #Deals with when they need to fulfill a requirement.
    #Here we figure out if its a major requirement or a general requirement.
    #Also checks if they want what classes they've registered for, because some phrasings end up in this intent.
    def handleStudentRequirementRequest(self, input, luisAI, luis_intent, luis_entities, unsure=False):
        self.call_debug_print("ayyyyy")
        if self.nluu.get_history(input):
            self.call_debug_print("hey")
            return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.schedule_class_res), User_Query.UserQuery(self.student_profile, self.decision_tree.current_node.userQuery)]
        if len(self.last_user_query) > 0:
            if self.last_user_query[-1].type.name == "student_info_major_requirements":
                return self.handle_student_info_major_requirements(input, luisAI, luis_intent, luis_entities)
            else:
                return self.handle_student_info_requirements(input, luisAI, luis_intent, luis_entities)
        else:
            return self.handle_student_info_requirements(input, luisAI, luis_intent, luis_entities)

    #checks what distros they still need
    #Could be none, so we deal with that.
    #We rely on Luis to figure out the distro because they are so different in terms of PoS
    #Then we use the TM to get us courses.
    def handle_student_info_requirements(self, input, luisAI, luis_intent, luis_entities, unsure=False):  # 16
        if unsure:
            return self.decision_tree.get_next_node()
        self.call_debug_print(luisAI.query)
        if "nothing" in luisAI.query or "none" in luisAI.query or " no " in luisAI.query:
            self.call_debug_print("we bout to graduate boyz")
            self.decision_tree.current_node.answered = True
            return self.decision_tree.get_next_node()
        if luis_entities:
            for entity in luis_entities:
                self.call_debug_print("i still gotta finish up that " + entity.entity)
                if entity.type == "distribution":
                    distro = self.task_manager_distribution_match(entity.entity)
                    tm_distro = self.task_manager_query_courses_by_distribution(distro)
                    self.student_profile.distributions_needed.append(distro) #add the text to gen distros
                    self.student_profile.distro_courses[distro] = tm_distro #add returned courses to last talked about courses
                    self.student_profile.potential_courses = tm_distro
            if len(self.student_profile.distributions_needed) != 0:
                return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.student_info_requirements_res),
                        self.decision_tree.get_next_node()]
            else:
                return self.handle_student_info_major_requirements(input, luisAI, luis_intent, luis_entities,
                                                                   unsure=False)

        else:
            return self.handle_student_info_major_requirements(input, luisAI, luis_intent, luis_entities, unsure=False)

    #Searches for the course they talk about when they say they need to complete something for their major.
    #Based on their year and major
    def handle_student_info_major_requirements(self, input, luisAI, luis_intent, luis_entities, unsure=False):  # 17
        if unsure:
            course = Course.Course()
            if self.student_profile.major and self.student_profile.major != "Undecided":
                course.department = list(self.student_profile.major)[0]
                if self.student_profile.terms_left > 6:
                    course.course_num = ["100", "200"]
                    some_courses = self.task_manager_query_courses_by_level(course)
                else:
                    course.course_num = ["200", "300"]
                    some_courses = self.task_manager_query_courses_by_level(course)

            else:
                course.department = list(self.student_profile.major)[0]
                if self.student_profile.terms_left > 6:
                    course.course_num = ["100", "200"]
                    some_courses = self.task_manager_query_courses_by_level(course)

                else:
                    course.course_num = ["200", "300"]
                    some_courses = self.task_manager_query_courses_by_level(course)
            if some_courses is not None:
                self.student_profile.major_classes_needed.extend(some_courses[0:4])
                self.student_profile.potential_courses = some_courses[0:4]
            return [
                User_Query.UserQuery(self.student_profile, User_Query.QueryType.student_info_major_requirements_res),
                self.decision_tree.get_next_node()]

        if len(luisAI.query.split(" ")) < 2:
            responseSentiment = self.sentimentAnalyzer.polarity_scores(luisAI.query)
            if responseSentiment["neg"] > responseSentiment["pos"] or "nothing" in luisAI.query:
                return [self.decision_tree.get_next_node()]
        courses = self.getCoursesFromLuis(input, luisAI, luis_intent, luis_entities, specific=False, major=True)
        if courses is None:
            return [
                self.decision_tree.get_next_node()]  # bc if we don't get a course, lets assume there isn't one, greiss maximum and shit
        self.student_profile.major_classes_needed.extend(courses)
        self.student_profile.potential_courses = courses
        return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.student_info_major_requirements_res),
                self.decision_tree.get_next_node()]

    def handle_student_info_concentration(self, input, luisAI, luis_intent, luis_entities, unsure=False):  # 18
        return self.handleStudentConcentration(input, luisAI, luis_intent, luis_entities, unsure)

    def handle_class_info_name(self, input, luisAI, luis_intent, luis_entities, unsure=False):  # 20
        return self.handleClassDescriptionRequest(input, luisAI, luis_intent, luis_entities, unsure)

    def handle_class_info_prof(self, input, luisAI, luis_intent, luis_entities, unsure=False):  # 21
        return self.handleClassProfessorRequest(input, luisAI, luis_intent, luis_entities, unsure)

    def handle_new_class_name(self, input, luisAI, luis_intent, luis_entities, unsure=False):  # 30
        return self.handleClassDescriptionRequest(input, luisAI, luis_intent, luis_entities, unsure)


    #We haven't trained for this
    def handle_new_class_prof(self, input, luisAI, luis_intent, luis_entities, unsure=False):  # 31
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

    #searches for a class within a department
    def handle_new_class_dept(self, input, luisAI, luis_intent, luis_entities, unsure=False):  # 32
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

    def handle_new_class_requirements(self, input, luisAI, luis_intent, luis_entities, unsure=False):  # 34
        self.handleClassDescriptionRequest(input, luisAI, luis_intent, luis_entities, unsure)

    def handle_new_class_time(self, input, luisAI, luis_intent, luis_entities, unsure=False):  # 35
        self.handleClassDescriptionRequest(input, luisAI, luis_intent, luis_entities, unsure)

    def handle_new_class_description(self, input, luisAI, luis_intent, luis_entities, unsure=False):  # 36
        self.handleClassDescriptionRequest(input, luisAI, luis_intent, luis_entities, unsure)

    #Deals with a type of question we don't use anymore- yes or no questions for a recommendation
    def handle_new_class_request(self, input, luisAI, luis_intent, luis_entities, unsure=False):  # 37
        if " ok" in self.last_query or "sure" == self.last_query or "recommend" in self.last_query:
            self.call_debug_print("they have gotten to the point where they want a course from us")
            self.call_debug_print("Lets fix this later")
        if "no " in self.last_query or "I don" in self.last_query or "I've" in self.last_query or "know" in self.last_query or "I'm" in self.last_query:
            return [self.decision_tree.get_next_node()]
        return [self.decision_tree.get_next_node()]

        # @params

    # @return
    # Called every time we get an input
    # Uses intent and/or the current node to decide which function to call
    # and eventually returns a UserQuery list.
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
            self.call_debug_print(new_intent)
            eval_fn = None
            try:
                eval_fn = eval("self.handle_{}".format(new_intent))
            except:
                eval_fn = None
            if eval_fn:
                return eval_fn(input, luisAI, format(new_intent), luis_entities)
            else:
                return [User_Query.UserQuery(self.student_profile, User_Query.QueryType.clarify)]

    def getCoursesFromLuis(self, input, luisAI, luis_intent, luis_entities, specific=False, major=False):
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
            if major:  # so we can query on major requirements differently than other class requests
                major_interests = set()
                for w in self.nluu.find_interests(" ".join(self.student_profile.interests)):
                    major_interests.add(w)
                tm_courses = self.task_manager_keyword(possibilities)
                if tm_courses is None:
                    return None
                elif not type(tm_courses) is list:
                    toReturn = [tm_courses]
                else:
                    toReturn = tm_courses
            elif not specific:  # return to potential courses not relavent class (for class description)
                interests = set()
                for w in self.nluu.find_interests(" ".join(self.student_profile.interests)):
                    interests.add(w)
                tm_courses = self.task_manager_keyword(possibilities)
                if tm_courses is None:
                    return None
                elif not type(tm_courses) is list:
                    toReturn = [tm_courses]
                else:
                    toReturn = tm_courses
            elif specific:  # for schedule class
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
                if not type(tm_course) is list and tm_course is not None:
                    toReturn = [tm_course]
                elif tm_course is not None:
                    toReturn = tm_course
            if entity.type == "distribution":
                course.gen_distributions.append(entity.entity)
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
        # returns a list of classes
        self.call_debug_print("We here")
        tm_courses = TaskManager.query_courses(course)
        self.call_debug_print("We done")
        if type(tm_courses) is list:
            if len(tm_courses) > 0:
                if len(tm_courses) > 5:
                    tm_courses = tm_courses[0:5]
                return tm_courses
            else:
                return None
        else:
            return [tm_courses]

    def task_manager_keyword(self, keywords):
        # returns a list if classes based on a student object. Picks some of them and returns, stores the rest.
        stud = self.student_profile
        exclude = set(self.student_profile.potential_courses) if self.student_profile.potential_courses is not None \
            else set()
        tm_courses = TaskManager.query_by_keywords(keywords, exclude=exclude,
                                                   student_department=stud.major, student_interests=stud.interests)
        if type(tm_courses) is list:
            if len(tm_courses) > 0:
                if len(tm_courses) > 5:
                    tm_courses = tm_courses[0:5]
                return tm_courses
            else:
                if len(keywords) == 1:
                    tm_courses = TaskManager.query_by_title(keywords[0])
                    if len(tm_courses) > 0:
                        if len(tm_courses) > 5:
                            tm_courses = tm_courses[0:5]
                        return tm_courses
                    else:
                        return None
                elif len(keywords) > 1:
                    query_str = ""
                    for keyword in keywords:
                        query_str = query_str + keyword + ' '
                    query_str = query_str[:-1]
                    tm_courses = TaskManager.query_by_title(query_str)
                    if len(tm_courses) > 0:
                        if len(tm_courses) > 5:
                            tm_courses = tm_courses[0:5]
                        return tm_courses
                    else:
                        return None
                else:
                    return None
        else:
            return [tm_courses]
    #matches phrase to a department, returns a string.
    def task_manager_department_match(self, dept, majors=True):
        tm_department = TaskManager.department_match(dept)
        if type(tm_department) is list:
            if len(tm_department) > 0:
                return tm_department[0]
            else:
                return None
        else:
            return tm_department

    def task_manager_major_match(self, major):
        tm_major = TaskManager.major_match(major)
        return tm_major

    def task_manager_concentration_match(self, concentration):
        tm_concentration = TaskManager.concentration_match(concentration)
        return tm_concentration

    def task_manager_class_title_match(self, class_string, department=None):
        # returns a course object
        tm_class_match = TaskManager.query_by_title(class_string, department)
        if type(tm_class_match) is list:
            if len(tm_class_match) > 0:
                return tm_class_match[0]
            else:
                return None
        else:
            return tm_class_match

    def task_manager_distribution_match(self, distribution, dept=None):
        tm_distro = TaskManager.distro_match(distribution)
        return tm_distro

    def task_manager_query_courses_by_level(self, course):
        # given a course object with 100, 200, 300, returns courses in that department with that level
        tm_level = TaskManager.query_courses_by_level(course)
        if len(tm_level) > 0:
            if len(tm_level) > 5:
                tm_level = tm_level[0:4]
            return tm_level
        else:
            return None

    def task_manager_query_courses_by_distribution(self, distro, dept=None):
        # given a distributions, return courses that fulfil that distribution
        # also potentially uses student major and keywords to query on courses.
        tm_distro = self.task_manager_distribution_match(distro)
        if self.student_profile.major:
            major = list(self.student_profile.major)[0]
        else:
            major = None
        if dept != None:
            tm_department = TaskManager.department_match(dept)
            class_match = TaskManager.query_by_distribution(tm_distro, tm_department, list(self.student_profile.interests),
                                                            major)
        else:
            class_match = TaskManager.query_by_distribution(tm_distro, None, list(self.student_profile.interests),
                                                            major)
        if len(class_match) > 0:
            if len(class_match) > 5:
                class_match = class_match[0:4]
            return class_match
        else:
            return None


    def call_debug_print(self, ob):
        debug.debug_print(ob, self.debug)
