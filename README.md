# Making your advisor obsolete: A dialogue system (comps 2016-2017)

This projects is an attempt at a conversation machine to help register students for courses at Carleton College. We combine domain knowledge about Carleton, principles of conversations like Grice's maxims of conversation, and fundamental computer science principles to create a conversational structure and reactive system that can incorporate context and objectives to register a client for an upcoming Spring-term courseload. 

We have broken this project up into 3 main parts:
 * NLUU: Natural Language Understanding Unit
 * Dialogue Manager
 * Task Manager
 

## NLUU: Natural Language Understanding Unit

The NLUU is responsible for all things relating to natural language in both input and output. We rely on third-party libraries like python's `nltk` and Microsoft's LUIS (Language Understanding Intelligent Service) that deal with raw text and break it down into a number of useful ways. 
 
### nltk
We use `nltk` to extract parts of sentences that we believe are likely keywords and useful components of the client's sentiments, stripping away semantics. Additionally, we use `nltk`'s word stemmer and the operating system's list of words to create a dictionary whose keys are word stems and values are lists of words whose stem is the key. This is so that when "tree" and "trees" are one of the same. 

### LUIS
We use Microsoft's LUIS to extract intent from a client's response. We have trained the LUIS program on a number of utterances and flagged each as a particular intent. For instance, "Register me for math of cs" yields a `ScheduleClass` intent, meaning that the client wants to add a class to their schedule. We then use this knowledge of what the client wants to do to determine our next actions.


## Dialogue Manager
This is the real brains of the program in terms of conversation decision making and handling. A number of files in this folder are domain objects to help us group piece of information, such as courses and students. Every time the student asks about particular classes, each is filled out and manipulated using a `Course` object. Each conversation as well is given a `Student` object that holds information about previous things we have learned about the student as well as courses we've talked about. These are relatively brainless collections of data that do not provide functionality, except for a pretty way of printing to the terminal. The two main files in this domain are `Conversation.py` and `decision_tree.py`.

### Conversation
This file starts the conversation, enters a conversational loop, and handles all of the decision making given the current intent and the past context in which a particular utterance is made. For instance, "Put me in CS111" will give back the same `ScheduleClass` intent as before, and `Conversation` will determine that `CS111` is a course, query the database (via TaskManager) to fill out the information, and add it to the student's schedule. 

More interestingly, we handle more complicated interactions that last longer than a single input/output. For instance, say the client is interested in rocks. We query the database about classes that may have something to do with rocks and suggest 3-5 courses for the client to consider. They may wish to register for one of those courses, but colloquially referring to a listed course by its title may sound irregular. One would instead say "Register me for the 2nd one". Being able to understand the intent and the context is integral to producing the correct behavior. This is what `Conversation` attempts to do.


### Decision Tree
The decision tree is a tree of nodes that guide the conversation. We ask leading questions, respond to deviations in the trajectory in the conversation made by the client in intelligent ways that still allow us to accomplish our objective of registering the client for 3 courses. The order in which we ask questions and determining how questions have been answered or deflected is handled here. 


## Task Manager
This acts as an intelligent database. It has access to the real PostgreSQL database that houses information on courses, professors and a calculated keyword occurence matrix. 


