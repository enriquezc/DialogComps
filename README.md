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
The Task Manager acts as an intelligent connection to the database that organizes particular results it returns before sending them back to the Dialogue Manager. It has access to the PostgreSQL server that houses information on courses, professors and a calculated keyword occurrence matrix. The Task Manager uses a wide range of query functions to construct a SQL query, executes that query, and then, depending on the type of request from the Dialogue Manager, decides what courses need to returned first.

The functions that rely on this organization are functions like `query_by_keywords` and `query_by_distribution`, where the order of the returned courses has the ability to define what courses the user will look at in a possibly enormous selection of results. The construction of these course objects happens in a helper function called `fill_out_courses`, which uses the returned SQL query results, and simply fills out the corresponding information in the course object. The actual organization of these courses relies on another helper function called `calculate_course_relevance`, which assigns a score to the `weighted_sum` attribute based on the diversity of keywords that occur in the title and description, the total count of keywords that occur, the department the course exists in, and the other interests that the student has previously mentioned, passed to us as `student_interests`. The function `query_by_distribution` doesn’t have a list of keywords as input, so instead, the Dialogue Manager passes previous interests, and those are used as keywords to adjust the order of the courses returned.

The weights accompanied to these measures of relevance is arbitrary, chosen by the comps group on the basis that it was an approximate way of representing which courses were more important to students. Weighing options differently could affect what kind of courses appear first in the list of returned courses. Adjusting the weights assigned is as easy as changing the contents of `weights`, a list of the weights to be assigned in `calculate_course_relevance`. 

The task manager is also responsible for correctly assigning what majors and concentrations students are using based on dictionaries called `major_dict` and `concentration_dict`. Functions like `major_match` and `concentration_match` use edit distance to determine what major or concentration the student was discussing. The long form is returned for printing purposes (as opposed to the short form four letter code, e.g. “ECON”).

## Occurrence Matrix
The occurrence matrix consists of the series of words in the course descriptions and titles organized in rows, aligned with the occurrence of that particular word in the department that is represented by the column. This is referred to as a text-document matrix in Jurafsky and Martin’s Speech and Language Processing.

In this particular case, we used departments as documents because the individual courses do not contain enough words for the occurrence matrix to be of any use. Jurafsky and Martin recommend 10,000 words per document, hence using the entire department, which should provide enough words to appropriately match the needs of the text-document literature.

The function responsible for creating the occurrence matrix is called `make_occurrence_matrix` in the Task Manager.


