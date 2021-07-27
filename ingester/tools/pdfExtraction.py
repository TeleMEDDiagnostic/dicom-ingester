#! /usr/bin/env pyhon
# -*- coding utf-8 -*-

"""
    Simple parser that finds a PDF document encapsulated in a dcm file

    Example: python3 pdfExtraction.py Telemed\ samples/pdfInDICOM.dcm

"""

import sys
import pydicom

if len(sys.argv) < 2:
    sys.exit("Format: python3 input.dcm")
else:
    # Read the file
    data = pydicom.dcmread(sys.argv[1])
    
    # Try to find the document
    elm = data.dir("EncapsulatedDocument")

    if elm and (data.data_element("MIMETypeOfEncapsulatedDocument").value == "application/pdf"):
        print("PDF document found and extracted")
        pdfFile = open("extracted.pdf", 'wb')
        pdfFile.write(data.data_element(elm[0]).value)
        pdfFile.close()
    else:
        print("This file doesn't have an encapsulated document")
