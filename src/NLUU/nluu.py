import nltk
import luis
from src.Dialog_Manager import Student, Course, User_Query
from src.Dialog_Manager.User_Query import QueryType
from src.utils import constants
from nltk.stem.snowball import SnowballStemmer
import random

class nLUU:
    def __init__(self, luisurl):
        self.luis = luis.Luis(luisurl)
        self.response_dict = {
            QueryType.welcome: self.create_welcome_response,
            QueryType.goodbye: self.create_goodbye_response,
            QueryType.clarify: self.create_clarify_response,
            QueryType.specify: self.create_specify_response,
            QueryType.pleasantry: self.create_pleasantry_response,
            QueryType.class_info_term: self.create_class_info_term,
            #QueryType.class_info_term_res: self.create_class_info_term_res,
            QueryType.class_info_time: self.create_class_info_time,
            #QueryType.class_info_time_res: self.create_class_info_time_res,
            #QueryType.classes_info_prof_res: self.create_class_info_prof_res,
            QueryType.class_info_name: self.create_class_info_name,
            #QueryType.class_info_name_res: self.create_class_info_name_res,
            QueryType.class_info_prof: self.create_class_info_prof,
            #QueryType.class_info_prof_res: self.create_class_info_prof_res,
            QueryType.class_info_scrunch: self.create_class_info_scrunch,
            QueryType.class_info_sentiment: self.create_class_info_sentiment,
            QueryType.class_info_sentiment_extended: self.create_class_info_sentiment,
            QueryType.new_class_dept: self.create_new_class_dept,
            QueryType.student_info_name: self.create_student_info_name,
            QueryType.student_info_major: self.create_student_info_major,
            QueryType.student_info_previous_classes: self.create_student_info_previous_classes,
            QueryType.student_info_interests: self.create_student_info_interests,
            QueryType.student_info_time_left: self.create_student_info_time_left,
            QueryType.student_info_abroad: self.create_student_info_abroad,
            QueryType.student_info_requirements: self.create_student_info_requirements,
            QueryType.student_info_major_requirements: self.create_student_info_major,
            QueryType.student_info_concentration : self.create_student_info_concentration,
            QueryType.new_class_name: self.create_new_class_name,
            QueryType.new_class_prof: self.create_new_class_prof,
            QueryType.new_class_sentiment: self.create_new_class_sentiment,
            QueryType.new_class_requirements: self.create_new_class_requirements,
            QueryType.new_class_time: self.create_new_class_time,
            QueryType.new_class_description: self.create_new_class_description,
            QueryType.schedule_class_res: self.create_schedule_class_res,
            QueryType.full_schedule_check : self.create_full_schedule_check,
            QueryType.student_info_name_res : self.create_student_info_name_res,
            QueryType.student_info_major_res : self.create_student_info_major_res,
            QueryType.student_info_previous_classes_res : self.create_student_info_previous_classes_res,
            QueryType.student_info_interests_res : self.create_student_info_interests_res,
            QueryType.student_info_time_left_res : self.create_student_info_time_left_res,
            QueryType.student_info_abroad_res : self.create_student_info_abroad_res,
            QueryType.student_info_requirements_res : self.create_student_info_requirements_res,
            QueryType.student_info_major_requirements_res : self.create_student_info_major_requirements_res,
            QueryType.student_info_concentration_res : self.create_student_info_concentration_res
        }
        self.stemmer = SnowballStemmer("english")
        #Requires a local copy of atis.cfg
        #atis_grammar = nltk.data.load("atis.cfg")
        #self.parser = nltk.ChartParser(atis_grammar)



    def tokenize(self, s):
        '''
            Tokenizes input from client
        '''
        return nltk.word_tokenize(s)


    def pos_tag(self, s):
        '''
            Part-of-speech taging for str
        '''
        return nltk.pos_tag(s)


    def create_syntax_tree(self, s):
        '''
            Creates a syntax tree from str
        '''
        return self.parser.parse(s)


    def get_luis(self, s):
        '''
            Calls  pyluis to get intent analysis
        '''
        return self.luis.analyze(s)

    def create_response_string(self, userQuery):
        '''
            Takes whatever response from backend and converts to readable string
        '''
        if type(userQuery.object) == Course.Course:
            s = 'Here\'s some data about your course:\n'
            d = userQuery.object.__dict__
            print(d)
            for k, v in d.items():
                if v != None and v != 0 and not (type(v) == list and len(v) == 0):
                    s += k + ':' + v + '\n'
        elif type(userQuery.object) == Student:
            s = 'Please ask me about a course.'
        else:
            s = 'Please ask me about a course'
        return s

    def create_response(self, userQuery):
        fun = self.response_dict[userQuery.type]
        if fun == None:
            fun = self.response_dict[QueryType.welcome]
        return fun(userQuery)

    def create_welcome_response(self, userQuery):
        return constants.Responses.WELCOME[1]

    def create_goodbye_response(self, userQuery):
        return constants.Responses.GOODBYE[1]

    def create_clarify_response(self, userQuery):
        return constants.Responses.CLARIFY[0]

    def create_specify_response(self, userQuery):
        return constants.Responses.SPECIFY[0]

    def create_pleasantry_response(self, userQuery):
        return constants.Responses.PLEASANTRY[0]

    def create_class_info_term(self, userQuery):
        return constants.Responses.CLASS_INFO_TERM[0].format(userQuery.object.name)

    def create_class_info_term_res(self, userQuery):
        s = constants.Responses.CLASS_INFO_TERM_RES[0]
        return s.format(userQuery.object.relevant_class.name, userQuery.object.relevant_class.term)

    def create_classes_info_prof_res(self, userQuery):
        s = constants.Responses.CLASSES_INFO_PROF_RES[0]
        class_str = ""
        if type(userQuery.object.relevant_class) == list:
            for course in userQuery.object.relevant_class:
                class_str += course.id + ": " + course.name + "\n"
        else:
            class_str = userQuery.object.relevant_class.id + ": " + userQuery.object.relevant_class.name
        return s.format(userQuery.object.relevant_class[0].prof, class_str)

    def create_class_info_name(self, userQuery):
        s = constants.Responses.CLASS_INFO_NAME[0]
        return s.format(userQuery.object.relevant_class.name)

    def create_class_info_name_res(self, userQuery):
        s = constants.Responses.CLASS_INFO_NAME_RES[0]
        return s.format(userQuery.object.relevant_class.name)

    def create_class_info_time(self, userQuery):
        s = constants.Responses.CLASS_INFO_TIME[0]
        return s.format(userQuery.object.relevant_class.name)

    def create_class_info_time_res(self, userQuery):
        s = constants.Responses.CLASS_INFO_TIME_RES[0]
        return s.format(userQuery.object.relevant_class.name, userQuery.object.relevant_class[0].time)

    def create_class_info_prof(self, userQuery):
        s = constants.Responses.CLASS_INFO_PROF[0]
        return s.format(userQuery.object.relevant_class.name)

    def create_class_info_prof_res(self, userQuery):
        s = constants.Responses.CLASS_INFO_PROF_RES[0]
        return s.format(userQuery.object.relevant_class.prof)

    def create_class_info_sentiment(self, userQuery):
        s = constants.Responses.CLASS_INFO_SENTIMENT[0]
        return s.format(userQuery.object.relevant_class.name)

    def create_class_info_scrunch(self, userQuery):
        s = constants.Responses.CLASS_INFO_SCRUNCH[0]
        return s.format(userQuery.object.relevant_class.name)

    def create_new_class_dept(self, userQuery):
        s = constants.Responses.NEW_CLASS_DEPT[0]
        return s

    def create_student_info_name(self, userQuery):
        s = constants.Responses.STUDENT_INFO_NAME[0]
        return s

    def create_student_info_major(self, userQuery):
        s = constants.Responses.STUDENT_INFO_MAJOR[0]
        return s

    def create_student_info_previous_classes(self, userQuery):
        s = constants.Responses.STUDENT_INFO_PREVIOUS_CLASSES[0]
        return s

    def create_student_info_interests(self, userQuery):
        s = constants.Responses.STUDENT_INFO_INTERESTS[0]
        return s

    def create_student_info_time_left(self, userQuery):
        s = constants.Responses.STUDENT_INFO_TIME_LEFT[0]
        return s

    def create_student_info_abroad(self, userQuery):
        s = constants.Responses.STUDENT_INFO_ABROAD[0]
        return s

    def create_student_info_requirements(self, userQuery):
        s = constants.Responses.STUDENT_INFO_REQUIREMENTS[0]
        return s

    def create_student_info_major_requirements(self, userQuery):
        s = constants.Responses.STUDENT_INFO_MAJOR_REQUIREMENTS[0]
        return s

    def create_new_class_name(self, userQuery):
        return constants.Responses.NEW_CLASS_NAME[0]

    def create_new_class_prof(self, userQuery):
        return constants.Responses.NEW_CLASS_PROF[0]

    def create_new_class_dept(self, userQuery):
        return constants.Responses.NEW_CLASS_DEPT[0]

    def create_new_class_sentiment(self, userQuery):
        s = constants.Responses.NEW_CLASS_SENTIMENT[0]
        return s.format(userQuery.object.relevant_class[0].name)

    def create_new_class_requirements(self, userQuery):
        return constants.Responses.NEW_CLASS_REQUIREMENTS[0]

    def create_new_class_time(self, userQuery):
        return constants.Responses.NEW_CLASS_TIME[0]

    def create_new_class_description(self, userQuery):
        '''s = constants.Responses.NEW_CLASS_DESCRIPTION[0]
        return s.format(userQuery.object.relevant_class[0].name, userQuery.object.relevant_class[0].description)'''
        s = constants.Responses.NEW_CLASS_DESCRIPTION[1]
        return s.format(userQuery.object.relevant_class[0].id, userQuery.object.relevant_class[0].name, userQuery.object.relevant_class[0].description)

    def create_schedule_class_res(self, userQuery):
        s = constants.Responses.SCHEDULE_CLASS_RES[0]
        course_list = ""
        for course in userQuery.object.current_classes:
            course_list += (course.name + "\n")
        return s.format(course_list)

    def create_full_schedule_check(self, userQuery):
        s = constants.Responses.FULL_SCHEDULE_CHECK[0]
        course_list = ""
        for course in userQuery.object.current_classes:
            course_list += (course.name + "\n")
        return s.format(course_list, userQuery.object.current_credits)

    def create_student_info_name_res(self, userQuery):
        s = constants.Responses.STUDENT_INFO_NAME_RES[0]
        return s.format(userQuery.object.name)

    def create_student_info_major_res(self, userQuery):
        s = constants.Responses.STUDENT_INFO_MAJOR_RES[0]
        if len(userQuery.object.major) == 1:
            return s.format(userQuery.object.major[0])
        elif len(userQuery.object.major) == 0:
            print("There are no majors")
            return s
        else:
            majors = userQuery.object.major[0] + " and " + userQuery.object.major[1]
            return s.format(majors)

    def create_student_info_previous_classes_res(self, userQuery):
        s = constants.Responses.STUDENT_INFO_PREVIOUS_CLASSES_RES[0]
        previous_classes = ""
        for course in userQuery.object.previous_classes:
            previous_classes += (course.name + "\n")
        return s.format(previous_classes)

    def create_student_info_interests_res(self, userQuery): 
        s = constants.Responses.STUDENT_INFO_INTERESTS_RES[0]
        interest_string = ""
        for interest in userQuery.object.interests:
            interest_string += (interest + "\n")
        return s

    def create_student_info_time_left_res(self, userQuery):
        s = constants.Responses.STUDENT_INFO_TIME_LEFT_RES[0]
        return s

    def create_student_info_abroad_res(self, userQuery):
        s = constants.Responses.STUDENT_INFO_ABROAD_RES[0]
        return s

    def create_student_info_requirements_res(self, userQuery):
        s = constants.Responses.STUDENT_INFO_REQUIREMENTS_RES[0]
        return s

    def create_student_info_major_requirements_res(self, userQuery):
        s = constants.Responses.STUDENT_INFO_MAJOR_REQUIREMENTS_RES[0]
        return s

    def create_student_info_concentration(self, userQuery):
        s = constants.Responses.STUDENT_INFO_CONCENTRATION[0]
        return s

    def create_student_info_concentration_res(self, userQuery):
        if len(userQuery.object.concentration) > 0:
            s = constants.Responses.STUDENT_INFO_CONCENTRATION_RES[0]
            concentration_string = ""
            for concentration in userQuery.object.concentration:
                concentration_string += (concentration + "\n")
            return s.format(concentration_string)

        else:
            s = constants.Responses.STUDENT_INFO_CONCENTRATION_RES[1] 
            return s

    def stem(self, s):
        return(self.stemmer.stem(s))

    def find_course(self, utterance):
        tokens = nltk.word_tokenize(utterance)
        pos = nltk.pos_tag(tokens)
        return [word for word,p in pos if p in ['JJ','NNP','NN']]

    def find_name(self, utterance):
        tokens = nltk.word_tokenize(utterance)
        pos = nltk.pos_tag(tokens)
        return [word for word,p in pos if p == 'NNP']

    def find_interests(self, utterance):
        return self.find_course(utterance)

#if __name__ == '__main__':
#    nluu = nLUU("https://api.projectoxford.ai/luis/v1/application?id=fc7758f9-4d40-4079-84d3-72d6ccbb3ad2&subscription-key=c18a6e7119874249927033e72b01aeea")
#    res = nluu.get_luis("when is Intro CS this year?")
#    print("res1:{}".format(res))
#    intents = res.intents
#    results = []
#    if intents[0].intent == 'StudentMajorResponse' or intents[0].intent == 'None':
#        line = res.query
#        pos = nluu.pos_tag(nluu.tokenize(line))
#        for word, p in pos:
#            if p == 'JJ' or p == 'NNP':
#                results.append(word)

#    if intents[0].intent == 'ClassDescriptionRequest':
#        pass
#    print("res: {}".format(" ".join(results)))
