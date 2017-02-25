import psycopg2

def parse_time_room(str_in):
    if str_in.isspace():
        return None
    elif str_in == "":
        return None
    elif str_in == None:
        return None

    classroom = ""
    meeting_times = []

    meeting_strings = str_in.split('|')

    for meeting_string in meeting_strings:
        meeting_list = meeting_string.split()
        if len(meeting_list) < 2 or len(meeting_list) > 5:
            return None
        else:
            if classroom == "":
                classroom = meeting_list[0] + " " + meeting_list[1]
            if meeting_list[2] == "TBA" or meeting_list[3] == "TBA":
                break
            elif len(meeting_list) == 5:
                meeting = [meeting_list[2]]
                meeting.append((meeting_list[3].lstrip('0'), meeting_list[4].lstrip('0')))
                meeting_times.append(meeting)
            else:
                break

    return (classroom, meeting_times)

global conn
conn = psycopg2.connect(host = "cmc307-07.mathcs.carleton.edu", \
database = "dialogcomps", user = "dialogcomps", password = "dialog!=comps")

cur = conn.cursor()
query_string = "SELECT * FROM COURSE WHERE ((sec_term LIKE '17%') AND sec_term NOT LIKE '%SU') AND sec_name NOT LIKE '%WL%'"

cur.execute(query_string)
results = cur.fetchall()

for result in results:
    if result[24] != None:
        try:
            res = parse_time_room(result[24])
            print(res)
        except:
            print("EXCEPTION!")
            print("\n")
            print(result[24])
            print("\n")

print(len(results))
