#! /usr/bin/env python
# -*- coding utf utf-8 -*-

"""
    File parser that can find and display entries from the public dictionary and matching data element(s)
    using a pattern as search criteria.

    Linux
    Example: python3 showFields.py TeleMed\ samples/ECG001-24012019-140353.dcm

    Microsoft
    Example: python showFields.py "TeleMed samples\ECG001-24012019-140353.dcm"

"""

import sys
import pydicom

if len(sys.argv) < 2:
    sys.exit("Format: python3 input.dcm")
else:
    dataSet = pydicom.dcmread(sys.argv[1])
    entered = input("keyword to search (type 'end' to exit): ")

    while(entered != 'end'):
        fields = dataSet.dir(entered)
        print(len(fields))

        if len(fields) > 0:
            print(type(fields))

            for field in fields:
                print(field)
                tagGroup = dataSet.data_element(field).tag.group
                tagElement = dataSet.data_element(field).tag.element
                print(dataSet.data_element(field).value)
                print("Type of the value is " + str(type(dataSet.data_element(field).value)))

                if dataSet.data_element(field).tag.is_private: 
                    print("Tag is private")
                else:
                    print("Tag is not private")
                
                print("Tag is " + '(' + '0x{:04x}'.format(tagGroup) + ',' + '0x{:04x}'.format(tagElement) + ")\n\n")

        else:
            "No matches for the entered keyword"
        
        entered = input("keyword to search: ")

        

