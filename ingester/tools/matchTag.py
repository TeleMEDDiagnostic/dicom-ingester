#! /usr/bin/env python
# -*- coding utf -*-

import sys
import pydicom

"""
    Need to go inside of sequences
"""

if len(sys.argv) < 2:
    sys.exit("Format: python3 input.dcm")
else:
    dataSet = pydicom.dcmread(sys.argv[1])

    tagGroup = input("Group: ")
    tagElement = input("Element: ")

    
    
    while(tagGroup != "end"):
        theTag = pydicom.tag.Tag("0x" + tagGroup, "0x" + tagElement)
        print("Entered tag is " + '(' + '0x{:04x}'.format(theTag.group) + ',' + '0x{:04x}'.format(theTag.element) + ")")

        #print("dictionary name " + dataSet.get(theTag).name)
        for elm in dataSet.iterall():
        
            if elm.tag.group == theTag.group and elm.tag.element == theTag.element:
                field = elm.keyword

                tagGroup = elm.tag.group
                tagElement = elm.tag.element
                print(elm.value)
                print("Type of the value is " + str(type(elm.value)))
                if elm.tag.is_private: 
                    print("Tag is private")
                else:
                    print("Tag is not private")
                    
                print("Tag is " + '(' + '0x{:04x}'.format(tagGroup) + ',' + '0x{:04x}'.format(tagElement) + ")\n\n")

        tagGroup = input("Group: ")
        tagElement = input("Element: ")


