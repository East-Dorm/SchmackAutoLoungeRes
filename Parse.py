import re
from datetime import datetime, timedelta
import string


# Our event info class
class EventInfo:
    def __init__(self, header: str):
        self.header = header
        self.requestInfoMaybe = False
        self.unadulterated_header = header
        self.definitly_a_lounge_res = False
        # Create time with an hour of 4. If the hour is four by the end, 
        # we will abort. ALso, get rid of microsecond bs
        self.time = datetime.today().replace(hour=21, minute=0, second=0, microsecond=0)
    
    def __str__(self):
        return f"{self.header} {self.time}"

    def __eq__(self, other):
        return str(self) == str(other)

def time_strip(event: EventInfo):
     # Using weekdays
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for i in range(len(days)):
        if days[i] in event.header:
            event.header = event.header.replace(days[i], "")
            event.time = event.time + timedelta(days = (i - event.time.weekday()) % 7)
    
    
    AreYouSureThisIsALoungeRes = False
    date = re.search(r'(\d{2})/(\d{2})', event.header)
    #try again, but for dates like 2/20
    if date is None:
        date = re.search(r'(\d{1})/(\d{2})', event.header)
    # for dates like 10/8
    if date is None:
        date = re.search(r'(\d{2})/(\d{1})', event.header)
    # for dates lke 2/3
    if date is None:
        date = re.search(r'(\d{1})/(\d{1})', event.header)
    
    if date is not None:
        AreYouSureThisIsALoungeRes = True
        event.time = event.time.replace(month=int(date.group(1)), day=int(date.group(2)))
        event.header = event.header.replace(date.group(0), "")
    


    # All useful potential patterns. The order matters because some would trigger the others
    timepatterns = [r'(\d{2}):(\d{2}) pm', r'(\d{2}):(\d{2})pm', r'(\d{1}):(\d{2}) pm' r'(\d{1}):(\d{2})pm', r'(\d{2}):(\d{2}) am', r'(\d{2}):(\d{2})am',
                     r'(\d{1):(\d{2})am', r'(\d{1):(\d{2}) am', r'at (\d{2}) am', r'at (\d{2}) pm', r'at (\d{1}) pm', r'at (\d{1}) am', r'(\d{2}):(\d{2})', r'(\d{1}):(\d{2})',
                        r'@(\d{1})pm', r'(\d{1}) pm',r'(\d{2}) pm', r'(\d{2})pm', r'(\d{2}) am', r'(\d{2})am', r'@(\d{1}) pm', r'@ (\d{1})', r'@(\d{1})', r'(\d{1})pm', r'at (\d{2})', r'at (\d{1})', r'(\d{1})pm',
                        r'(\d{1})am', r'(\d{1}) pm',r'(\d{1}) am'
                        ]
    for timepattern in timepatterns:
        time = re.search(timepattern, event.header)
        # check if am, else convert to pm
        if time is not None:
            AreYouSureThisIsALoungeRes = True
            potential_hour_delta = 0
            if "am" in timepattern:
                if time.group(1) == "12":
                    print("pweeese")
                    potential_hour_delta = -12
                event.time += timedelta(days=1)
            else:
                potential_hour_delta = 12
            # strip time
            event.header = event.header.replace(time.group(0), "")
            # set the time to the correct hour and minute
            try:
                event.time = event.time.replace(hour=int(time.group(1)) + potential_hour_delta, minute=int(time.group(2)))
            except:  
               pass
               event.time = event.time.replace(hour=int(time.group(1)) + potential_hour_delta)
            break


    # special cases
    if "tomorrow" in event.header:
        event.time += timedelta(days=1)
    if "afternoon" in event.header:
        event.time = event.time.replace(hour=15)
    if "now" in event.header:
        event.time = datetime.today().replace(second=0, microsecond=0)

    # find today, tonight, or tommorrow
    today_variants = ["today", "tonight", "tomorrow", "now", "this evening", "this afternoon", "afternoon", "evening"]
    for word in today_variants:
        if word in event.header:
            AreYouSureThisIsALoungeRes = True
            event.header = event.header.replace(word, "")


    if AreYouSureThisIsALoungeRes:
        event.definitly_a_lounge_res = True    

def yeet_these(event: EventInfo):
    """Clean Up! Clean Up!
    Everybody, Everywhere
    Clean Up! Clean Up!
    Everybody do your share

    Clean Up! Clean Up!
    Everybody, Everywhere
    Clean Up! Clean Up!
    Everybody do your share

    Clean Up! Clean Up!
    Everybody, Everywhere
    Clean Up! Clean Up!
    Everybody do your share"""
    #get rid of any extra words in parenthesis or brackets
    noBetween = ["(", ")", "[", "]"]
    for i in range(len(noBetween)//2):
        beginI = event.header.find(noBetween[2*1])
        endI = event.header.find(noBetween[2*i+1])
        if beginI != -1 and endI != -1:
            # remove everything in between
            event.header = event.header[:beginI] + event.header[endI+1:]


    yeetList = ["[", "]", "{", "}", ":", "(", ")", "@", " pm", "@", " at ", "/", ",", ".", "-", "approximately", "approx"]
    for char in yeetList:
        event.header = event.header.replace(char, "")
    
    listWords = event.header.split()
    BadEndings = ["on", "ish", "and", "this"]
    for word in BadEndings:
        if listWords[-1] == word:
            listWords.pop(-1)

    if listWords[0] == "re":
        listWords.pop(0)
    
    event.header = " ".join(listWords)


    """# get rid of extra spaces
    while "  " in event.header:
        event.header = event.header.replace("  ", " ")
    while event.header[0] == " ":
        event.header = event.header[1:]
    while event.header[-1] == " ":
        event.header = event.header[:-1]"""
    
def lounge_res_strip(event: EventInfo):
    isThisALoungeRes = False
    if "lounge res" in event.header:
        event.header = event.header.replace("lounge res", "")
        isThisALoungeRes = True
    if "loungeres" in event.header:
        event.header = event.header.replace("loungeres", "")
        isThisALoungeRes = True
    if "come see" in event.header:
        isThisALoungeRes = True
    if "come watch" in event.header:
        event.header = event.header.replace("come watch", "")
        isThisALoungeRes = True
    if "fmm" in event.header:
        # This is incomprehensible good luck. But we are just setting the date to  next friday
        # Note: -1 mod seven is 6
        event.time = event.time + timedelta(days = (4 - event.time.weekday()) % 7)
        event.time = event.time.replace(hour=0)
        event.header = event.header.replace("fmm", "")
        isThisALoungeRes = True
        # Worry about Mountain time
        if "mountain time" in event.header:
            event.header = event.header.replace("mountain time", "MOUNTAIN TIME FMM")
            event.time = event.time - timedelta(hours = 1)
        if "mt " in event.header:
            event.header = event.header.replace("mt", "MOUNTAIN TIME FMM")
            event.time = event.time - timedelta(hours = 1)
        event.definitly_a_lounge_res = True
    if "ttt" in event.header:
        event.time = event.time + timedelta(days = (1 - event.time.weekday()) % 7)
        isThisALoungeRes = True
        event.definitly_a_lounge_res = True
        event.header = event.header.replace("ttt", "")
    if "mmm" in event.header:
        event.time = event.time + timedelta(days = (0 - event.time.weekday()) % 7)
        isThisALoungeRes = True
        event.definitly_a_lounge_res = True
        event.header = event.header.replace("mmm", "")
    if "east dorm cinema" in event.header:
        isThisALoungeRes = True
        event.header = event.header.replace("east dorm cinema", "")
    if "res life" in event.header:
        isThisALoungeRes = True
        event.header = event.header.replace("Res Life", "")
    if "dorm meeting" in event.header:
        isThisALoungeRes = True
        event.header = event.header.replace("east dorm cinema", "")

    return isThisALoungeRes

# This is the main bad boy
def extract_event_info(original_header: str) -> EventInfo:
    """returns the title of the event and its datetime in an EventInfo variable"""
    # set up vars
    event = EventInfo(original_header)
    
    #lowercase the string
    event.header = event.header.lower()


    # Strip the lounge res, fmm, etc. and if there is none, don't send the api call to google calendar
    if not lounge_res_strip(event):
        # A returned title of meowzles indicates that there is no lounge res
        return EventInfo("meowzles")
         
    # Strip the time
    time_strip(event)
    if not event.definitly_a_lounge_res:
        event.requestInfoMaybe = True
        return EventInfo("meowzles")
    
    yeet_these(event)

    """if (len(event.header) < 20):
        event.header = event.unadulterated_header
    else:"""
    event.header = string.capwords(event.header, sep = None)
    print(event)
    return event