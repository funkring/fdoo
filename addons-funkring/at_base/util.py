# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-

#############################################################################
#
#    Copyright (c) 2007 Martin Reisenhofer <martin.reisenhofer@funkring.net>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from dateutil.relativedelta import relativedelta
from datetime import datetime
from datetime import date
import math
import re
import time
import base64
import tempfile
import random

DT_FORMAT = '%Y-%m-%d'
DHM_FORMAT = '%Y-%m-%d %H:%M:%S'
HM_FORMAT = '%H:%M:%S'
HM_FORMAT_SHORT = '%H:%M'

SEVERITY = [('0','Normal'),('1','Warning'),('2','Blocker')]
PRIORITY = [('0','Not urgent'),('1','Normal'),('2','Urgent'),('3','Very Urgent')]

PATTERN_ID = re.compile("([0-9]+)")

class DateSequenceEntry(object):
    """ A Date Sequence Entry """
    def __init__(self,inDate,inFinal=False,inSeq=-1):
        self.date=inDate
        self.finalSeq=inFinal
        self.seq=inSeq


def floatTimeConvert(float_val):
    if not float_val:
        return "00:00"

    hours = math.floor(abs(float_val))
    mins = round(abs(float_val)%1+0.01,2)
    if mins >= 1.0:
        hours = hours + 1
        mins = 0.0
    else:
        mins = mins * 60
    float_time = '%02d:%02d' % (hours,mins)
    return float_time

def setSubDictValue(inDict,key,subkey,value):
    if not value:
        return
    subDict = inDict.get(key,None)
    if not subDict:
        subDict={}
        inDict[key]=subDict
    subDict[subkey]=value

def timeToStrHours(inTime):
    if not inTime:
        return inTime
    if not isinstance(inTime,datetime):
        inTime = strToTime(inTime)
    return inTime.strftime(HM_FORMAT_SHORT)

def strToTime(inTime):
    if not inTime:
        return inTime
    if isinstance(inTime,datetime):
        return inTime
    return datetime.strptime(inTime,DHM_FORMAT)

def timeToStr(inTime):
    return datetime.strftime(inTime,DHM_FORMAT)

def timeToDate(inTime):
    time = strToTime(inTime)
    return date(time.year,time.month,time.day)

def dateOnlyStr(inTime):
    if inTime:
        return inTime.split(" ")[0]
    return None

def dateOnly(inTime):
    date = dateOnlyStr(inTime)
    return datetime(date.year,date.month,date.day)

def timeToDateStr(inTime):
    return dateToStr(timeToDate(inTime))

def dateToTimeStr(inDate):
    return timeToStr(strToDate(inDate))

def strToDate(inDate):
    if not inDate:
        return inDate

    if isinstance(inDate,datetime):
        return inDate

    return datetime.strptime(inDate, DT_FORMAT)

def formatDate(inDate,inFormat):
    inDate = strToDate(inDate)
    return datetime.strftime(inDate, inFormat)

def dateFormat(inDate,inFormat):
    resDate = strToDate(inDate)
    return datetime.strftime(resDate,inFormat)

def parseStrDate(inStr,inFormat):
    resDate = datetime.strptime(inStr,inFormat)
    return dateToStr(resDate)

def dateToStr(inDate):
    return datetime.strftime(inDate,DT_FORMAT)

def currentDate():
    return time.strftime(DT_FORMAT)

def currentDateTime():
    return time.strftime(DHM_FORMAT)

def nextMinute():
    return timeToStr(datetime.now()+relativedelta(minute=1))

def mergeTime(inTime1,inTime2):
    inTime1 = strToTime(inTime1)
    if not inTime1.hour and not inTime1.minute and not inTime1.second:
        inTime2 = strToTime(inTime2)
        return datetime(inTime1.year,inTime1.month,inTime1.day,inTime2.hour,inTime2.minute,inTime2.second)
    return inTime1

def mergeTimeStr(inTime1,inTime2):
    return timeToStr(mergeTime(inTime1,inTime2))

def formatToMonthDate(inDate):
    return datetime.strftime(strToDate(inDate),"%m.%Y")

def getNextDayOfMonthDate(inDate,inDay=-1,inMonth=1):
    if inDay >= 1:
        inDay -= 1

    day =  date(inDate.year,inDate.month,1);
    day += relativedelta(months=inMonth)
    day += relativedelta(days=inDay)

#    if day <= date(inDate.year,inDate.month,inDate.day):
#        day =  date(inDate.year,inDate.month,1);
#        day += relativedelta(months=1)
#        day += relativedelta(months=inMonth)
#        day += relativedelta(days=1)
#        day += relativedelta(days=inDay)

    return day


def getNextDayOfMonth(inDate,inDay=-1,inMonth=1):
    """ Get next day of month """
    return dateToStr(getNextDayOfMonthDate(strToDate(inDate),inDay=inDay,inMonth=inMonth))

def getFirstOfMonth(inDate):
    if not inDate:
        return inDate
    inDate = strToDate(inDate)
    return dateToStr(date(inDate.year,inDate.month,1))

def getEndOfMonth(inDate):
    return getNextDayOfMonth(inDate)


def getNextDayDate(inDate):
    day =  date(inDate.year,inDate.month,inDate.day);
    day += relativedelta(days=1)
    return day


def getNextDayDateTime(inDate):
    day =  datetime(inDate.year,inDate.month,inDate.day);
    day += relativedelta(days=1)
    return day

#def getEndOfDayDate(inDate):
#    day =  date(inDate.year,inDate.month,inDate.day);
#    day += relativedelta(days=1)
#    return day
#
#def getEndOfDayDateTime(inDate):
#    day =  datetime(inDate.year,inDate.month,inDate.day);
#    day += relativedelta(days=1)
#    return day

def getLastTimeOfDay(inDate):
    day =  datetime(inDate.year,inDate.month,inDate.day);
    day += relativedelta(days=1)
    day -= relativedelta(seconds=1)
    return day

def getDateSequence(inStartSeq,inSeq,inCurrentDate,inMaxMonths=0,inDay=-1):
    """ get sequence for the passed date
        @param:  inMaxMonths the max month of a period
        @return: a Sequence of DateSequenceEntry
    """
    resSeq = []
    if not inSeq:
        return resSeq

    if not inStartSeq:
        return resSeq

    #convert dates
    inStartSeq = strToDate(inStartSeq)
    inCurrentDate = strToDate(inCurrentDate)

    #get months
    startSeqMonth = (inStartSeq.year*12)+inStartSeq.month-1
    lastDateMonth = (inCurrentDate.year*12)+inCurrentDate.month-1

    #get last seq month
    lastSeqMonth=inSeq[-1]
    if lastSeqMonth==0:
        lastSeqMonth=1

    #get month and period count
    months = lastDateMonth-startSeqMonth
    periodCount = int(math.floor((lastDateMonth-startSeqMonth) / lastSeqMonth))

    #check if sequence is over
    if inMaxMonths and periodCount >= 1 and months > inMaxMonths:
        return resSeq

    #get sequences
    nextStartSeq = inStartSeq + relativedelta(months=periodCount*lastSeqMonth)
    for seq in inSeq:
        cur = getNextDayOfMonth(nextStartSeq+relativedelta(months=seq-1),inDay=inDay)
        resSeq.append(DateSequenceEntry(cur,inSeq=seq))

    #check if it is last sequence
    if resSeq:
        if inMaxMonths:
            seqEntry = resSeq[-1]
            inMaxDate = getNextDayOfMonth(inStartSeq+relativedelta(months=inMaxMonths-1),inDay=inDay)
            if seqEntry.date >= inMaxDate:
                seqEntry.finalSeq = True

    return resSeq


def getNextSequenceEntry(inStartSeq,inSeq,inLastDate,inMaxMonths=0,inDay=-1):
    """ get next entry of sequence
    @param inStartSeq: Start Date of Sequence
    @param inSeq: Sequence Pattern (Months)
    @param inLastDate: Last Sequene Date
    @param inMaxMonth: Maximum Month of the Sequence
    @param inDay: Day wenn the Sequence start -1 Last Day of current Month, 1 first day of next month,
                  0 first day of current month
    """

    if not inLastDate or inStartSeq == inLastDate:
        seqEntries =  getDateSequence(inStartSeq,inSeq,inStartSeq,inMaxMonths,inDay)
        if seqEntries:
            return seqEntries[0]

    else:
        inLastDate = strToDate(inLastDate)
        inLastDate += relativedelta(days=1)
        inLastDate = dateToStr(inLastDate)
        seqEntries =  getDateSequence(inStartSeq,inSeq,inLastDate,inMaxMonths,inDay)
        for entry in seqEntries:
            if entry.date > inLastDate:
                return entry

    return None


def getNextDaysOfMonths(inFromDate, inToDate,day=-1,month=1):
    """ Get a list of last day beetween two dates """

    inFromDate = getNextDayOfMonthDate(strToDate(inFromDate),day=day,month=month)
    inToDate = getNextDayOfMonthDate(strToDate(inToDate),day=day,month=month)

    day = inFromDate
    delta = relativedelta(months=1)

    res = []
    while day <= inToDate:
        res.append(dateToStr(day))
        day += delta
        day = getNextDayOfMonthDate(day,day=day,month=month)

    return res


def getMonths(inFromDate, inToDate):
    """ Get Month beetween two Dates"""

    inFromDate = strToDate(inFromDate)
    inToDate = strToDate(inToDate)

    i = inFromDate
    delta = relativedelta(months=1)
    months=0
    date
    while i <= inToDate:
        months+=1
        i+=delta

    if months > 0:
        return months

    return 1


def cleanFileName(inName):
    repl_map = {
            "Ö" : "Oe",
            "Ü" : "Ue",
            "Ä" : "Ae",
            "ö" : "oe",
            "ü" : "ue",
            "ä" : "ae"
    }


    for key,value in repl_map.iteritems():
        inName = inName.replace(key,value)

    inName = inName.replace(", ","_")
    inName = inName.replace(" ","_")
    inName = re.sub("[^a-zA-Z0-9\-_ ,]","",inName)
    return inName

def toList(inStr):
    strList = [str(x) for x in inStr]
    res = ",".join(strList)
    return "(%s)" % (res,)

def idFirst(inIds):
    if isinstance(inIds, (int, long, float)):
        return inIds
    if isinstance(inIds, (list,tuple)) and inIds:
        return inIds[0]
    return None

def idList(inIds):
    if isinstance(inIds, (int, long, float)):
        inIds = [inIds]
    return inIds

def createTempFileFromBinary(ext,data=None,datas=None):
    data = (datas and base64.decodestring(datas)) or data
    if data and ext:
        tempFile = tempfile.mktemp(ext)
        fp = open(tempFile,"wb")
        try:
            fp.write(data)
        finally:
            fp.close()
        return tempFile
    return None

def model_get(inContext):
    data = inContext.get("data")
    model = data and data.get("model") or inContext.get("active_model") or None
    return model

def active_ids(inContext,inObj=None):
    if inContext:
        active_ids = inContext.get("active_ids")
        if not active_ids:
            active_id = inContext.get("active_id")
            if active_id:
                active_ids = [active_id]
        active_model = inContext.get("active_model")
        if inObj:
            if not isinstance(inObj,basestring):
                inObj=inObj._name
            if active_ids and active_model==inObj:
                return active_ids
        elif active_ids:
            return active_ids
    return []

def active_id(inContext,inObj=None):
    ids = active_ids(inContext,inObj)
    return ids and ids[0] or None

def removeIfEmpty(d,key):
    if d.has_key(key):
        val = d.get(key)
        if not val:
            del d[key]

def data_get(inContext,multi=False):
    data = inContext.get("data")
    if not data:
        model = inContext.get("active_model")
        ids = inContext.get("active_ids")
        oid = ids and ids[0] or inContext.get("active_id") or None
        if model and oid:
            data = {
              "model" : model,
              "id" : oid
            }
            if multi:
                if ids:
                    data["ids"]=ids
                else:
                    data["ids"]=[oid]
    return data or {}

def password(size=10,charset="abcdefghijklmnopqrstuvwxyz0123456789"):
    chars = []
    i=0
    while i<size:
        chars.append(random.choice(charset))
        i+=1
    return "".join(chars)

def bits(value):
    bits = 0
    while (value >= (1 << bits)):
        bits+=1
    return bits

def writeProperties(path,properties,bool_true="true",bool_false="false"):
    f = open(path,"w")
    try:
        for key,value in properties.items():
            str_value=""
            if type(value) is bool:
                str_value=value and bool_true or bool_false
            elif value or type(value) in (int,long,float):
                str_value=str(value)
            f.write("%s=%s\n" % (key,str_value))
    finally:
        f.close()

def datePrivious(inDate):
    inDate = strToDate(inDate)
    day =  date(inDate.year,inDate.month,inDate.day);
    day -= relativedelta(days=1)
    return day

def dateEasterSunday(inYear):
    a =  inYear % 19
    k = inYear / 100
    m = 15 + (3*k + 3) / 4 - (8*k + 13) / 25
    d = (19*a + m) % 30
    s = 2 - (3*k + 3) / 4
    r = (d + a / 11) / 29
    og = 21 + d - r
    sz = 7 - (inYear + inYear / 4 + s) % 7
    oe = 7 - (og - sz) % 7
    os = (og + oe)-1
    easter_sunday = date(inYear,3,1)
    easter_sunday += relativedelta(days=os)
    return easter_sunday

def sumUp(dictBase,dictOther):
    for key, otherValue in dictOther.items():
        if isinstance(otherValue, dict):
            value = dictBase.get(key)
            if not value:
                dictBase[key]=otherValue
            else:
                sumUp(value,otherValue)
        elif type(otherValue) in (long,int,float):
            value = dictBase.get(key)
            if not value:
                dictBase[key]=otherValue
            else:
                dictBase[key]=value+otherValue
    return dictBase

def getNames(values):
    """ return the names from the value record dict as list """
    res = []
    if not values:
        return res
    for key,value in values.items():
        if key=="id":
            continue
        if isinstance(value,tuple):
            res.append(value[1])
        else:
            res.append(value)
    return res

def getId(val):
    """ Parses an Id or return None if id is unparseable """
    if not val:
        return None
    if isinstance(val,int):
        return val
    if isinstance(val,float):
        return int(val)
    if isinstance(val,basestring):
        m=PATTERN_ID.match(val)
        if m:
            return int(m.group(1))
    return None

if __name__ == '__main__':
    print dateEasterSunday(2013)-dateEasterSunday(2012)
#     print password(32)
#
#     res = getDateSequence("2011-04-01",[1,2,3,4,5,6],"2011-04-01",6,inDay=-1)
#     for seqEntry in res:
#         if seqEntry.finalSeq:
#             print "Last Sequence: "
#         print seqEntry.date
#
#     print ""
#
#     startDate = "2011-04-01"
#     lastDate = "2011-04-01"
#     while True:
#         nextData = getNextSequenceEntry(startDate, [1,2,3,4,5,6], lastDate, 6, -1)
#         if not nextData:
#             print "No next data found"
#             break;
#
#         if nextData.finalSeq:
#             print "Final Sequence " + nextData.date
#             break;
#         else:
#             print nextData.date
#
#         lastDate = nextData.date
#
#     pass
