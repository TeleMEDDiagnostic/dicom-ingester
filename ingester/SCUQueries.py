#!/usr/bin/env python

from pynetdicom import AE, evt, UID, build_role
import pydicom
import pynetdicom
from pydicom.uid import ImplicitVRLittleEndian, ExplicitVRLittleEndian
import imageParser as ip
import time
import threading

def handleStore(thread_list):

    def handle_event(event):
        print("I'm in handleStore")
        # I have to do this because if I try to pass event.dataset to imageToPng it doesn't work, don't ask me why
        ds = event.dataset

        # Add the File Meta Information
        ds.file_meta = event.file_meta
        t = threading.Thread(target=ip.imageToPng, args=(ds,))
        t.start()
        thread_list.append(t)

        return 0x0000
    return handle_event

def cFind(pID):
    if len(pID) == 0:
        return "No argument was passed"
    else:
        ae = AE(ae_title=b'OSTEP')

        # Patient Root Query/Retrieve Information Model – FIND
        ae.add_requested_context('1.2.840.10008.5.1.4.1.2.1.1', [ImplicitVRLittleEndian, ExplicitVRLittleEndian])

        # Study Root Query/Retrieve Information Model – FIND
        ae.add_requested_context(UID('1.2.840.10008.5.1.4.1.2.2.1'), [ImplicitVRLittleEndian, ExplicitVRLittleEndian, '1.2.840.10008.1.2.4.50'])

        # UltrasoundImageStorage
        ae.add_requested_context(UID('1.2.840.10008.5.1.4.1.2.1.2'), ['1.2.840.10008.1.2.4.51'])

        # UltrasoundMultiframeImageStorage
        ae.add_requested_context(UID('1.2.840.10008.5.1.4.1.2.2.2'), ['1.2.840.10008.1.2.4.51'])

        
        patientRole = build_role(UID('1.2.840.10008.5.1.4.1.2.1.1'), scu_role=True)
        studyRole = build_role(UID('1.2.840.10008.5.1.4.1.2.2.1'), scu_role=True)
        imageRole = build_role(UID('1.2.840.10008.5.1.4.1.1.6.1'), scu_role=True)
        multiframeRole = build_role(UID('1.2.840.10008.5.1.4.1.1.3.1'), scu_role=True)

        #assoc = ae.associate('www.dicomserver.co.uk', 11112, ext_neg=[patientRole, studyRole, imageRole, multiframeRole])
        assoc = ae.associate('localhost', 4242, ext_neg=[patientRole, studyRole, imageRole, multiframeRole], ae_title=b'Orthanc')
        thread_list = []

        if assoc.is_established:
            print("Association established")

            ae.add_supported_context(UID('1.2.840.10008.5.1.4.1.1.3.1'), ['1.2.840.10008.1.2.4.50'])
            ae.add_supported_context(UID('1.2.840.10008.5.1.4.1.1.6.1'), ['1.2.840.10008.1.2.4.50'])
            scp = ae.start_server(('', 2000), block=False, evt_handlers=[(evt.EVT_C_STORE, handleStore(thread_list))])

            dataSetWithAttributes = pydicom.dataset.Dataset()
            dataSetWithAttributes.add_new([0x0010, 0x0020], "PN", pID)
            dataSetWithAttributes.add_new([0x0010, 0x0010], "LO", "")
            dataSetWithAttributes.add_new([0x0008, 0x0016], "UI", "")
            dataSetWithAttributes.add_new([0x0008, 0x0060], "CS", "")
            dataSetWithAttributes.add_new([0x0008, 0x0062], "CS", "")
            dataSetWithAttributes.add_new([0x0020, 0x1206], "US", "")
            dataSetWithAttributes.add_new([0x0020, 0x1208], "US", "")
            dataSetWithAttributes.add_new([0x0020, 0x1209], "US", "")
            dataSetWithAttributes.add_new([0x0008, 0x1150], "UI", "")
            dataSetWithAttributes.add_new([0x0020, 0x000e], "UI", "")
            dataSetWithAttributes.add_new([0x0020, 0x000d], "UI", "")
            dataSetWithAttributes.add_new([0x0008, 0x0052], "LO", "STUDY")

            responseGenerator = assoc.send_c_find(dataSetWithAttributes, query_model='P')
            returnedDatasets = []
            print("Results for Study")
            for (status, identifier) in responseGenerator:
                if status:
                    print('C-FIND query status: 0x{0:04x}'.format(status.Status))

                    # If the status is 'Pending' then `identifier` is the C-FIND response
                    if status.Status in (0xFF00, 0xFF01):
                        print(type(identifier))
                        print(identifier)
                        returnedDatasets.append(identifier)
                else:
                    print('Connection timed out, was aborted or received invalid response')

            #dataSetSeries = pydicom.dcmread("/home/josue/Projects/telemed/1209380365")
            dataSetSeries = pydicom.dataset.Dataset()
            dataSetSeries.add_new([0x0000, 0x0900], "US", "")
            dataSetSeries.add_new([0x0010, 0x0020], "PN", "")
            dataSetSeries.add_new([0x0010, 0x0010], "LO", "")
            dataSetSeries.add_new([0x0008, 0x0016], "UI", returnedDatasets[0].get(pydicom.tag.Tag(0x0008, 0x0016)).value)
            dataSetSeries.add_new([0x0008, 0x0060], "CS", "")
            dataSetSeries.add_new([0x0020, 0x1206], "US", "")
            dataSetSeries.add_new([0x0020, 0x1208], "US", "")
            dataSetSeries.add_new([0x0020, 0x1209], "US", "")
            dataSetSeries.add_new([0x0008, 0x1150], "UI", "")
            dataSetSeries.add_new([0x0008, 0x0018], "UI", "")
            dataSetSeries.add_new([0x0020, 0x000d], "UI", "")
            dataSetSeries.add_new([0x0020, 0x000e], "UI", returnedDatasets[0].get(pydicom.tag.Tag(0x0020, 0x000e)).value)
            
            dataSetSeries.QueryRetrieveLevel = "SERIES"
            
            responseGenerator = assoc.send_c_move(dataSetSeries, b'OSTEP', query_model='S')
            print("\nResults for Series")
            for (status, identifier) in responseGenerator:
                if status:
                    print('C-MOVE query status: 0x{0:04x}'.format(status.Status))
                    print(identifier)

                    # If the status is 'Pending' then `identifier` is the C-FIND response
                    if status.Status in (0xFF00, 0xFF01):
                        print(identifier)
                else:
                    print('Connection timed out, was aborted or received invalid response')

            assoc.release()
            scp.shutdown()
            for t in thread_list:
                t.join()
        else:
            print("couldn't associate")
        

if __name__ == '__main__':
    
    import sys

    if len(sys.argv) < 2:
        sys.exit("Format: python3 patientID")
    else:
        cFind(sys.argv[1])
