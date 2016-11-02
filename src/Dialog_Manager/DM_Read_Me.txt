We're making a dialog manager. Here's how we think its gonna work.

1. We get an input from the NLU Unit. They give us a parsed, tokenized, syntax tree as well as LUIS object
that analyzed intent and entities from each sentence of input.

2. We decide what the intent of each sentence is based on LUIS probabilities, as well as mining the input tree for
 special parts of speech (nouns, adjectives, verbs).

3. Depending on the type of noun/adjective we're looking at, we use LUIS's entity weights to figure out what exactly
that noun/adjective is talking about

4. Mine information from sentence and store it. This is dependent on what the entities are we create or populate
different objects. Note, this may require a relation extractor.
4a. If the subject in question is a professor, try to identify which course he or she is being referenced with respect to
if we find one, add the prof to the class object, else add them to the general positive or negative interest lists of
the student.
4b. If the subject in question is a class, see is the class is already in the student's taken or current classes. If not,
create a class object. Depending on the verb used when refering to the class, either add it to the potential class list(?)
the past class list or the current class list.
4c. If the adjective or verb is a sentiment, identify what the sentiment is connected to and add it to the subject
in question.
4d. Similar cases with department, student themselves, or any other case we can think of.

5. For any edited object, call a task manager to gain as much additional information about object as possible.

6. If more important is still required, add a query to the priority queue asking for more information about the object
in question

7. If they asked a question, check if we already have information to answer question. If so, add the response with
priority. If not, ask task manager specifically for information. If still lacking requisite information, figure out
what more info is needed to answer question, and add that to top of prio Q.

8. Call task manager with information asking for course reccomendations. If probable interest is high enough,
add reccomendation to prio Q.

9. Send top of prio Q to NLU Unit.

10. Rinse, repeat.