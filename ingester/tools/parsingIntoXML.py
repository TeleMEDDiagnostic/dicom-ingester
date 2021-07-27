#! /usr/bin/env python
# -*- coding utf-8 -*-

"""
    Simple parser that finds all the dataElements in a DICOM file using a pattern as
    criteria, and then creates an XML file using the parsed data
    It uses the PyDicom and xml.etree.ElementTree modules.

    Example: python3 parsingIntoXML.py ECG001-24012019-140353.dcm name

"""

import sys
import pydicom
import xml.etree.ElementTree as ET

# Function to create a subelement in the XML tree adding the value of a keyword to it
def createSubelementWithAValue(kw, val, parent):
    print("Tag '" + kw + "'.\ntype '" + str(type(val)) + "'. Inserting its value '" + val + "', inside of the tag\n")

    return ET.SubElement(parent, kw, name = val)


if len(sys.argv) < 3:
    sys.exit("Format: python3 input.dcm keyword")
else:
    # Read the file
    data = pydicom.dcmread(sys.argv[1])
    pattrn = sys.argv[2]
    
    # Get a list of all the keywords that match the pattern
    elm = data.dir(pattrn)

    if elm:
        print("Number of matches: " + str(len(elm)))
        print ("Pattern to find: '%s'" % pattrn)
        print("Found keyword(s): ", ', '.join(elm))

        for val in elm:
             # Value for every dataElement that matches the keywords
            print("\nKeyword: %s, \nvalue: %s" % (val, data.data_element(val).value))
    else:
        sys.exit("Keyword " + pattrn + " not found in the dataset")

print("\n\nXML FILE")
print("------\n")

root = ET.Element("ECG")
patient = ET.SubElement(root, "Patient")


"""
 In some cases, the data obtained from the query is not type str and it needs conversion to str.
 So far, it only converts from pydicom.valurep.PersonName3, pydicom.valuerep.IS and pydicom.valuerep.DSfloat

"""

for pt in elm:
    theValue = data.data_element(pt).value

    if isinstance(theValue, str):
        subElm = createSubelementWithAValue(pt, theValue, patient)
        subElm.text = theValue

    elif isinstance(theValue, pydicom.valuerep.PersonName3):
        # this is necessary to extract the value from PersonName3
        # https://stackoverflow.com/questions/606191/convert-bytes-to-a-string
        # theName = theValue.encode().decode("cp437", 'backslashreplace') <-- consider this if there are problems with encoding
        theValue = theValue.encode().decode("utf-8")
        subElm = createSubelementWithAValue(pt, theValue, patient)
        subElm.text = theValue

    elif isinstance(theValue, pydicom.valuerep.IS):
        theValue = theValue.original_string
        subElm = createSubelementWithAValue(pt, theValue, patient)
        subElm.text = theValue

    elif isinstance(theValue, pydicom.valuerep.DSfloat):
        theValue = str(theValue.real)
        subElm = createSubelementWithAValue(pt, theValue, patient)
        subElm.text = theValue

    else: 
        print("Tag '" + pt + "'.\nType '" + str(type(theValue)) + "'. It needs conversion.\n")

tree = ET.ElementTree(root)
# ET.dump(root)
tree.write("sample.xml", xml_declaration = True, encoding = 'utf-8')


