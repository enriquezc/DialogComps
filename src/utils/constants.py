class Responses:
    WELCOME = ("Hi, my name is DLNbot3000. Welcome to my office!\nAsk me about a specific course, or tell me some of your interests and I can find a related course.",)
    GOODBYE = ("Goodbye, {}",
               "See ya",
               "Smell ya later!",)
    CLARIFY = ("Could you clarify what you just said?",
               "I'm not sure I understand, could you repeat that?",
               "Hmmm, I don't quite follow. Maybe ask me in a different manner?",
               "I'm sorry, I didn't get that. Could you clarify?",
               )
    TM_CLARIFY = ("I wasn't able to find anything related to what you just said. Please ask me about something else.",)
    TM_COURSE_CLARIFY = ("I couldn't find a course related to that. Maybe it isn't offered at Carleton?.", )
    SPECIFY = ("Can you be more specific on that regard?",)
    PLEASANTRY = ("Suh",)
    STUDENT_INFO_NAME = ("What's your name?",)
    STUDENT_INFO_NAME_RES = ("Nice to meet you, {}.",
                             "Nice to meet you.",)
    STUDENT_INFO_MAJOR = ("What's your major?",)
    STUDENT_INFO_MAJOR_RES = ("Okay, you're a {} major.",
                              "{} major, huh? I've heard they're the best students.",
                              "So you haven't chosen your major yet?",)
    STUDENT_INFO_CONCENTRATION = ("Do you have a concentration? If so, what is it?",)
    STUDENT_INFO_CONCENTRATION_RES = ("Okay, so your concentrations include: {}",
                                      "Okay, you don't have any concentrations.")
    STUDENT_INFO_PREVIOUS_CLASSES = ("Can you tell me about classes you've already taken?",)
    STUDENT_INFO_PREVIOUS_CLASSES_RES = ("I'll try to find classes for you to look at other than:\n {}",)
    STUDENT_INFO_INTERESTS = ("What are some of your interests?",)
    STUDENT_INFO_INTERESTS_RESA = ("I'll try to find some classes for you to look at that relate to your interests:\n ")
    STUDENT_INFO_INTERESTS_RESB = ('{}',)
    STUDENT_INFO_TIME_LEFT = ("What class year are you?",)
    STUDENT_INFO_TIME_LEFT_RES = ("I'll keep that in mind while I'm helping you out.",)
    STUDENT_INFO_ABROAD = ("Do you have any plans to study abroad?",)
    STUDENT_INFO_ABROAD_RES = ("That sounds like an awesome experience.",)
    STUDENT_INFO_REQUIREMENTS = ("Which, if any, general graduation requirements (distros) do you still need to complete?",
                                 "Are there any general graduation requirements (distros) you still need to complete?",)
    STUDENT_INFO_REQUIREMENTS_RES = ("Let's try to find some courses to fill these requirements.",
                                     "Here are some classes that fill general requirements that you still need:\n{}",)
    STUDENT_INFO_MAJOR_REQUIREMENTS = ("What classes, if any, do you need to take to complete your major?",)
    STUDENT_INFO_MAJOR_REQUIREMENTS_RES = ("Let's try to find some classes to fill these requirements.\n",)
    CLASS_INFO_NAME = ("What is the name of {}?",)
    CLASS_INFO_NAME_RES = ("{} is the official name.",)
    CLASS_INFO_PROF = ("Which professor taught {}?",)
    CLASS_INFO_PROF_RES = ("{} taught this class.",)
    CLASSES_INFO_PROF_RES = ("{} taught these classes: {}",)
    CLASS_INFO_TERM = ("What term did you take {}?",)
    CLASS_INFO_TERM_RES = ("{} is offered in the {}",)
    CLASS_INFO_SENTIMENT = ("What did you think of {}?",)
    CLASS_INFO_SENTIMENT_EXTENDED = ("Which parts of {} did you like or dislike?",)
    CLASS_INFO_SCRUNCH = ("Did you scrunch {}?",)
    CLASS_INFO_TIME = ("What time was {}?",)
    CLASS_INFO_TIME_RES = ("{} is during {}.",)
    CLASS_INFO_DISTRIBUTIONS = ("Would you like to fulfill some of those requirements this term?",)
    CLASS_INFO_DISTRIBUTIONS_RES = ("{}",)
    NEW_CLASS_NAME = ("What is the name of a class you'd like to take?",
                      "Are there any classes that you'd like to take?",)
    NEW_CLASS_PROF = ("Is there a professor that you'd like to take a class with?",)
    NEW_CLASS_DEPT = ("Do you want to take a class in any particular department?",)
    NEW_CLASS_SENTIMENT = ("What do you think about taking {}?",)
    NEW_CLASS_REQUIREMENTS = ("Which requirements would you like to complete?",)
    NEW_CLASS_TIME = ("What time of day would you like your classes to be?",)
    NEW_CLASS_DESCRIPTIONA = ("So, here's what I know about {}.\n {} is available next term at {}, taught by {}.",)
    NEW_CLASS_DESCRIPTIONB = ("So, here's what I know about {}.\n {} is available next term at {}",)
    NEW_CLASS_DESCRIPTIONC = ("\n {}. Here's its official description:\n {}",)
    SCHEDULE_CLASS_RES = ("You are registered for {} credits. \nHere are the classes you're currently registered for:\n{}",)
    EMPTY_SCHEDULE_RES = ("You are not currently registered for any classes.",)
    FULL_SCHEDULE_CHECK = ("Here are the classes you're currently registered for:\n{}You're registered for {} credits, do you want to register for more classes?",)
    ALREADY_TALKED_ABOUT = ("We already talked about all the relevant courses to these interests. Ask about something else.",)
