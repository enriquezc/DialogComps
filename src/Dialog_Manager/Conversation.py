import queue
import re
import sys
from nltk.tree import Tree
from src.NLUU import nluu
import nltk
import luis
from src.Task_Manager import TaskManager
from src.Dialog_Manager import Student, Course, User_Query, DecisionTree


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
        self.head_node = DecisionTree.NodeObject(User_Query.UserQuery(None, User_Query.QueryType.welcome), [], [])
        self.current_node = self.head_node
        self.current_class = None
        self.decision_tree = DecisionTree.DecisionTree(self.student_profile)
        self.queries = []
        self.conversing = False
        self.nluu = nluu.nLUU(luis_url)
        TaskManager.init()

    def start_conversation(self):

        self.conversing = True
        our_str_response = "Hello young eager mind! What can I help you with?"
        while self.conversing:
            client_response = input(our_str_response + "\n")
            luis_analysis = self.nluu.get_luis(client_response)
            print("luis: {}".format(luis_analysis))
            userQuery = self.get_next_response(client_response, luis_analysis) # tuple containing response type as first argument, and data to format for other arguments
            print("userQuery: {}".format(userQuery))
            if userQuery.type == User_Query.QueryType.goodbye:
                print("Goodbye")
                self.conversing = False
                break
            our_str_response = self.nluu.create_response(userQuery)

    # @params
    # @return
    def classify_intent(self, luis_input):
        # input is a luis dictionary
        if luis_input.intents[0].score >= .5:
            return luis_input.intents[0].intent
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

    # @params
    # @return
    def get_next_response(self, input, luisAI):
        self.last_query = input
        luis_entities = luisAI.entities
        luis_intent = self.classify_intent(luisAI)
        print(luis_intent)
        for entity in luis_entities:
            print(entity)
        if luis_entities:
            self.queries.append(input)
            # print(luis_intent)
            # print(luisAI.query)
            # entity_information = self.task_manager_information(luis_entities)
            # done
            if luis_intent == "StudentMajorRequest":
                for entity in luis_entities:
                    if entity.type == "u'DEPARTMENT":
                        for major in self.student_profile.major:
                            if entity.entity == major or len(self.student_profile.major) == 2:
                                pass
                            else:
                                self.student_profile.major.append(entity.entity)
                return User_Query.UserQuery(self.student_profile, User_Query.QueryType.pleasantry)

            # done for now
            if luis_intent == "ScheduleClass":
                # if entity.type == "class":  # add more if's for different types
                course = Course.Course()
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
                        self.student_profile.relevant_class = tm_courses
                        self.student_profile.current_classes.append(tm_courses)
                        self.student_profile.current_credits =+ 6
                        self.student_profile.total_credits += tm_courses.credits
                        print(self.student_profile.current_credits)
                        if self.student_profile.current_credits < 12:
                            self.current_class, self.decision_tree.current_course = course, course
                            self.decision_tree.get_next_node(5)
                            #return User_Query.UserQuery(self.student_profile, User_Query.QueryType.schedule_class_res)
                        else:
                            self.current_class, self.decision_tree.current_course = course, course
                            self.decision_tree.get_next_node(5)
                            #return User_Query.UserQuery(self.student_profile, User_Query.QueryType.full_schedule_check)
                    if entity.type == "personname":
                        course.prof = entity.entity
                        tm_courses = self.task_manager_information(course)
                        self.student_profile.potential_courses = tm_courses
                        if not tm_courses:
                            return User_Query.UserQuery(None, User_Query.QueryType.clarify)
                        else:
                            for pot_course in self.student_profile.potential_courses:
                                if pot_course.name or pot_course.id:
                                    self.student_profile.current_classes.append(tm_courses)
                                    self.student_profile.current_credits += 6
                                    self.student_profile.total_credits += tm_courses.credits
                                    if self.student_profile.current_credits < 12:
                                        self.current_class, self.decision_tree.current_course = course, course
                                        return self.decision_tree.get_next_node(5)
                                        #return User_Query.UserQuery(self.student_profile, User_Query.QueryType.schedule_class_res)
                                    else:
                                        self.current_class, self.decision_tree.current_course = course, course
                                        self.decision_tree.get_next_node(5)
                                        #return User_Query.UserQuery(self.student_profile, User_Query.QueryType.full_schedule_check)
                    if entity.type == "time":  # time object is a list of lists, first is M-F, second is len 2,
                        pass  # with start/end time that day?
                    # want a parse tree / relation extraction because we do not know
                    # whether it is during, before, or after without context.
                    if entity.type == "department":
                        course.department = entity.entity
                        tm_courses = self.task_manager_information(course)
                        self.student_profile.potential_courses = tm_courses
                        self.current_class, self.decision_tree.current_course = course, course
                        return self.decision_tree.get_next_node(5)
                        # return User_Query.UserQuery(self.student_profile, User_Query.QueryType.schedule_class_res)

            # done
            elif luis_intent == "StudentNameInfo":
                for entity in luis_entities:
                    if entity.type == "personname":
                        self.student_profile.name = entity.entity
                if self.student_profile.name:
                    return User_Query.UserQuery(self.student_profile, User_Query.QueryType.student_info_major)
                else:
                    return User_Query.UserQuery(None, User_Query.QueryType.student_info_major)


            # class sentiment only relavent on a prev class
            # done
            elif luis_intent == "ClassSentiment":
                prev_course = None
                if self.student_profile.all_classes:
                    if prev_course in self.student_profile.all_classes:
                        pass
                else:
                    return User_Query.UserQuery(None, User_Query.QueryType.clarify)

                return User_Query.UserQuery(prev_course, User_Query.QueryType.class_info_sentiment)

            # done for now
            elif luis_intent == "ClassDescriptionRequest":
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
                        print(tm_courses)
                        if not tm_courses:
                            return User_Query.UserQuery(None, User_Query.QueryType.clarify)
                        else:
                            self.student_profile.current_classes.append(tm_courses)
                            self.current_class, self.decision_tree.current_course = course, course
                            return self.decision_tree.get_next_node(36)
                            #return User_Query.UserQuery(tm_courses, User_Query.QueryType.new_class_description)
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
                        #return User_Query.UserQuery(course, User_Query.QueryType.new_class_description)
                        self.decision_tree.get_next_node(36)

            # done
            elif luis_intent == "WelcomeResponse":
                return User_Query.UserQuery(None, User_Query.QueryType.name)


            elif luis_intent == "ClassDescriptionResponse":
                course = Course.Course()
                self.task_manager_information(course)


            elif luis_intent == "ClassProfessorRequest":
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
                            return User_Query.UserQuery(None, User_Query.QueryType.clarify)
                        else:
                            self.student_profile.current_classes.append(tm_courses)
                            return User_Query.UserQuery(tm_courses, User_Query.QueryType.new_class_prof)

            elif luis_intent == "ClassProfessorResponse":
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
                            return User_Query.UserQuery(None, User_Query.QueryType.clarify)
                        else:
                            self.student_profile.current_classes.append(tm_courses)
                            return User_Query.UserQuery(tm_courses, User_Query.QueryType.new_class_prof)

            elif luis_intent == "StudentRequirementRequest":
                course = Course.Course()
                self.task_manager_information(course)
                return User_Query.UserQuery(course, User_Query.QueryType.class_info_description)

            elif luis_intent == "StudentRequirementResponse":
                course = Course.Course()
                self.task_manager_information(course)
                return User_Query.UserQuery(course, User_Query.QueryType.class_info_description)

            # done
            elif luis_intent == "StudentMajorResponse":
                return User_Query.UserQuery(self.student_profile.major, User_Query.QueryType.student_info_interests)

            # done
            elif luis_intent == "ClassTimeResponse":
                for entity in luis_entities:
                    for course in self.student_profile.all_classes:
                        if entity == course:
                            return User_Query.UserQuery(course, User_Query.QueryType.class_info_description)


            elif luis_intent == "ClassTimeRequest":
                course = Course.Course()
                self.task_manager_information(course)
                return User_Query.UserQuery(course, User_Query.QueryType.class_info_description)

            elif luis_intent == "ClassTermResponse":
                course = Course.Course()
                self.task_manager_information(course)
                return User_Query.UserQuery(course, User_Query.QueryType.class_info_description)

            elif luis_intent == "ClassTermRequest":
                pass

            # done
            elif luis_intent == "StudentInterests":
                for entity in luis_entities:
                    print(entity)
                    if entity.type == "u'CLASS" or entity.type == "u'DEPARTMENT" or entity.type == "u'SENTIMENT":
                        self.student_profile.interests.append(entity.entity)
                return User_Query.UserQuery(self.student_profile, User_Query.QueryType.new_class_name)

            # else statement will ask for more information
            elif luis_intent == "None":
                # if entity.type == "class":  # add more if's for different types
                if self.decision_tree.current_node.userQuery.type.value == 10:
                    if luis_entities:
                        for entity in luis_entities:
                            if entity.type == 'personname':
                                self.student_profile.name = entity.entity
                                return self.decision_tree.get_next_node() #also would ideally say greet user by name
                    elif len(self.last_query.split()) < 3:
                        self.student_profile.name = self.last_query
                        return self.decision_tree.get_next_node()
                    else:
                        return User_Query.UserQuery(None, User_Query.QueryType.clarify)
                if self.decision_tree.current_node.userQuery.type.value == 14:
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
                        return User_Query.UserQuery(None, User_Query.QueryType.clarify)
                    return self.decision_tree.get_next_node()

                elif self.decision_tree.current_node.userQuery.type.value == 11:
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
                        return self.decision_tree.get_next_node()
                    else:
                        return User_Query.UserQuery(None, User_Query.QueryType.clarify)
                elif self.decision_tree.current_node.userQuery.type.value == 17:
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

                    return User_Query.UserQuery(None, User_Query.QueryType.clarify)
                elif self.decision_tree.current_node.userQuery.type.value == 16:
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

                    return User_Query.UserQuery(None, User_Query.QueryType.clarify)

                elif self.decision_tree.current_node.userQuery.type.value == 13:
                    listOfWords = self.last_query
                    if "dunno" in listOfWords or "don't know" in listOfWords:
                        self.decision_tree.current_node.asked = True
                        return self.decision_tree.get_next_node()
                    if " in " in listOfWords:
                        listOfWords = listOfWords.split(" in ")
                    elif "s are " in listOfWords:
                        listOfWords = listOfWords.split("s are ")
                    if type(listOfWords) == type("thisIsAString"):
                        listOfWords = [listOfWords]
                    for word in listOfWords[1:]:
                        for smallerWord in word.split(","):
                            self.student_profile.interests.append(smallerWord)
                    if len(self.student_profile.interests) != 0:
                        return self.decision_tree.get_next_node()
                    return User_Query.UserQuery(None, User_Query.QueryType.clarify)

                elif self.decision_tree.current_node.userQuery.type.value == 32:
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
                    return User_Query.UserQuery(None, User_Query.QueryType.clarify)

                elif self.decision_tree.current_node.userQuery.type.value == 31:
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
                        return User_Query.UserQuery(None, User_Query.QueryType.clarify)
                elif self.decision_tree.current_node.userQuery.type.value == 37:
                    if " ok" in self.last_query or "sure" == self.last_query or "reccomend" in self.last_query:
                        print("they have gotten to the point where they want a course from us")
                        print("Lets fix this later")
                    if "no " in self.last_query or "I don" in self.last_query or "I've" in self.last_query or "know" in self.last_query or "I'm" in self.last_query:
                        return self.decision_tree.get_next_node()
                    return User_Query.UserQuery(None, User_Query.QueryType.clarify)






                ##oldstuffI haven't touched
                course = Course.Course()
                if luis_entities:
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
                            self.student_profile.current_classes.append(tm_courses)
                            self.student_profile.current_credits += tm_courses.credits
                            self.student_profile.total_credits += tm_courses.credits
                            print(self.student_profile.current_credits)

                            if self.student_profile.current_credits < 12:
                                #return User_Query.UserQuery(self.student_profile, User_Query.QueryType.schedule_class_res)
                                self.decision_tree.get_next_node()
                            else:
                                print(self.student_profile.current_credits)
                                self.decision_tree.get_next_node()
                                #return User_Query.UserQuery(self.student_profile, User_Query.QueryType.full_schedule_check)
                        if entity.type == "personname":
                            course.prof = entity.entity
                            tm_courses = self.task_manager_information(course)
                            self.student_profile.potential_courses = tm_courses
                            if not tm_courses:
                                return User_Query.UserQuery(None, User_Query.QueryType.clarify)
                            else:
                                for pot_course in self.student_profile.potential_courses:
                                    if pot_course.name or pot_course.id:
                                        self.student_profile.current_classes.append(tm_courses)
                                        self.student_profile.current_credits += 6
                                        self.student_profile.total_credits += tm_courses.credits
                                        if self.student_profile.current_credits < 12:
                                            self.decision_tree.get_next_node()
                                            #return User_Query.UserQuery(self.student_profile, User_Query.QueryType.schedule_class_res)
                                        else:
                                            self.decision_tree.get_next_node()
                                            #return User_Query.UserQuery(self.student_profile, User_Query.QueryType.full_schedule_check)
                        if entity.type == "time":  # time object is a list of lists, first is M-F, second is len 2,
                            pass  # with start/end time that day?
                        # want a parse tree / relation extraction because we do not know
                        # whether it is during, before, or after without context.
                        if entity.type == "department":
                            course.department = entity.entity
                            tm_courses = self.task_manager_information(course)
                            self.student_profile.potential_courses = tm_courses
                            #return User_Query.UserQuery(self.student_profile, User_Query.QueryType.schedule_class_res)
                            self.decision_tree.get_next_node()
                else:
                    return User_Query.UserQuery(None, User_Query.QueryType.clarify)

            else:
                print(User_Query.UserQuery(None, User_Query.QueryType.clarify).type)
                return User_Query.UserQuery(None, User_Query.QueryType.clarify)
        else:
            self.decision_tree.get_next_node()
            return User_Query.UserQuery(None, User_Query.QueryType.clarify)

    def task_manager_information(self, course):
        tm_courses = TaskManager.query_courses(course)
        if tm_courses:
            if len(tm_courses) == 1:
                return tm_courses
            else:
                return tm_courses[0]
        if not tm_courses:
            return User_Query.UserQuery(None, User_Query.QueryType.clarify)
            # @params course to add to student classes
            # @return 0 for added successfully, 1 for not added

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
