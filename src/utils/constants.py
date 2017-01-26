class Responses:
    WELCOME = ("Hello, how are you?",
                "Sup dude")
    GOODBYE = ("Goodbye, {}",
               "See ya")
    CLARIFY = ("Could you clarify what you just said?",)
    SPECIFY = ("Can you be more specific on that regard?",)
    PLEASANTRY = ("Suh",)
    STUDENT_INFO_NAME = ("What's your name?",)
    STUDENT_INFO_MAJOR = ("What's your major?",)
    STUDENT_INFO_PREVIOUS_CLASSES = ("Can you tell me about classes you've already taken?",)
    STUDENT_INFO_INTERESTS = ("What are some of your interests?",)
    STUDENT_INFO_TIME_LEFT = ("How many terms do you have left at Carleton?",)
    STUDENT_INFO_ABROAD = ("Do you have any plans to study abroad?",)
    STUDENT_INFO_REQUIREMENTS = ("Are there any general graduation requirements you still need to complete?",)
    STUDENT_INFO_MAJOR_REQUIREMENTS = ("Are there any requirements for your major that you still need to complete?",)
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
    NEW_CLASS_NAME = ("Are there any classes that you'd like to take?",)
    NEW_CLASS_PROF = ("Is there a professor that you'd like to take a class with?",)
    NEW_CLASS_DEPT = ("Do you want to take a class in any particular department?",)
    NEW_CLASS_SENTIMENT = ("What do you think about taking {}?",)
    NEW_CLASS_REQUIREMENTS = ("Which requirements would you like to complete?",)
    NEW_CLASS_TIME = ("What time of day would you like your classes to be?",)
    NEW_CLASS_DESCRIPTION = ("Here's some more information about the class you asked about:\n {}:\n {}.",)
    SCHEDULE_CLASS_RES = ("Here are the classes you're currently registered for:\n {}.",)
    FULL_SCHEDULE_CHECK = ("Here are the classes you're currently registered for:\n {} You're registered for {} credits, do you want to register for more classes?",)