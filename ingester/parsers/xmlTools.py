#! /usr/bin/env python
# -*- coding utf utf-8 -*-

import xml.etree.ElementTree as ET
import pydicom

def toStr(val):
    # Right now DA, DT, TM, DSdecimal and PersonName are missing, most of them return str so conversion is "probably" not needed.
    result = val
    if isinstance(val, pydicom.valuerep.PersonName3) or isinstance(val, pydicom.valuerep.PersonNameUnicode):
        # https://stackoverflow.com/questions/606191/convert-bytes-to-a-string
        # theName = theValue.encode().decode("cp437", 'backslashreplace') <-- consider this if there are problems with encoding

        result = val.encode('utf-8').decode("utf-8")

    elif isinstance(val, pydicom.valuerep.IS):
        result = val.original_string

    elif isinstance(val, pydicom.valuerep.DSfloat):
        result = str(val.real)
    elif isinstance(val, int):
        result = str(val)
    elif isinstance(val, pydicom.multival.MultiValue):
        result = val.__str__()

    return result


def createSubelementWithAValue(kw, val, parent):
    temp = ET.SubElement(parent, kw)
    temp.text = val
    return temp


def createSubelementWithAttribute(kw, attr, attrVal, val, parent):
    temp = ET.SubElement(parent, kw)
    temp.set(attr, attrVal)
    temp.text = val
    return temp


def insertTupleInXML(fieldTuple, tagTuple, dataSet, XMLnode):
    for index in range(len(fieldTuple)):
        de = dataSet.get(tagTuple[index])
        if de is not None:
            """print("Keyword : " + str(de.keyword))
            print("Type: " + str(type(de.value)))
            print("Value :" + toStr(de.value))
            print("Group tag: " + str(de.tag.group))
            print("Element tag: " + str(de.tag.element))"""
            createSubelementWithAValue(fieldTuple[index], toStr(de.value), XMLnode)
        else:
            createSubelementWithAValue(fieldTuple[index], "", XMLnode)


