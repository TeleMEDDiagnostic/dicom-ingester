#! /usr/bin/env python
# -*- coding utf utf-8 -*-

import sys
import pydicom
import xml.etree.ElementTree as ET

import parsers.xmlTools as EX
srData = { "name" : "Adult Echocardiography Procedure Report",
        "report" : {
        "patient" : {},
        "findingSite" : []
        }
    }
def processChild(dataSet, level, parent, elements):
    counter = 0
    spaces = "     " * level

    for i in dataSet:
        #print(spaces + "Relationship type " + EX.toStr(i.get(pydicom.tag.Tag(0x0040, 0xa010)).value))
        #print(spaces + "Value Type " + EX.toStr(i.get(pydicom.tag.Tag(0x0040, 0xa040)).value))
        #print(i)

        #EX.toStr(dataSet.get(pydicom.tag.Tag(0x0010, 0x0020)).value)

        value = spaces;
        val = ""
        key= ""
        unit=""
        if i.get(pydicom.tag.Tag(0x0040, 0xa040)).value == "TEXT":
            conceptNameCodeDataSet = i.get(pydicom.tag.Tag(0x0040, 0xa043)).value[0]
            value += EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value) + ": " + i.get(pydicom.tag.Tag(0x0040, 0xa160)).value
            key = EX.toStr(conceptNameCodeDataSet.get(pydicom.tag.Tag(0x0008, 0x0104)).value)
            val = i.get(pydicom.tag.Tag(0x0040, 0xa160)).value
            unit = ""


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
            print(value)
            if key != "" and val != "":
                fillSRData(key, val, unit, parent, "")

        contentSequence = i.get(pydicom.tag.Tag(0x0040, 0xa730))
        #print("\n" + spaces + "Child " + str(counter) + ", level " + str(level))
        if contentSequence is not None:
            #print(spaces + "Entering level ------------" + str(level + 1))            
            processChild(contentSequence.value, level + 1, parent, elements)
            #print(spaces + "Exiting level ------------" + str(level + 1))            
        counter += 1
        elements[0] += 1
        

def fillSRData(key, value, unit, parent, currentChild):
    obj = {}
    if parent == "patient":
        obj[key] = value
        srData["report"]["patient"] |= obj

def extractReport(dataSet):
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

        print("Length of content sequence " + str(len(dataSet.get(pydicom.tag.Tag(0x0040, 0xa730)).value)))
        print("Type of content sequence " + str(type(dataSet.get(pydicom.tag.Tag(0x0040, 0xa730)).value[0])))
        counter = 0
        numberOfElements = []
        numberOfElements.append(0)
        processChild(dataSet.get(pydicom.tag.Tag(0x0040, 0xa730)).value, 0, "patient", numberOfElements)

        print("Number of elements " + str(numberOfElements[0]))
        
        
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
