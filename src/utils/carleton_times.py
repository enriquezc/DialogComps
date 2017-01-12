from enum import Enum
from datetime import time

class Times(Enum):
	ONEA = 1
	TWOA = 2
	THREEA = 3
	FOURA = 4
	FIVEA = 6
	OTC = 7
	TTC = 8
	FVC = 9
	FSC = 10

	times = {
		1: (1,time(8,30), time(9,40)),
		2: (1,time(9,50), time(11,0)),
		3: (1,time(11,10), time(12,20)),
		4: (1,time(12,30), time(13,40)),
		5: (1,time(13,50), time(15,0)),
		6: (1,time(15,10), time(16,20)),
		7: (2,time(8,15), time(10,0)),
		8: (2,time(10,10), time(11,55)),
		9: (2,time(13,15), time(15,0)),
		10: (2,time(15,10), time(16,55)),
	}

	def describe(self):
        # self is the member here
        return self.name, self.value

    def get_times(self):
    	return times[self.value]

    def overlaps(self, day, start_hour, start_minute, end_hour, end_minute):
    	(i, start, end) = self.get_times()
    	if (day % 2 == 0 and i == 1) or (day % 2 == 1 and i == 2):
    		return False
    	else:
    		if start_hour < start and end_hour < start:
    			return False
    		elif end_hour > end and start_hour > end:
    			return False
    		else:
    			return True
