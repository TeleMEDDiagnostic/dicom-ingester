#! /usr/bin/env python
# -*- coding utf utf-8 -*-

import pydicom
import xml.etree.ElementTree as ET
import struct

import parsers.xmlTools as EX

def extractSamples(waveform, size, interpretation):
    if interpretation == "SB":
        # signed 8 bit linear
        result = struct.unpack('b' * int(size), waveform)

    elif interpretation == "UB":
        # unsigned 8 bit linear
        result = struct.unpack('B' * int(size), waveform)

    elif interpretation == "MB":
        # 8 bit mu-law (in accordance with ITU-T Recommendation G.711)
        print("MB interpretation not implemented yet")

    elif interpretation == "AB":
        # 8 bit A-law (in accordance with ITU-T Recommendation G.711)
        print("AB interpretation not implemented yet")

    elif interpretation == "SS":
        # signed 16 bit linear
        sizeForReading = size / 2
        result = struct.unpack('h' * int(sizeForReading), waveform)

    elif interpretation == "US":
        # unsigned 16 bit linear
        sizeForReading = size / 2
        result = struct.unpack('H' * int(sizeForReading), waveform)

    elif interpretation == "SL":
        # signed 32 bit linear
        sizeForReading = size / 4
        result = struct.unpack('l' * int(sizeForReading), waveform)

    elif interpretation == "UL":
        # unsigned 32 bit linear
        sizeForReading = size / 4
        result = struct.unpack('L' * int(sizeForReading), waveform)

    elif interpretation == "SV":
        # signed 64 bit linear
        sizeForReading = size / 8
        result = struct.unpack('q' * int(sizeForReading), waveform)

    elif interpretation == "UV":
        # unsigned 64 bit linear
        sizeForReading = size / 8
        result = struct.unpack('Q' * int(sizeForReading), waveform)

    return result


def waveformParser(waveformSequence, waveformAnnotationDE, root):

    print("\n*** Waveform Information Section ***")
    waveFieldTuple = ('SampleRate',          # samplingFrequency
                    'Resolution',         # waveformBitStored
                    'LeadSampleCount')    # NumberOfWaveformSamples

    waveTagTuple = (pydicom.tag.Tag(0x003a,0x001a),     # samplingFrequency
                    pydicom.tag.Tag(0x5400,0x1004),     # waveformBitAllocated
                    pydicom.tag.Tag(0x003a, 0x0010))    # NumberOfWaveformSamples
    # MedianSampleCount is missing

    EX.insertTupleInXML(waveFieldTuple, waveTagTuple, waveformSequence, root)

    del waveFieldTuple
    del waveTagTuple

    """
        Filter info section
    """
    print("\n*** Filter Information Section ***")
    filterFieldTuple = ('ACFilter',             # NotchFilterFrequency
                        'HighPassFilter',       # FilterHighFrequency
                        'LowPassFilter')        # FilterLowFrequenecy

    filterTagTuple = (pydicom.tag.Tag(0x003a,0x0222),     # NotchFilterFrequency
                    pydicom.tag.Tag(0x003a,0x0221),     # FilterHighFrequency
                    pydicom.tag.Tag(0x003a,0x0220))     # FilterLowFrequency

    #TODO(Josue): We only need one value for the filters. No need to show every filter value per channel
    # This is not the most optimized way, it'll have to be changed eventually
    NFfound = False
    HFfound = False
    LFfound = False
    for elm in waveformSequence.iterall():
        if elm.tag.group == filterTagTuple[0].group and elm.tag.element == filterTagTuple[0].element and not NFfound:
            NFfound = True
            if isinstance(elm.value, str):
                EX.createSubelementWithAValue(filterFieldTuple[0], elm.value, root)
            else:
                EX.createSubelementWithAValue(filterFieldTuple[0], EX.toStr(elm.value), root)

        elif elm.tag.group == filterTagTuple[1].group and elm.tag.element == filterTagTuple[1].element and not LFfound:
            HFfound = True
            if isinstance(elm.value, str):
                EX.createSubelementWithAValue(filterFieldTuple[1], elm.value, root)
            else:
                EX.createSubelementWithAValue(filterFieldTuple[1], EX.toStr(elm.value), root)

        elif elm.tag.group == filterTagTuple[2].group and elm.tag.element == filterTagTuple[2].element and not LFfound:
            LFfound = True
            if isinstance(elm.value, str):
                EX.createSubelementWithAValue(filterFieldTuple[2], elm.value, root)
            else:
                EX.createSubelementWithAValue(filterFieldTuple[2], EX.toStr(elm.value), root)

        if LFfound and HFfound and NFfound:
            break

    del filterFieldTuple
    del filterTagTuple

    """
        Waveform Data section
    """
    waveformFieldTuple = (pydicom.tag.Tag(0x003a, 0x0200),      # ChannelDefinitionSequence
                            pydicom.tag.Tag(0x003a, 0x0208),    # ChannelSourceSequence
                            pydicom.tag.Tag(0x0008, 0x0104),    # CodeMeaning
                            pydicom.tag.Tag(0x5400, 0x1006),    # Waveform Sample Interpretation
                            pydicom.tag.Tag(0x003a, 0x0010),    # Number of Waveform Samples
                            pydicom.tag.Tag(0x003a, 0x0005),    # Number of Waveform Channels
                            pydicom.tag.Tag(0x5400, 0x1010))    # Waveform Data

    ChannelDefinitionSequence = 0
    for elm in waveformSequence.iterall():
        if elm.tag.group == waveformFieldTuple[0].group and elm.tag.element == waveformFieldTuple[0].element:
            ChannelDefinitionSequence = elm.value
            break
        
    print("\n*** Waveform Data Section ***")

    waveformSampleInterpretation = waveformSequence.get(waveformFieldTuple[3])
    print("WaveformSampleInterpretation '" + waveformSampleInterpretation.value + "'")

    numberOfSamples = waveformSequence.get(waveformFieldTuple[4])
    print("Number of Samples: " + str(numberOfSamples.value))

    numberOfChannels = waveformSequence.get(waveformFieldTuple[5])
    print("Length of the sequence: " + str(numberOfChannels.value))

    waveformData = waveformSequence.get(waveformFieldTuple[6])

    # Parsing waveform data
    extractedSamples = extractSamples(waveformData.value, len(waveformData.value), waveformSampleInterpretation.value)
    print("The length of parsedWaveform is " + str(len(extractedSamples)))
    print("The type of parsedWaveform is " + str(type(extractedSamples)))


    channels = []
    for i in range(numberOfChannels.value):
        # TODO(Josue) Find a way to do this without making a copy
        temp = extractedSamples[numberOfSamples.value * i : numberOfSamples.value * (i + 1)]
        channels.append(','.join([str(item) for item in temp]))
        
    leadData = EX.createSubelementWithAttribute("LeadData", 'LeadCount', EX.toStr(numberOfChannels.value), "", root)

    leads = []
    for channelDefinitionDS in ChannelDefinitionSequence:
        # This returns a dataElement, and its value is a Sequence of dataSets
        #channelSourceDE = channelDefinitionDS.get(waveformFieldTuple[1])
        #ChannelSourceSequence = channelSourceDE.value
        ChannelSourceSequence = channelDefinitionDS.get(waveformFieldTuple[1]).value

        selectedChannel = 0
        for channelSourceDS in ChannelSourceSequence:
            # Need to decide if I want codeValue or codeMeaning, right now I'm using codeMeaning
            codeMeaning = channelSourceDS.get(waveformFieldTuple[2])
            subElement = EX.createSubelementWithAttribute("LeadData", 'lead', EX.toStr(codeMeaning.value).replace("Lead ", ""), "", leadData)
            subElement.text = channels[selectedChannel]
            selectedChannel += 1
            print(EX.toStr(codeMeaning.value))

            leads.append(EX.toStr(codeMeaning.value).replace("Lead ", ""))

    del waveformFieldTuple

    """
        ECG Measurements, Measurement Table sections
    """
    print("\n*** ECG Measurements, Measurement Table Sections ***")
        
    ECGMeasSequences = (pydicom.tag.Tag(0x0040, 0x08ea),    # Measurement Units Code Sequence
                        pydicom.tag.Tag(0x0040, 0xa043))    # Concept NameCode Sequence

    ECGMeasFields = (pydicom.tag.Tag(0x0008, 0x0100),       # Code Value
                        pydicom.tag.Tag(0x0008, 0x0104),    # Code Meaning
                        pydicom.tag.Tag(0x0040, 0xa30a))    # Numeric Value

    waveformAnnotationSequence = waveformAnnotationDE.value

    # ECG measurements
    ECGMeasurementsNameCodes = ("Ventricular Heart Rate", "P Duration", "PQ", "PR Interval", "RR Interval", "QRS Duration",
                                "QT Interval", "QTc Interval", "QT duration", "QTc Interval using Bazett", "QTc Interval using Framingham",
                                "QTc Interval using Fridericia", "QTc Interval using Hodges", "P Axis", "QRS Axis", "T Axis",
                                "P_ON", "P_OFF" , "QRS_ON" , "QRS_OFF" , "T_OFF")

    ECGMeasurementsFields = ("HR", "P", "PQ", "PRInterval", "RR", "QRS", 
                            "QT", "QTc", "QTd", "QTcBazett", "QTcFramingham", "QTcFridericia", "QTcHodges", "Paxis",
                            "QRSAxis", "Taxis", "P_ON", "P_OFF", "QRS_ON", "QRS_OFF", "T_OFF")

    ECGMeasurementsLists = tuple([] for i in range(len(ECGMeasurementsFields)))
    ECGMeasurementsUnits = [""] * len(ECGMeasurementsFields)

    # MeasurementTable
    MeasurementsTableNameCodes = ("P wave amplitude", "Q wave duration", "Q wave amplitude",
                                    "R1 wave amplitude", "R2 wave amplitude", "R1 wave duration", "R2 wave duration",
                                    "J point amplitude", "J point + 20 ms amplitude", "J point + 40 ms amplitude", "J point + 60 ms amplitude", "J point + 80 ms amplitude",
                                    "S1 wave amplitude", "S2 wave amplitude", "S1 wave duration", "S2 wave duration",
                                    "Minimum P wave amplitude", "Maximum P wave amplitude", "Minimum T wave amplitude", "Maximum T wave amplitude")

    MeasurementsTableFields = ("PAmplitude ", "QDuration", "QAmplitude", "R1Amplitude", "R2Amplitude", "R1Duration", "R2Duration", 
                                "Jpoint", "Jpoint20", "Jpoint40", "Jpoint60", "Jpoint80", "S1Amplitude", "S2Amplitude",
                                "S1Duration", "S2Duration", "MinimumPAmplitude", "MaximumPAmplitude", "MinimumTAmplitude", "MaximumTAmplitude")

    MeasurementsTableLists = tuple([] for i in range(len(MeasurementsTableFields)))
    MeasurementsTableUnits = [""] * len(MeasurementsTableFields)

    # I need to change this to a more optimized way to do it
    for ds in waveformAnnotationSequence:
        measurementUnitCodeDE = ds.get(ECGMeasSequences[0])
        conceptNameCodeDE = ds.get(ECGMeasSequences[1])
        numericValue = ds.get(ECGMeasFields[2])

        # I'm assuming when both measurement and concept are not none, the value is valid
        if measurementUnitCodeDE is not None and conceptNameCodeDE is not None:
            measurementUnitCodeSequence = measurementUnitCodeDE.value
            conceptNameCodeSequence = conceptNameCodeDE.value

            measurementCodeValue = measurementUnitCodeSequence[0].get(ECGMeasFields[0])
            print("\nMeasurement Unit Code: " + EX.toStr(measurementCodeValue.value))

            conceptCodeValue = conceptNameCodeSequence[0].get(ECGMeasFields[1])
            print("Concept Name Code: " + EX.toStr(conceptCodeValue.value))
            print("Numeric Value: " + EX.toStr(numericValue.value))

            """
                complatible with insertTupleinXML()?
            """
            if EX.toStr(conceptCodeValue.value) in ECGMeasurementsNameCodes:
                index = ECGMeasurementsNameCodes.index(EX.toStr(conceptCodeValue.value))
                print ("Index is: ", str(index))
                ECGMeasurementsLists[index].append(EX.toStr(numericValue.value))
                ECGMeasurementsUnits[index] = EX.toStr(measurementCodeValue.value)

            elif EX.toStr(conceptCodeValue.value) in MeasurementsTableNameCodes:
                index = MeasurementsTableNameCodes.index(EX.toStr(conceptCodeValue.value))
                MeasurementsTableLists[index].append(EX.toStr(numericValue.value))
                MeasurementsTableUnits[index] = EX.toStr(measurementCodeValue.value)

    ECGMeasurements = EX.createSubelementWithAValue("ECGMeasurement", "", root)
    MeasurementTable = EX.createSubelementWithAValue("MeasurementTable", "", root)

    print("\nECGMeasurements")
    # here there should be the for loop to insert everything
    for i in range(len(ECGMeasurementsFields)):
        subElement = EX.createSubelementWithAttribute(ECGMeasurementsFields[i],
                                                        "Unit",
                                                        ECGMeasurementsUnits[i],
                                                        ','.join(iten for iten in ECGMeasurementsLists[i]),
                                                        ECGMeasurements)
        print("CodeName: " + ECGMeasurementsNameCodes[i])
        print("Field: " + ECGMeasurementsFields[i])
        print("Numeric Value: " + ','.join(iten for iten in ECGMeasurementsLists[i]))
    
    print("\nMeasurementTable")
    subElement = EX.createSubelementWithAValue("LeadOrder", ','.join(i for i in leads), MeasurementTable)
    for i in range(len(MeasurementsTableFields)):
        subElement = EX.createSubelementWithAttribute(MeasurementsTableFields[i],
                                                    "Unit",
                                                    MeasurementsTableUnits[i],
                                                    ','.join(item for item in MeasurementsTableLists[i]),
                                                    MeasurementTable)
        print("CodeName: " + MeasurementsTableNameCodes[i])
        print("Field: " + MeasurementsTableFields[i])
        print("Numeric Value: " + ','.join(iten for iten in MeasurementsTableLists[i]))
 
    del ECGMeasSequences
    del ECGMeasFields        

# TODO(Josue) This doesn't work right now
# need to change the main
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
            waveformParser(dataSet)