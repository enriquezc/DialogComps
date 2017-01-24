import queue
import re
import sys
from nltk.tree import Tree
from src.Dialog_Manager import Student, Course, User_Query
import nltk
import luis
from src.Task_Manager import TaskManager


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

    def __init__(self):
        self.student_profile = Student.Student()
        self.last_query = 0
        self.head_node = NodeObject(User_Query.UserQuery(None, User_Query.QueryType.clarify), [], [])
        self.current_node = self.head_node
        self.current_class = None
        self.decision_tree = DecisionTree(self.student_profile)
        self.queries = []

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
                        self.student_profile.current_classes.append(tm_courses)
                        self.student_profile.current_credits =+ 6
                        self.student_profile.total_credits += tm_courses.credits
                        print(self.student_profile.current_credits)
                        if self.student_profile.current_credits < 12:
                            self.current_class, self.decision_tree.current_course = course, course
                            self.decision_tree.get_next_node()
                            #return User_Query.UserQuery(self.student_profile, User_Query.QueryType.schedule_class_res)
                        else:
                            print(self.student_profile.current_credits)
                            self.current_class, self.decision_tree.current_course = course, course
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
                                        self.current_class, self.decision_tree.current_course = course, course
                                        self.decision_tree.get_next_node()
                                        #return User_Query.UserQuery(self.student_profile, User_Query.QueryType.schedule_class_res)
                                    else:
                                        self.current_class, self.decision_tree.current_course = course, course
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
                        self.current_class, self.decision_tree.current_course = course, course
                        self.decision_tree.get_next_node()
                        #return User_Query.UserQuery(self.student_profile, User_Query.QueryType.schedule_class_res)

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
                            self.decision_tree.get_next_node()
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
                        self.decision_tree.get_next_node(self)

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
            # @params
            # @return

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


class NodeObject:
    # have a relavent function for each user query??!?!?!
    # how do we do that? Can we just assign a variable to be a function? That doesn't make any sense tho
    # What if we have a string that is also the name of a function? Can that work? python is dumb and obtrusive


    def __init__(self, userQ, requiredQ, potentialQ):
        self.userQuery = userQ
        self.required_questions = []
        requiredQ = requiredQ or []
        self.required_questions.extend(requiredQ)
        self.asked = False
        self.answered = False
        self.potential_next_questions = []
        self.potential_next_questions.extend(potentialQ)
        self.node_function = None

    def answer(self):
        pass

    def relevant_course(*args):
        pass

    def call_database(self):
        pass

class DecisionTree:
    def __init__(self, student):
        self.head_node = NodeObject(User_Query.UserQuery(None, User_Query.QueryType.clarify), [], [])
        self.current_node = None
        self.build_Tree()
        self.current_node = self.head_node
        self.current_course = None
        self.student = student

    def is_answered(self, node):
        if node.userQuery.type== 0:
            node.answered = True
            return True
        elif node.userQuery.type== 1:
            node.answered = False
            return False
        elif node.userQuery.type== 2:
            node.answered = False
            return False
        elif node.userQuery.type== 3:
            node.answered = False
            return False
        elif node.userQuery.type== 4:
            node.answered = False
            return False
        elif node.userQuery.type== 5:
            if self.current_course in self.student.current_classes:
                node.answered = True
                return True
            node.answered = False
            return False
        elif node.userQuery.type== 10:
            if self.student.name != None:
                node.answered = True
                return True
            node.answered = False
            return False
        elif node.userQuery.type== 11:
            if self.student.major != []:
                node.answered = True
                return True
            node.answered = False
            return False
        elif node.userQuery.type== 12:
            if self.student.previous_classes != []:
                node.answered = True
                return True
            node.answered = False
            return False
        elif node.userQuery.type== 13:
            if self.student.interests != []:
                node.answered = True
                return True
            node.answered = False
            return False
        elif node.userQuery.type== 14:
            if self.student.terms_left == 0:
                node.answered = False
                return False
            node.answered = True
            return True
        elif node.userQuery.type== 15:
            if self.student.abroad != None:
                node.answered = True
                return True
            node.answered = False
            return False
        elif node.userQuery.type== 16:
            if self.student.distributions_needed != []:
                node.answered = True
                return True
            node.answered = False
            return False
        elif node.userQuery.type== 17:
            if self.student.major_classes_needed != []:
                node.answered = True
                return True
            elif self.student.major == "undeclared":
                node.answered = True
                return True
            node.answered = False
            return False
        elif node.userQuery.type== 18:
            if self.student.concentration != None:
                node.answered = True
                return True
            elif self.student.major == "undeclared":
                node.answered = True
                return True
            node.answered = False
            return False

        elif node.userQuery.type== 30:
            if self.current_course.name != None and self.current_course.id != None:
                node.answered = True
                return True
            node.answered = False
            return False
        elif node.userQuery.type== 31:
            if self.current_course.prof != None:
                node.answered = True
                return True
            node.answered = False
            return False
        elif node.userQuery.type == 32:
            if self.current_course.department != None:
                node.answered = True
                return True
            node.answered = False
            return False
        elif node.userQuery.type == 33:
            if self.current_course.sentiment != 0:
                node.answered = True
                return True
            node.answered = False
            return False
        elif node.userQuery.type == 35:
            if self.current_course.time != None:
                node.answered = True
                return True
            node.answered = False
            return False
        elif node.userQuery.type== 37:
            return False

    def build_Tree(self):
        listOfEnums = [0, 1, 2, 3, 4, 5, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 24, 25, 26, 30, 31, 32, 33,
                       34,
                       35, 36, 37]
        num_nodes = len(listOfEnums)
        mapOfNodes = {}
        for i in listOfEnums:
            mapOfNodes[i] = NodeObject(User_Query.QueryType(i), [], [])

        # here we go...
        mapOfNodes[0].required_questions.append(mapOfNodes[10])  # name
        mapOfNodes[10].required_questions.append(mapOfNodes[14])  # time left / year
        mapOfNodes[15].required_questions.extend([mapOfNodes[18], mapOfNodes[17]])  # concentration, major requirements
        mapOfNodes[11].potential_next_questions.append(mapOfNodes[16])  # distros
        mapOfNodes[17].potential_next_questions.extend(
            [mapOfNodes[30], mapOfNodes[26], mapOfNodes[35]])  # department, prof, reccomend
        mapOfNodes[14].potential_next_questions.extend([mapOfNodes[11], mapOfNodes[18], mapOfNodes[16],
                                                        mapOfNodes[13]])  # major, concentration, distros, interests
        mapOfNodes[16].potential_next_questions.append(mapOfNodes[13])  # interests
        mapOfNodes[16].required_questions.append(
            mapOfNodes[32])  # ask if they want to take a course that fills these reqs
        mapOfNodes[17].required_questions.append(
            mapOfNodes[32])  # Ask if they want to take a course that fills these reqs
        mapOfNodes[17].potential_next_questions.append(mapOfNodes[13])  # interests
        mapOfNodes[18].potential_next_questions.extend(
            [mapOfNodes[17], mapOfNodes[16], mapOfNodes[13]])  # major reqs, distros, interests
        mapOfNodes[26].potential_next_questions.append(mapOfNodes[35])  # reccomend
        mapOfNodes[30].potential_next_questions.extend([mapOfNodes[26], mapOfNodes[35]])  # prof, reccomend
        mapOfNodes[32].potential_next_questions.extend(
            [mapOfNodes[13], mapOfNodes[35]])  # interests, should we reccomend something?
        mapOfNodes[35].potential_next_questions.append(mapOfNodes[25])  # what class would they want to take?
        self.head_node = mapOfNodes[0]

    # takes in nothing, returns a userquery for asking how they feel about a new class.
    # The new classes are stored in the student object, under potential courses.
    def recommend_course(self):
        self.student.potential_courses = TaskManager.recommend_course(self.student)
        if len(self.student.potential_courses) > 0:
            return User_Query(33)
        else:
            return User_Query(13)

    # @params: the current node of the tree
    # @return: the next node of the tree
    def get_next_node(self):
        self.current_node.asked = True
        try:
            if self.current_node.answered == 1:
                for i in range(len(self.current_node.required_questions)):
                    if self.current_node.required_questions[i].asked or self.is_answered(self.current_node.required_questions[i]):
                        pass
                    else:

                        self.current_node = self.current_node.required_questions[i]

                for i in range(len(self.current_node.potential_next_questions)):
                    if self.current_node.potential_next_questions[i].asked or self.is_answered(
                            self.current_node.potential_next_questions[i]):
                        pass
                    else:
                        self.current_node = self.current_node.potential_next_questions[i]

                for i in range(len(self.current_node.required_questions)):
                    if self.current_node.required_questions[i].answered:
                        pass
                    else:
                        self.current_node = self.current_node.required_questions[i]

                for i in range(len(self.current_node.required_questions)):
                    if self.current_node.potential_next_questions[i].answered:
                        pass
                    else:
                        self.current_node = self.current_node.potential_next_questions[i]

            if self.current_node.answered == 0:
                for i in range(len(self.current_node.potential_next_questions)):
                    if self.current_node.potential_next_questions[i].asked or self.current_node.potential_next_questions[
                        i].answered:
                        pass
                    else:
                        self.current_node = self.current_node.potential_next_questions[i]

                # have looped through and no node that is asked or answered, now loop to find one that is just not answered
                for i in range(len(self.current_node.potential_next_questions)):
                    if self.current_node.potential_next_questions[i].answered:
                        pass
                    else:
                        self.current_node = self.current_node.potential_next_questions[i]

            if self.current_node.userQuery > 10 and self.current_node.userQuery < 20:
                return User_Query.UserQuery(self.student, self.current_node.userQuery)
            elif self.current_node.userQuery > 18:
                return User_Query.UserQuery(self.current_course, self.current_node.userQuery)
            else:
                return User_Query.UserQuery(None, self.current_node.userQuery)
        except ValueError:
            print("Unexpected error:", sys.exc_info()[0])
            raise