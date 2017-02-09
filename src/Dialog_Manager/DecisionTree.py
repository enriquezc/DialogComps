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

    def answer(self):
        pass

    def relevant_course(*args):
        pass

    def call_database(self):
        pass

class DecisionTree:
    def __init__(self, student):
        self.mapOfNodes = {}
        self.head_node = NodeObject(User_Query.UserQuery(None, User_Query.QueryType.clarify), [], [])
        #self.current_node = None
        self.build_Tree()
        self.current_node = self.head_node
        self.current_course = None
        self.student = student


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
            if self.current_course in self.student.current_classes:
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
            if self.current_course.name and self.current_course.id:
                node.answered = True
                return True
            node.answered = False
            return False
        elif node.userQuery.value == 31: #new_class_prof
            if self.current_course.prof:
                node.answered = True
                return True
            node.answered = False
            return False
        elif node.userQuery.value == 32: #new_class_dept
            if self.current_course.department:
                node.answered = True
                return True
            node.answered = False
            return False
        elif node.userQuery.value == 33: #new_class_sentiment
            if self.current_course.sentiment:
                node.answered = True
                return True
            node.answered = False
            return False
        elif node.userQuery.value == 35: #new_class_time
            if self.current_course.time:
                node.answered = True
                return True
            node.answered = False
            return False
        elif node.userQuery.value == 37: #new_class_res
            return False

    def build_Tree(self):
        listOfEnums = [0, 1, 2, 3, 4, 5, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 24, 25, 26, 30, 31, 32, 33,
                       34, 35, 36, 37]
        for i in listOfEnums:
            self.mapOfNodes[i] = NodeObject(User_Query.QueryType(i), [], [])

        # here we go...
        self.mapOfNodes[0].required_questions.append(self.mapOfNodes[10])  # name
        self.mapOfNodes[10].required_questions.extend([self.mapOfNodes[11], self.mapOfNodes[13]])  # time left / year
        self.mapOfNodes[10].potential_next_questions.extend([self.mapOfNodes[11], self.mapOfNodes[13]])  # time left / year
        self.mapOfNodes[11].required_questions.extend([self.mapOfNodes[18]])
        self.mapOfNodes[11].potential_next_questions.extend([self.mapOfNodes[13]])
        self.mapOfNodes[12].potential_next_questions.extend([self.mapOfNodes[13], self.mapOfNodes[20]])
        self.mapOfNodes[13].potential_next_questions.extend([self.mapOfNodes[30], self.mapOfNodes[20]])  # time left / year
        self.mapOfNodes[15].required_questions.extend([self.mapOfNodes[18]])  # concentration, major requirements
        #self.mapOfNodes[17].potential_next_questions.extend(
            #[self.mapOfNodes[30], self.mapOfNodes[20], self.mapOfNodes[36]])  # department, prof, reccomend
        self.mapOfNodes[14].potential_next_questions.extend([self.mapOfNodes[11], self.mapOfNodes[18], self.mapOfNodes[13]])  # major, concentration, distros, interests
        #self.mapOfNodes[16].potential_next_questions.append(self.mapOfNodes[13])  # interests
        #self.mapOfNodes[16].required_questions.append(
            #self.mapOfNodes[32])  # ask if they want to take a course that fills these reqs
        #self.mapOfNodes[17].required_questions.append(
            #self.mapOfNodes[32])  # Ask if they want to take a course that fills these reqs
        #self.mapOfNodes[17].potential_next_questions.append(self.mapOfNodes[13])  # interests
        self.mapOfNodes[18].potential_next_questions.extend([self.mapOfNodes[30], self.mapOfNodes[13]])  # major reqs, distros, interests
        self.mapOfNodes[20].potential_next_questions.append(self.mapOfNodes[36])  # reccomend
        self.mapOfNodes[30].potential_next_questions.extend([self.mapOfNodes[20], self.mapOfNodes[36]])  # prof, reccomend
        self.mapOfNodes[32].potential_next_questions.extend(
            [self.mapOfNodes[13], self.mapOfNodes[36]])  # interests, should we reccomend something?
        self.mapOfNodes[36].potential_next_questions.append(self.mapOfNodes[20])  # what class would they want to take?
        self.head_node = self.mapOfNodes[10]

    # takes in nothing, returns a userquery for asking how they feel about a new class.
    # The new classes are stored in the student object, under potential courses.
    def recommend_course(self):
        self.student.potential_courses = TaskManager.recommend_course(self.student)
        if len(self.student.potential_courses) > 0:
            return User_Query.UserQuery(self.student, node.userQuery)
        else:
            return User_Query.UserQuery(self.student, past_node.userQuery)

    # @params: the current node of the tree
    # @return: the next node of the tree
    def get_next_node(self):
        past_node = self.current_node
        '''if query_number != self.current_node:
            past_node = self.mapOfNodes[query_number]'''

        #self.current_node = self.mapOfNodes[query_number]
        self.current_node.asked = True
        if self.current_node.userQuery == 30 or self.current_node.userQuery == 37:
            self.current_node.asked = False
        if self.is_answered(past_node):
            for node in past_node.required_questions:
                print("asked: ", self.is_answered(node))
                print("answered: ", self.is_answered(node))
                if not self.is_answered(node):
                    if not node.asked:
                        self.current_node = node
                        print("has answered")
                        return User_Query.UserQuery(self.student, node.userQuery)
        for node in past_node.potential_next_questions:
            if not self.is_answered(node):
                if not node.asked:
                    self.current_course = node
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
                self.current_course = node
                print("next node: 1 ", past_node.userQuery)
                return User_Query.UserQuery(self.student, node.userQuery)
        if not self.is_answered(past_node):
            print("next node: 2 ", past_node.userQuery)
            return User_Query.UserQuery(self.student, past_node.userQuery)

        if len(past_node.required_questions) > 0:
            self.current_node = past_node.required_questions[0]
            return self.get_next_node()
        if len(past_node.potential_next_questions) > 0:
            self.current_node = past_node.required_questions[0]
            return self.get_next_node()
        self.current_node = self.mapOfNodes[0]
        return self.get_next_node()

        '''try:
            if self.current_node.answered == 1:
                for node in self.current_node.required_questions:
                    if node.asked or self.is_answered(node):
                        pass
                    else:

                        self.current_node = self.current_node.required_questions
                for node in self.current_node.potential_next_questions:
                    if node.asked or self.is_answered(node):
                        pass
                    else:
                        self.current_node = node

                for node in self.current_node.required_questions:
                    if self.is_answered(node):
                        pass
                    else:
                        self.current_node = node

                for node in self.current_node.required_questions:
                    if self.is_answered(node):
                        pass
                    else:
                        self.current_node = node

            if self.current_node.answered == 0:
                for node in self.current_node.potential_next_questions:
                    if node.asked or node.answered:
                        pass
                    else:
                        self.current_node = node

                # have looped through and no node that is asked or answered, now loop to find one that is just not answered
                for node in self.current_node.potential_next_questions:
                    if node.answered:
                        pass
                    else:
                        self.current_node = node
                if past_node == self.current_node:
                    return self.current_node


            return [User_Query.UserQuery(self.student, self.current_node.userQuery)]

        except ValueError:
            print("Unexpected error:", sys.exc_info()[0])
            raise
    '''
    '''if __name__ == "__main__":
        student = Student.Student()
        decision_tree = DecisionTree.DecisionTree(student)
        next_node = decision_tree.get_next_node(36)
        print(next_node.type)'''

