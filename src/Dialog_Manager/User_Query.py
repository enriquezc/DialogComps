from enum import Enum


class QueryType(Enum):
    #welcome statement for our bot
    welcome = 0
    #exit statement for our bot
    goodbye = 1
    #asking to clarify previous statement
    clarify = 2
    #ask to be more specific
    specify = 3
    #pleasantries
    pleasantry = 4
    #successfully scheduled a class
    schedule_class_res = 5



    #ask for more info about student
    # their name
    student_info_name = 10
    # their major and/or concentration
    student_info_major = 11
    # more info about their previous classes
    student_info_previous_classes = 12
    # more info about their interests
    student_info_interests = 13
    # more info about how much time left at Carleton
    student_info_time_left = 14
    # more info about studying abroad (current/future plans)
    student_info_abroad = 15
    #ask about distro requirements left
    student_info_requirements = 16
    #ask about major requirements left
    student_info_major_requirements = 17
    #ask about concentration
    student_info_concentration = 18



    #ask for more info about a class they've taken
    #specific name of class they've taken
    class_info_name  = 20
    #professor who taugh said class
    class_info_prof = 21
    #which term they took the class
    class_info_term = 22
    #how they felt about the class (basic)
    class_info_sentiment = 23
    #what parts of a class they liked or disliked.
    #More related to student interests than class sentiment
    class_info_sentiment_extended = 24
    #did they scrunch the class.
    class_info_scrunch = 25
    #What time of day the class was
    class_info_time = 26
    #ask for more info about a class they want to take
    #If name is given, as if they want to take this class
    #If class object is given, this indicates they have an idea of what they want to take
    #but we can't identify the name. Probably a rare case
    #If no class object passed, ask general question about specific classes they'd like to take
    new_class_name = 30
    #Ask about what professor they'd like to take, if any
    new_class_prof = 31
    #ask about departments they'd like to take classes in
    new_class_dept = 32
    #given a class, see how they feel about it
    new_class_sentiment = 33
    #Ask what requirements they'd like to fulfill.
    new_class_requirements = 34
    #Ask what time they'd like the class to be. Or alternatively, what time they don't want it to be
    new_class_time = 35
    #Return information about a course they've asked for
    new_class_description = 36




#This gets passed on to the NLUU, allowing it to decipher
class UserQuery:
    def __init__(self, object = None, type = QueryType.pleasantry):
        self.type = type
        #As of now either empty, of type class, or of type student.
        self.object = object

