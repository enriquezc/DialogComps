import queue
import re
import sys
from nltk.tree import Tree
from src.Dialog_Manager import Student, Course, User_Query
from src.NLUU import nluu
import nltk
import luis
from src.Task_Manager import TaskManager


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
class DecisionTree:
    def __init__(self, student):
        self.mapOfNodes = {}
        self.head_node = NodeObject(User_Query.UserQuery(None, User_Query.QueryType.welcome), [], [])
        self.build_Tree()
        self.current_node = self.head_node
        self.current_courses = [Course.Course()]
        self.student = student


    def get_current_node(self):
        return self.current_node

    def is_answered(self, node):
        if node.userQuery.value == 0: #welcome
            node.answered = True
            return True
        elif node.userQuery.value == 1: #goodbye
            node.answered = False
            return False
        elif node.userQuery.value == 2: #clarify
            node.answered = False
            return False
        elif node.userQuery.value == 3: #specify
            node.answered = False
            return False
        elif node.userQuery.value == 4: #pleasantry
            node.answered = False
            return False
        elif node.userQuery.value == 5: #schedule_class_res
            if self.current_courses[0] in self.student.current_classes:
                node.answered = True
                return True
            node.answered = False
            return False
        elif node.userQuery.value == 10: #student_name_info
            if self.student.name:
                node.answered = True
                return True
            node.answered = False
            return False
        elif node.userQuery.value == 11: #student_info_major
            if len(self.student.major) > 0:
                node.answered = True
                return True
            node.answered = False
            return False
        elif node.userQuery.value == 12: #student_info_previous_classes
            if self.student.previous_classes:
                node.answered = True
                return True
            node.answered = False
            return False
        elif node.userQuery.value == 13: #student_info_interests
            if self.student.interests:
                node.answered = True
                return True
            node.answered = False
            return False
        elif node.userQuery.value == 14: #student_info_time_left
            if self.student.terms_left == 0:
                node.answered = False
                return False
            node.answered = True
            return True
        elif node.userQuery.value == 15: #student_info_abroad
            if self.student.abroad:
                node.answered = True
                return True
            node.answered = False
            return False
        elif node.userQuery.value == 16: #student_info_requirements
            if self.student.distributions_needed:
                node.answered = True
                return True
            node.answered = False
            return False
        elif node.userQuery.value == 17: #student_info_major_requirements
            if self.student.major_classes_needed:
                node.answered = True
                return True
            elif self.student.major == "undeclared":
                node.answered = True
                return True
            node.answered = False
            return False
        elif node.userQuery.value == 18: #student_info_concentration
            if self.student.concentration:
                node.answered = True
                return True
            elif self.student.major == "undeclared":
                node.answered = True
                return True
            node.answered = False
            return False

        elif node.userQuery.value == 30: #new_class_name
            if self.current_courses[0].name or self.current_courses[0].id:
                node.answered = True
                return True
            node.answered = False
            return False
        elif node.userQuery.value == 31: #new_class_prof
            if self.current_courses[0].prof:
                node.answered = True
                return True
            node.answered = False
            return False
        elif node.userQuery.value == 32: #new_class_dept
            if self.current_courses[0].department:
                node.answered = True
                return True
            node.answered = False
            return False
        elif node.userQuery.value == 33: #new_class_sentiment
            if self.current_courses[0].sentiment:
                node.answered = True
                return True
            node.answered = False
            return False
        elif node.userQuery.value == 35: #new_class_time
            if self.current_courses[0].time:
                node.answered = True
                return True
            node.answered = False
            return False
        elif node.userQuery.value == 37: #new_class_res
            return False

    def build_Tree(self):
        for query_type in User_Query.QueryType:
            self.mapOfNodes[query_type] = NodeObject(query_type, [], [])

        # here we go...
        self.mapOfNodes[User_Query.QueryType.welcome].required_questions.extend([self.mapOfNodes[User_Query.QueryType.student_info_name]])  # name
        self.mapOfNodes[User_Query.QueryType.schedule_class_res].required_questions.extend([self.mapOfNodes[User_Query.QueryType.new_class_name]])
        self.mapOfNodes[User_Query.QueryType.schedule_class_res].potential_next_questions.extend([self.mapOfNodes[User_Query.QueryType.new_class_name]])
        #self.mapOfNodes[User_Query.QueryType.full_schedule_check].required_questions.extend([self.mapOfNodes[User_Query.QueryType.goodbye]])
        #self.mapOfNodes[User_Query.QueryType.full_schedule_check].potential_next_questions.extend([self.mapOfNodes[User_Query.QueryType.goodbye]])

        self.mapOfNodes[User_Query.QueryType.student_info_name].required_questions.extend([self.mapOfNodes[User_Query.QueryType.student_info_major], self.mapOfNodes[User_Query.QueryType.student_info_interests]])  # time left / year
        self.mapOfNodes[User_Query.QueryType.student_info_name].potential_next_questions.extend([self.mapOfNodes[User_Query.QueryType.student_info_major], self.mapOfNodes[User_Query.QueryType.student_info_interests]])  # time left / year
        self.mapOfNodes[User_Query.QueryType.student_info_major].required_questions.extend([self.mapOfNodes[User_Query.QueryType.student_info_concentration],])
        self.mapOfNodes[User_Query.QueryType.student_info_major].potential_next_questions.extend([self.mapOfNodes[User_Query.QueryType.student_info_interests]])
        self.mapOfNodes[User_Query.QueryType.student_info_previous_classes].potential_next_questions.extend([self.mapOfNodes[User_Query.QueryType.student_info_interests]])
        self.mapOfNodes[User_Query.QueryType.student_info_interests].potential_next_questions.extend([self.mapOfNodes[User_Query.QueryType.new_class_name]])
        self.mapOfNodes[User_Query.QueryType.student_info_abroad].required_questions.extend([self.mapOfNodes[User_Query.QueryType.student_info_concentration]])  # concentration, major requirements
        self.mapOfNodes[User_Query.QueryType.student_info_major_requirements].potential_next_questions.extend([self.mapOfNodes[User_Query.QueryType.new_class_name], self.mapOfNodes[User_Query.QueryType.class_info_name], self.mapOfNodes[User_Query.QueryType.new_class_description]])  # department, prof, recommend
        self.mapOfNodes[User_Query.QueryType.student_info_time_left].potential_next_questions.extend([self.mapOfNodes[User_Query.QueryType.student_info_major], self.mapOfNodes[User_Query.QueryType.student_info_concentration], self.mapOfNodes[User_Query.QueryType.student_info_interests]])  # major, concentration, distros, interests
        self.mapOfNodes[User_Query.QueryType.student_info_requirements].potential_next_questions.append(self.mapOfNodes[User_Query.QueryType.student_info_interests])  # interests
        self.mapOfNodes[User_Query.QueryType.student_info_requirements].required_questions.append(self.mapOfNodes[User_Query.QueryType.new_class_dept])  # ask if they want to take a course that fills these reqs
        self.mapOfNodes[User_Query.QueryType.student_info_major_requirements].required_questions.append(self.mapOfNodes[User_Query.QueryType.new_class_dept])  # Ask if they want to take a course that fills these reqs
        self.mapOfNodes[User_Query.QueryType.student_info_major_requirements].potential_next_questions.append(self.mapOfNodes[User_Query.QueryType.student_info_interests])  # interests
        self.mapOfNodes[User_Query.QueryType.student_info_concentration].potential_next_questions.extend([self.mapOfNodes[User_Query.QueryType.new_class_name], self.mapOfNodes[User_Query.QueryType.student_info_interests]])  # major reqs, distros, interests
        self.mapOfNodes[User_Query.QueryType.class_info_name].potential_next_questions.append(self.mapOfNodes[User_Query.QueryType.new_class_request])  # recommend
        self.mapOfNodes[User_Query.QueryType.new_class_name].potential_next_questions.extend([self.mapOfNodes[User_Query.QueryType.schedule_class_res], self.mapOfNodes[User_Query.QueryType.new_class_request]])  # prof, recommend
        self.mapOfNodes[User_Query.QueryType.new_class_dept].potential_next_questions.extend(
            [self.mapOfNodes[User_Query.QueryType.student_info_interests], self.mapOfNodes[User_Query.QueryType.new_class_description]])  # interests, should we recommend something?
        self.mapOfNodes[User_Query.QueryType.new_class_description].potential_next_questions.append(self.mapOfNodes[User_Query.QueryType.new_class_name])  # what class would they want to take?

        self.head_node = self.mapOfNodes[User_Query.QueryType.student_info_name]
        self.current_node = self.head_node

    # takes in nothing, returns a userquery for asking how they feel about a new class.
    # The new classes are stored in the student object, under potential courses.
    def recommend_course(self):
        self.student.potential_courses = TaskManager.recommend_course(self.student)
        if len(self.student.potential_courses) > 0:
            return User_Query.UserQuery(self.student, self.node.userQuery)
        else:
            return User_Query.UserQuery(self.student, self.past_node.userQuery)

    # @params: the current node of the tree
    # @return: the next node of the tree
    def get_next_node(self):
        
        past_node = self.current_node
        print(past_node.userQuery)
        '''if query_number != self.current_node:
            past_node = self.mapOfNodes[query_number]'''

        #self.current_node = self.mapOfNodes[query_number]
        self.current_node.asked = True
        if self.current_node.userQuery == 30 or self.current_node.userQuery == 37:
            self.current_node.asked = False
        if self.is_answered(past_node):
            for node in past_node.required_questions:
                print("asked: ", past_node.asked)
                print("answered: ", self.is_answered(past_node))
                if not self.is_answered(node):
                    if not node.asked:
                        self.current_node = node
                        print("has answered")
                        return User_Query.UserQuery(self.student, node.userQuery)
        for node in past_node.potential_next_questions:
            if not self.is_answered(node):
                if not node.asked:
                    self.current_node = node
                    print("current node: 1 ", past_node.userQuery)

                    return User_Query.UserQuery(self.student, node.userQuery)
        if self.is_answered(past_node):
            for node in past_node.required_questions:
                if not self.is_answered(node):
                    #if not node.asked:
                    self.current_node = node
                    print("current node: 2 ", past_node.userQuery)
                    return User_Query.UserQuery(self.student, node.userQuery)

        for node in past_node.potential_next_questions:
            if not self.is_answered(node):
                #   if not node.asked:
                self.current_node = node
                print("next node: 1 ", past_node.userQuery)
                return User_Query.UserQuery(self.student, node.userQuery)
        if not self.is_answered(past_node):
            print("next node: 2 ", past_node.userQuery)
            return User_Query.UserQuery(self.student, past_node.userQuery)

        if len(past_node.required_questions) > 0:
            self.current_node = past_node.required_questions[0]
            return self.get_next_node()
        if len(past_node.potential_next_questions) > 0 and len(past_node.required_questions) > 0:
            self.current_node = past_node.required_questions[0]
            return self.get_next_node()
        self.current_node = self.mapOfNodes[User_Query.QueryType.welcome]
        return self.get_next_node()