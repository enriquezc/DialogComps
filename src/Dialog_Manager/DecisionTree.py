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
        for i in listOfEnums:
            self.mapOfNodes[i] = NodeObject(User_Query.QueryType(i), [], [])

        # here we go...
        self.mapOfNodes[0].required_questions.append(self.mapOfNodes[10])  # name
        self.mapOfNodes[10].required_questions.extend([self.mapOfNodes[11], self.mapOfNodes[13]])  # time left / year
        self.mapOfNodes[10].potential_next_questions.extend([self.mapOfNodes[11], self.mapOfNodes[13]])  # time left / year
        self.mapOfNodes[11].required_questions.extend([self.mapOfNodes[12], self.mapOfNodes[18]])
        self.mapOfNodes[11].potential_next_questions.extend([self.mapOfNodes[13],self.mapOfNodes[12],self.mapOfNodes[16]])
        self.mapOfNodes[12].potential_next_questions.extend(
            [self.mapOfNodes[13],self.mapOfNodes[16], self.mapOfNodes[17], self.mapOfNodes[20]])
        self.mapOfNodes[13].potential_next_questions.extend([self.mapOfNodes[20], self.mapOfNodes[30]])  # time left / year
        self.mapOfNodes[15].required_questions.extend([self.mapOfNodes[18], self.mapOfNodes[17]])  # concentration, major requirements
        self.mapOfNodes[17].potential_next_questions.extend(
            [self.mapOfNodes[30], self.mapOfNodes[20], self.mapOfNodes[36]])  # department, prof, reccomend
        self.mapOfNodes[14].potential_next_questions.extend([self.mapOfNodes[11], self.mapOfNodes[18], self.mapOfNodes[16],
                                                        self.mapOfNodes[13]])  # major, concentration, distros, interests
        self.mapOfNodes[16].potential_next_questions.append(self.mapOfNodes[13])  # interests
        self.mapOfNodes[16].required_questions.append(
            self.mapOfNodes[32])  # ask if they want to take a course that fills these reqs
        self.mapOfNodes[17].required_questions.append(
            self.mapOfNodes[32])  # Ask if they want to take a course that fills these reqs
        self.mapOfNodes[17].potential_next_questions.append(self.mapOfNodes[13])  # interests
        self.mapOfNodes[18].potential_next_questions.extend(
            [self.mapOfNodes[17], self.mapOfNodes[16], self.mapOfNodes[13]])  # major reqs, distros, interests
        self.mapOfNodes[20].potential_next_questions.append(self.mapOfNodes[36])  # reccomend
        self.mapOfNodes[30].potential_next_questions.extend([self.mapOfNodes[20], self.mapOfNodes[36]])  # prof, reccomend
        self.mapOfNodes[32].potential_next_questions.extend(
            [self.mapOfNodes[13], self.mapOfNodes[36]])  # interests, should we reccomend something?
        self.mapOfNodes[36].potential_next_questions.append(self.mapOfNodes[20])  # what class would they want to take?
        self.head_node = self.mapOfNodes[0]

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
    def get_next_node(self, query_number = self.current_node):
        past_node = self.current_node
        if query_number != self.current_node:
            past_node = self.mapOfNodes[query_number]


        #self.current_node = self.mapOfNodes[query_number]
        self.current_node.asked = True
        if self.is_answered(past_node):
            for node in past_node.required_questions:
                if not self.is_answered(node):
                    if not node.asked:
                        self.current_node  = node
                        return node
        for node in past_node.potential_next_questions:
            if not self.is_answered(node):
                if not node.asked:
                    self.current_course = node
                    return node
        if self.is_answered(past_node):
            for node in past_node.required_questions:
                if not self.is_answered(node):
                    #if not node.asked:
                    self.current_node = node
                    return node

        for node in past_node.potential_next_questions:
            if not self.is_answered(node):
                #   if not node.asked:
                self.current_course = node
                return node
        if not self.is_answered(past_node):
            return past_node

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

