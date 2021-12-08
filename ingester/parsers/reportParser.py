#! /usr/bin/env python
# -*- coding utf utf-8 -*-

import sys
import pydicom
import json
import os
import copy
import xml.etree.ElementTree as ET

import parsers.xmlTools as EX
srData = { "name" : "Adult Echocardiography Report",
        "report" : {
        "patient" : {},
        "findingSite" : [],
        "userDefined" : []
        }
    }

lastUserDefinedKey = ''
    



def processChild(dataSet, level, parent, elements, child):
    counter = 0
    spaces = "     " * level

   

    for i in dataSet:
        #print(spaces + "Relationship type " + EX.toStr(i.get(pydicom.tag.Tag(0x0040, 0xa010)).value))
        #print(spaces + "Value Type " + EX.toStr(i.get(pydicom.tag.Tag(0x0040, 0xa040)).value))
        #print(i)

        #EX.toStr(dataSet.get(pydicom.tag.Tag(0x0010, 0x0020)).value)

        value = spaces;
        label = ""
        val = ""
        key= ""
        unit=""
       
        if i.get(pydicom.tag.Tag(0x0040, 0xa040)).value == "TEXT":
            conceptNameCodeDataSet = i.get(pydicom.tag.Tag(0x0040, 0xa043)).value[0]
            value += EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value) + ": " + i.get(pydicom.tag.Tag(0x0040, 0xa160)).value
            key = EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
            val = i.get(pydicom.tag.Tag(0x0040, 0xa160)).value
            unit = ""
            if(parent == "Label"):
                labelKey = val;


        elif i.get(pydicom.tag.Tag(0x0040, 0xa040)).value == "PNAME":
            value += EX.toStr(i.get(pydicom.tag.Tag(0x0040, 0xa123)).value)

        # TODO(Josue) this one can have more than one, fix this
        elif i.get(pydicom.tag.Tag(0x0040, 0xa040)).value == "NUM":
            measuredValueDataSet = i.get(pydicom.tag.Tag(0x0040, 0xa300)).value[0]
            measuredUnitDataSet = measuredValueDataSet.get(pydicom.tag.Tag(0x0040, 0x08ea)).value[0]
            conceptNameCodeDataSet = i.get(pydicom.tag.Tag(0x0040, 0xa043)).value[0]            
            value += EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value) + ": " + EX.toStr(measuredValueDataSet.get(pydicom.tag.Tag(0x0040, 0xa30a)).value) + " " + EX.toStr(measuredUnitDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
            key = EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
            val = EX.toStr(measuredValueDataSet.get(pydicom.tag.Tag(0x0040, 0xa30a)).value) 
            unit = EX.toStr(measuredUnitDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)

        elif i.get(pydicom.tag.Tag(0x0040, 0xa040)).value == "CODE":
            conceptCodeDataSet = i.get(pydicom.tag.Tag(0x0040, 0xa168)).value[0]
            conceptNameCodeDataSet = i.get(pydicom.tag.Tag(0x0040, 0xa043)).value[0]
            value += EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value) + ": " + EX.toStr(conceptCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
            key = EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
            val = EX.toStr(conceptCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
            unit = ""

        elif i.get(pydicom.tag.Tag(0x0040, 0xa040)).value == "DATETIME":
            conceptNameCodeDataSet = i.get(pydicom.tag.Tag(0x0040, 0xa043)).value[0]
            value += EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value) + ": " + EX.toStr(i.get(pydicom.tag.Tag(0x0040, 0xa120)).value)
            key = EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
            val = EX.toStr(i.get(pydicom.tag.Tag(0x0040, 0xa120)).value)
            unit = ""

        elif i.get(pydicom.tag.Tag(0x0040, 0xa040)).value == "DATE":
            conceptNameCodeDataSet = i.get(pydicom.tag.Tag(0x0040, 0xa043)).value[0]
            value += EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value) + ": " + EX.toStr(i.get(pydicom.tag.Tag(0x0040, 0xa121)).value)
            key = EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
            val = EX.toStr(i.get(pydicom.tag.Tag(0x0040, 0xa121)).value)
            unit = ""
            
        elif i.get(pydicom.tag.Tag(0x0040, 0xa040)).value == "UIDREF":
            value += EX.toStr(i.get(pydicom.tag.Tag(0x0040, 0xa124)).value)


        if val is not None:
            #print(value)
            if key == "Finding Site"  and level != 3:
                parent = key
                child = val
                srData["report"]["findingSite"].append(createFindingSite(child))

        if val is not None:
            #print(value)
            if key == "Label"  and level == 2:
                parent = key
                label = val
                #srData["report"]["findingSite"].append(createFindingSite("userDefined"))
                            
            

        if key != "" and val != "" and key != "Finding Site" :
            fillSRData(key, val, unit, parent, child, level, label)

        contentSequence = i.get(pydicom.tag.Tag(0x0040, 0xa730))
        #print("\n" + spaces + "Child " + str(counter) + ", level " + str(level))
        if contentSequence is not None:
            #print(spaces + "Entering level ------------" + str(level + 1))            
            processChild(contentSequence.value, level + 1, parent, elements, child)
            #print(spaces + "Exiting level ------------" + str(level + 1))            
        counter += 1
        elements[0] += 1

def chechIfAlreadyExist(data, key, value, unit):
    for item in data:
       
        if(item["Key"] == key and item["Value"] == value):
            return False
    return True

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def fillSRData(key, value, unit, parent, currentChild, level, label):
    obj = {}


    if parent == "Finding Site":
        if level == 2:
            index = len( srData["report"]["findingSite"])

            index2 = len(srData["report"]["findingSite"][index -1]["measurements"])

            srData["report"]["findingSite"][index -1]["measurements"]
            valueNumber = ''
            if(is_number(value)):
                valueNumber = '{:.2f}'.format(float(value))
            else:
                valueNumber = value    
            
            res = chechIfAlreadyExist(srData["report"]["findingSite"][index -1]["measurements"], key.replace("'", ""), valueNumber, unit)
            if(res):
                if(unit != ""):
                    srData["report"]["findingSite"][index -1]["measurements"].append( {
                        "Key": key.replace("'", ""),
                        "Value": valueNumber,
                        "Unit": unit,
                        "Infos": []
                    })
                #print("-->" +key + ": " + value + " " + unit)
        if level == 3:
            index = len( srData["report"]["findingSite"])
            index2 = len(srData["report"]["findingSite"][index -1]["measurements"])
            if(index > 0 and index2 > 0):
                valueNumber = ''
                if(is_number(value)):
                    valueNumber = '{:.2f}'.format(float(value))
                else:
                    valueNumber = value           
                res = res = chechIfAlreadyExist(srData["report"]["findingSite"][index -1]["measurements"][index2-1]["Infos"], key.replace("'", ""), valueNumber, unit)
                if(res):
                    srData["report"]["findingSite"][index -1]["measurements"][index2-1]["Infos"].append({"Key": key.replace("'", ""), "Value": valueNumber})
                    


    if parent == "patient":
        key1 = key.replace(' ', '_')
        obj[key1] = value
        srData["report"]["patient"] |= obj

    if parent == "Label":        
        if(key == 'Label'):
            #obj[key + value] = value
            #srData["report"]["userDefined"].append({"Key": key.replace("'", ""), "Value": value})
            global lastUserDefinedKey
            lastUserDefinedKey = value
        if(label == ''):
            #obj[key + value] = value
            if(unit == '' ):
                unit = 'no units'
           
            if(is_number(value) ):
                srData["report"]["userDefined"].append({"Key": lastUserDefinedKey.replace("'", ""), "Value": '{:.2f}'.format(float(value)), "Unit": unit})
        


    

def createFindingSite(Name):
    return { "Name": Name,
    "measurements": []
    }

def generateMeasurmentAvg(data):
    avgs = copy.deepcopy(data)
    index = 0;
    for item in data["report"]["findingSite"]:
        msAvgs = {
            "Name": item["Name"],
            "Avgs": []
        }

        print(item["Name"])
        prevKey = ""
        prevUnit = ""

        avgValue = 0
        keyCount = 0
        for ms in item["measurements"]:
            if(prevKey != ms["Key"]):
                if(keyCount > 0):
                    avgs["report"]["findingSite"][index]["measurements"].append( {
                        "Key": prevKey + " Avg",
                        "Value": avgValue/keyCount,
                        "Unit": prevUnit,
                        "Infos": [{"Key": "Calculated", "Value": "Average"}]
                    })
                    keyCount = 0
                    avgValue = 0
                prevKey = ms["Key"]
                prevUnit =  ms["Unit"]
                
            if(prevKey == ms["Key"]):
                keyCount += 1;
                avgValue += float(ms["Value"])

           
            
            print("       " + ms["Key"])
        #this should cover last index
        if(keyCount > 0):
                    avgs["report"]["findingSite"][index]["measurements"].append( {
                        "Key": prevKey + " Avg",
                        "Value": avgValue/keyCount,
                        "Unit": prevUnit,
                        "Infos": [{"Key": "Calculated", "Value": "Average"}]
                    })
        index += 1;

    return avgs;

def extractReport(dataSet, obj):
    print("I'm extracting the report")

    # Remove this when integrated with main since the checking will happen somewhere else
    test = dataSet.get(pydicom.tag.Tag(0x0040, 0xa730))
    print(dataSet.get(pydicom.tag.Tag(0x0008, 0x0060)))
    print(type(test))
    if dataSet.get(pydicom.tag.Tag(0x0008, 0x0060)).value == "SR":
        print(dataSet.get(pydicom.tag.Tag(0x0008, 0x0060)))
        
        print(dataSet.get(pydicom.tag.Tag(0x0040, 0xa040)))
        print(dataSet.get(pydicom.tag.Tag(0x0040, 0xa043)).value)
        print(dataSet.get(pydicom.tag.Tag(0x0020, 0x0013)))
        print(dataSet.get(pydicom.tag.Tag(0x0040, 0xa491)))
        print(dataSet.get(pydicom.tag.Tag(0x0020, 0x0011)))
        print(dataSet.get(pydicom.tag.Tag(0x0040, 0xa010)))
        print(dataSet.get(pydicom.tag.Tag(0x0400, 0x0510)))
        print(dataSet.get(pydicom.tag.Tag(0x0042, 0x0011)))
        print(dataSet.get(pydicom.tag.Tag(0x0040, 0xDB73)))
        print(dataSet.get(pydicom.tag.Tag(0x0010, 0x0020)))


       

        conceptNameCodeDataSet = dataSet.get(pydicom.tag.Tag(0x0040, 0xa043)).value[0]

        #srData["name"] = EX.toStr(EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value))
       
        if(dataSet.get(pydicom.tag.Tag(0x0008, 0x1030)) is not None):
            print(EX.toStr(dataSet.get(pydicom.tag.Tag(0x0008, 0x1030)).value))
            srData["name"] = EX.toStr(dataSet.get(pydicom.tag.Tag(0x0008, 0x1030)).value)
        else:
            srData["name"] = "Adult Echo"


        print("Length of content sequence " + str(len(dataSet.get(pydicom.tag.Tag(0x0040, 0xa730)).value)))
        print("Type of content sequence " + str(type(dataSet.get(pydicom.tag.Tag(0x0040, 0xa730)).value[0])))
        counter = 0
        numberOfElements = []
        numberOfElements.append(0)
        processChild(dataSet.get(pydicom.tag.Tag(0x0040, 0xa730)).value, 0, "patient", numberOfElements, "")

        print("Number of elements " + str(numberOfElements[0]))
        
        patientDir = obj["folderForPatients"] + "/" + EX.toStr(dataSet.get(pydicom.tag.Tag(0x0010, 0x0020)).value)

        # for item  in srData["report"]["findingSite"]:
        #     mes = list(dict.fromkeys(item["measurements"]))

        iuid = EX.toStr(dataSet.get(pydicom.tag.Tag(0x0020, 0x000d)).value)

        testFolder =  patientDir + "/" + iuid

        if not os.path.exists(testFolder):
            os.makedirs(testFolder)

        # srDataAvgs = generateMeasurmentAvg(srData);
        with open(testFolder + "/report.json", 'w') as fp:
            json.dump(srData, fp)
            fp.close()
        
        reportFolder = obj["folderForImporter"] + "/" + EX.toStr(dataSet.get(pydicom.tag.Tag(0x0010, 0x0020)).value) + "/" + iuid
        if not os.path.exists(reportFolder):
            os.makedirs(reportFolder)
        
        # create the report file to trigger importer action to import a new test
        with open(reportFolder + "/report.json", 'w') as fp:
            json.dump(srData, fp)
            fp.close()
        
        #clearing data after one file is saved
        srData["report"]["patient"] = {}
        srData["report"]["findingSite"] = []
        srData["report"]["userDefined"] = []
        

        
        
        #print(dataSet.get(pydicom.tag.Tag(0x0040, 0xa504)).value)
    else:
        print("This is not an SR dicom file")

if __name__ == '__main__':

    import sys

    if len(sys.argv) < 2:
        sys.exit("Format: python3 input.dcm")
    else:
        try:
            dataSet = pydicom.dcmread(sys.argv[1])

        except pydicom.errors.InvalidDicomError:
            print("Dicom file '" + sys.argv[1] + "' is missing metadata information")

        except FileNotFoundError:
            print("File '" + sys.argv[1] + "' not found")

        else:
            extractReport(dataSet)
