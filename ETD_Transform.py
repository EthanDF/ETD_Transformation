from pymarc import *
import csv
import urllib
from urllib import request
from urllib import error
import codecs
import unicodedata
import time

def stopper(r):
    stopper = input('stop? press "n"')
    if stopper == 'n':
        return r
        # print(1 / 0)

def writeNewMARC(record, file):
    with open(file, 'ab') as x:
        try:
            x.write((record.as_marc()))
        except UnicodeEncodeError:
            print ("couldn't write")
    # print("Written!")


def readBib2Purl():
    '''read in list relating bibs to OCNs with pURLs and Abstracts
    list should contain Old Bib, OCL, PURL, Abstract'''

    bib2Purl = 'CurrentBatchDocs\\Bib2Purls.csv'

    checkList = []
    with open(bib2Purl, 'r', encoding='utf-8') as c:
        reader = csv.reader(c)
        for row in reader:
            checkList.append(row)

    # return checkList

    # create a dictionary where the key is old OCLC Number and returns a tuple with PURL, Abstract, and Old Bib
    bibPurlDict = {}

    for ocn in checkList:
        bibPurlDict[ocn[1]] = (ocn[2], ocn[3], ocn[0])

    return bibPurlDict

def read710():
    '''read in list relating old bibs to 710 values so that the 710 can be written to the new record'''

    bib2710 = 'CurrentBatchDocs\\Bib2710.csv'

    bibList = []
    with open(bib2710, 'r', encoding='utf-8') as c:
        reader = csv.reader(c)
        for row in reader:
            bibList.append(row)

    # return bibList

    bibDict = {}
    for bib in bibList:
        bibDict[bib[0]] = bib[1]

    return bibDict

def extract710Subfields(sevenTen):


    sevenTenList = sevenTen.split('$')
    sevenTenList = sevenTenList[1:]

    temp710 = Field(tag='710', indicators=['2', ' '])

    for s in sevenTenList:
        subField = s[:1]
        fieldVal = s[1:]
        temp710.add_subfield(subField, fieldVal)

    return temp710

def trailingPunct(Marcfield):
    '''this looks for an unwanted training punctuation in MARC 300 and returns the corrected Field'''

    subfieldList = Marcfield.subfields
    lastSFVal = subfieldList[-1]
    lastSF = subfieldList[-2]

    if lastSFVal[len(lastSFVal)-1:len(lastSFVal)] == ';':
        lastSFVal = lastSFVal[:len(lastSFVal)-1]
    elif lastSFVal[len(lastSFVal)-1:len(lastSFVal)] == ')':
        if lastSFVal[len(lastSFVal) - 2:len(lastSFVal)-1] == ';':
            lastSFVal = lastSFVal[:len(lastSFVal) - 2].rstrip()+')'
    else:
        pass

    lastSFVal = lastSFVal.rstrip()

    Marcfield[lastSF] = lastSFVal

    return Marcfield

# def addEndPunct(marcField):
#
#     subfieldList = marcField.subfields



def readETDs():

    debugMode = input("run in debug mode? If yes, enter '1'\n")
    debugMode = str(debugMode)

    batchNum = input("what is the batch number?\n")
    batchNum = str(batchNum)

    # identify the old batch of marc files
    marcFile = str('CurrentBatchDocs\\batch'+batchNum+'_ocl.mrc')
    outputFile = 'CurrentBatchDocs\\newMARC'+batchNum+'.dat'
    sevenTenReport = 'CurrentBatchDocs\\MARC_710_f_Report.txt'

    bib2PurlDict = readBib2Purl()
    sevenTenDict = read710()


    print("running...\n")

    # start reading in the old marc files
    with open(marcFile, 'rb') as fh:
        reader = MARCReader(fh, to_unicode=True, force_utf8=True)

        for rec in reader:

            OCN = str(rec['035']['a'])

            if debugMode == '1':
                print(OCN)
            # change the LDR pos 18 to 'i'

            if debugMode == '1':
                print(str(rec.leader))
            ldrStr = str(rec.leader)
            rec.leader = ldrStr[:18]+'i'+ldrStr[19:]
            if debugMode == '1':
                print(str(rec.leader))

            # change the 008 pos 23 to 'o'

            if debugMode == '1':
                print(str(rec['008'].value()))
            fixField = rec['008'].data
            rec['008'].data = fixField[:23]+'o'+fixField[24:]

            if debugMode == '1':
                print(str(rec['008'].value()))

            # delete the 040 and create a new one with subfield a and c = "FGM"
            # the subfield b = "eng" and subfield e = "rda" to MARC 040

            if debugMode == '1':
                print(str(rec['040']))
            try:
                rec.remove_field(rec.get_fields('040')[0])
            except IndexError:
                pass
            new040 = Field(tag='040', indicators=[' ', ' '], subfields=['a', 'FGM', 'b', 'eng', 'c', 'FGM', 'e', 'rda'])
            rec.add_field(new040)

            # old way was just adding subfields, but that won't work!
            # rec['040'].add_subfield('b', 'eng')
            # rec['040'].add_subfield('e', 'rda')

            if debugMode == '1':
                print(str(rec['040']))

            # Delete all call numbers in the MARC 050 or 090

            # just for debugging - show any 050 values before deleting
            if debugMode == '1':
                display050Before =[]
                callNumberBefore = rec.get_fields('050')
                for ab in callNumberBefore:
                    display050Before.append(ab.value())
                print('050 before: '+str(display050Before))

            try:
                while len(rec.get_fields('050')) > 0:
                    rec.remove_field(rec.get_fields('050')[0])
            except IndexError:
                pass

            if debugMode == '1':
                display050After =[]
                callNumberAfter = rec.get_fields('050')
                for ab in callNumberAfter:
                    display050After.append(ab.value())
                print('050 after : '+str(display050After))

            # just for debugging - show any 090 values before deleting
            if debugMode == '1':
                display090Before = []
                callNumberLocalBefore = rec.get_fields('090')
                for ab in callNumberLocalBefore:
                    display050Before.append(ab.value())
                print('090 before: ' + str(display090Before))

            try:
                while len(rec.get_fields('090')) > 0:
                    rec.remove_field(rec.get_fields('090')[0])
            except IndexError:
                pass

            if debugMode == '1':
                display090After = []
                callNumberLocalAfter = rec.get_fields('090')
                for ab in callNumberLocalAfter:
                    display090After.append(ab.value())
                print('090 after : ' + str(display090After))



            # update the MARC 100 field to add comma after the author and add $eauthor

            if debugMode == '1':
                print(str(rec['100']))

            # check that comma ends the subfield a
            authorName = str(rec['100']['a'])
            if authorName.rstrip()[-1:] != ',':
                rec['100']['a'] = str(rec['100']['a'] + ',')

            # check for a period proceeding the comma
            authorName = str(rec['100']['a'])
            if authorName.rstrip()[-2:-1] != '.':
                rec['100']['a'] = str(rec['100']['a'])[:-1] + '.,'
            rec['100'].add_subfield('e', 'author.')
            if debugMode == '1':
                print(str(rec['100']))

            # capture copyright create the MARC 264#1 field, the MARC 264#4 field and then remove the MARC 260

            # if debugMode == '1':
            #     print(str(rec['260']))
            # print MARC 264
            # if debugMode == '1':
            #     f = rec.get_fields('264')
            #     for fs in f:
            #         print(str(fs))


            # reset copyright date and publication date
            copy = None
            pubdate = None

            # MARC 260 subfield c is a copyright if and only if it contains "copyright" or ©
            copyString = str(rec['260']['c'])
            if copyString.find('©') >= 0:
                copy = copyString[copyString.find('©') + 1:copyString.find('©') + 5]
            elif copyString.find('copyright') >= 0:
                copy = copyString[copyString.find('copyright') + 2:copyString.find('copyright') + 6]
            else:
                copy = None

            # otherwise it is a publication date - this assumes the publication date comes first
            if copyString[0] != '©':
                pubdate = copyString[0:4]

            # add MARC 264#1
            crField = Field(tag='264', indicators=[' ', '1'], subfields=['a', 'Boca Raton, Florida :'])
            # add subfield c if available
            if pubdate is not None:
                crField.add_subfield('b', 'Florida Atlantic University,')
                crField.add_subfield('c', str(pubdate)+'.')
            else:
                crField.add_subfield('b', 'Florida Atlantic University.')
            rec.add_field(crField)

            # add MARC 264#4 only if copyright date is present -
            # also update the fixed fields if both pub date and copyright date are available
            # set DtST (7) to 't' and add in copyright date to both date fields

            if copy is not None:
                crField2 = Field(tag='264', indicators=[' ', '4'], subfields=['c', '©'+str(copy)])
                rec.add_field(crField2)

                if debugMode == '1':
                    print(str(rec['008'].value()))
                fixField = rec['008'].data

            # only update the 008 DtSt fixed field if both pub date and copyright date are available
            if copy is not None and pubdate is not None:
                rec['008'].data = fixField[:6]+'t'+str(pubdate).replace('.', '')+str(copy).replace('.', '')+fixField[15:]
                if debugMode == '1':
                    print(str(rec['008'].value()))


            # remove MARC 260
            rec.remove_field(rec.get_fields('260')[0])

            if debugMode == '1':
                print(str(rec['260']))
            # print MARC 264s
            if debugMode == '1':
                f = rec.get_fields('264')
                for fs in f:
                    print(str(fs))

            # update MARC 300$a to "1 online resource" and remove subfield

            if debugMode == '1':
                print(str(rec['300']))

            # delete subfield c & g first
            rec300 = rec['300']
            rec300.delete_subfield('c')
            rec300.delete_subfield('g')

            marc300 = str(rec['300']['a'])
            if ':' in marc300:
                marc300 = marc300.replace(':', '').rstrip()
                rec['300']['a'] = '1 online resource (' + marc300 + ') :'
            else:
                rec['300']['a'] = '1 online resource (' + marc300 + ')'

            # clean up subfields following updates for punctuation using function
            temp300 = trailingPunct(rec['300'])
            rec.remove_field(rec.get_fields('300')[0])
            rec.add_field(temp300)

            if debugMode == '1':
                print(str(rec['300']))

            # remove MARC 336, 337, 338 and then add them back

            if debugMode == '1':
                print(str(rec['336']))
                print(str(rec['337']))
                print(str(rec['338']))

            try:
                rec.remove_field(rec.get_fields('336')[0])
                rec.remove_field(rec.get_fields('337')[0])
                rec.remove_field(rec.get_fields('338')[0])
            except IndexError:
                pass

            rdaContent = Field(tag='336', indicators=[' ', ' '], subfields=['a', 'text', 'b', 'txt', '2', 'rdacontent'])
            rdaMedia = Field(tag='337', indicators=[' ', ' '], subfields=['a', 'computer', 'b', 'c', '2', 'rdamedia'])
            rdaCarrier = Field(tag='338', indicators=[' ', ' '], subfields=['a', 'online resource', 'b', 'cr', '2', 'rdacarrier'])

            rec.add_field(rdaContent)
            rec.add_field(rdaMedia)
            rec.add_field(rdaCarrier)

            if debugMode == '1':
                print(str(rec['336']))
                print(str(rec['337']))
                print(str(rec['338']))

            # add MARC 655 /4, $a = "Electronic Thesis or Dissertation"

            if debugMode == '1':
                print('655 before: '+str(rec['655']))
            try:
                rec.remove_field(rec.get_fields('655')[0])
            except IndexError:
                pass

            etd = Field(tag='655', indicators=[' ', '4'], subfields=['a', 'Electronic Thesis or Dissertation'])
            rec.add_field(etd)

            if debugMode == '1':
                print('655 after: '+str(rec['655']))

            # check MARC 500 for "Photocopy, Typescript, or UMI"

            p = 'photocopy'
            t = 'typescript'
            u = 'umi'
            f = rec.get_fields('500')

            displayf = []

            counter = 0
            for note in f:
                displayf.append(note.value())
                if p in note.value().lower() or t in note.value().lower() or u in note.value().lower():
                    if debugMode == '1':
                        print('found ')
                    rec.remove_field(rec.get_fields('500')[counter])
                counter += 1
            if debugMode == '1':
                print('500 before: '+str(displayf))

            # display the 500 fields after removal of photocopy - can be commented out
            if debugMode == '1':
                fafter = rec.get_fields('500')
                displayfafter = []
                for n in fafter:
                    displayfafter.append(n.value())
                print('500 after: '+str(displayfafter))

            # check MARC 502 for missing trailing punctuation

            f502before = rec.get_fields('502')
            displayf502 = []

            for note in f502before:
                displayf502.append(note.value())

            if debugMode == '1':
                print('502 before: '+str(displayf502))

            for note in f502before:
                sfList = note.subfields
                lastSF = sfList[-2]
                lastSFVal = sfList[-1]

                if lastSFVal[len(lastSFVal)-1:len(lastSFVal)] != '.':
                    note[lastSF] = lastSFVal.rstrip()+'.'

                f502after = rec.get_fields('502')
                displayf502after = []
                for noteafter in f502after:
                    displayf502after.append(noteafter.value())
                if debugMode == '1':
                    print('502 after: ' + str(displayf502after))


            # check MARC 533 for "Photocopy" - UPDATE: ALWAYS DELETE MARC 533

            # p = 'photocopy'
            # displayf2 = []
            # f2 = rec.get_fields('533')
            #
            # counter = 0
            # for note2 in f2:
            #     displayf2.append(note2.value())
            #     if p in note2.value().lower():
            #         if debugMode == '1':
            #             print('found ')
            #         rec.remove_field(rec.get_fields('533')[counter])
            #     counter += 1
            # if debugMode == '1':
            #     print('533 before: '+str(displayf2))

            if debugMode == '1':
                display533 =[]
                Before533 = rec.get_fields('533')
                for ab in Before533:
                    display533.append(ab.value())
                print('533 before: '+str(display533))

            try:
                while len(rec.get_fields('533')) > 0:
                    rec.remove_field(rec.get_fields('533')[0])
            except IndexError:
                pass

            # display the 533 fields after removal of photocopy - can be commented out
            if debugMode == '1':
                fafter2 = rec.get_fields('533')
                displayfafter2 = []
                for n in fafter2:
                    displayfafter2.append(n.value())
                print('533 after: '+str(displayfafter2))

            # use the OCN to return the PURL and the Abstract value, create the MARC 856 and 520 and add them after deleting any extant fields

            # delete 520

            # just for debugging - show any 520 values before deleting
            if debugMode == '1':
                displayAbstract =[]
                abBefore = rec.get_fields('520')
                for ab in abBefore:
                    displayAbstract.append(ab.value())
                print('520 before: '+str(displayAbstract))

            try:
                while len(rec.get_fields('520')) > 0:
                    rec.remove_field(rec.get_fields('520')[0])
            except IndexError:
                pass

            # # I was requested to delete the 655_7 FAST subject headings. I don't agree with this so this might get axed
            #
            # fastFields = rec.get_fields('650')
            # if debugMode == '1':
            #     ffList = []
            #     for ff in fastFields:
            #         ffList.append(str(ff))
            #     print('650 list before: '+str(ffList))
            #
            # for ff in fastFields:
            #     if ff.indicator2 == '7':
            #         rec.remove_field(ff)
            #
            # if debugMode == '1':
            #     fastFieldsafter = rec.get_fields('650')
            #     ffListAfter = []
            #     for ff in fastFieldsafter:
            #         ffListAfter.append(str(ff))
            #     print('650 list after : '+str(ffListAfter))

            # delete the 856

            # just for debugging - show any 856 values before deleting
            if debugMode == '1':
                displayURL = []
                urlBefore = rec.get_fields('520')
                for url in urlBefore:
                    displayURL.append(url.value())
                print(displayURL)

            try:
                while len(rec.get_fields('856')) > 0:
                    rec.remove_field(rec.get_fields('856')[0])
            except IndexError:
                pass

            # retreive the abstract and the purl based on the OCN tuple
            bib2PurlTuple = bib2PurlDict[OCN]
            purl = bib2PurlTuple[0]
            abstract = bib2PurlTuple[1]

            # declare and add MARC 520/abstract
            marc520 = Field(tag='520', indicators=['3', ' '], subfields=['a', abstract])
            rec.add_field(marc520)
            if debugMode == '1':
                print(str(rec['520']))

            # declare and add MARC 856/PURL
            marc856 = Field(tag='856', indicators=['4', '0'], subfields=['u', purl])
            rec.add_field(marc856)
            if debugMode == '1':
                print(str(rec['856']))

            # In OCLC, edit the 710 field for the year of publication of the original Thesis

            sevenTens = rec.get_fields('710')
            if debugMode == '1':
                print(str(len(sevenTens)))
                print(str(rec['710']))

            # get 710 value by looking up the value with the old Bib# in the bib2PurlTuple
            oldBib = bib2PurlTuple[2]
            try:
                sevenTenValue = sevenTenDict[oldBib]
                sevenTenValue = sevenTenValue.rstrip()
            except KeyError:
                print('problem with 710s for oldBib: '+str(oldBib))

            # call to function to create MARC 710 field if 710 results is not '' (nothing)
            if sevenTenValue != '':
                sevenTen = extract710Subfields(sevenTenValue)
                rec.add_field(sevenTen)
                if debugMode == '1':
                    print(str(rec['710']))
            else:
                if debugMode == '1':
                    print('710 value is blank for '+str(oldBib))
                pass

            # check to see if any part of the MARC 710 subfield f value contains a question mark
            if len(rec.get_fields('710')) > 0:

                test710 = rec['710']['f']
                resultString = ''
                if test710 is not None and '?' in test710:
                    if debugMode == '1':
                        print('"?" found in 710 value - please review')
                    resultString = resultString+str(rec['245'].value())+'\t'+str(oldBib)+'\t'+str(rec['710'].value())+'\n'
                    with open(sevenTenReport, 'a') as x:
                        x.write(resultString)

            # Test that the 856 field works

            if debugMode == '1':
                print('checking URL: '+str(purl))
            try:
                r = urllib.request.urlopen(purl)
            except urllib.error.HTTPError:
                urlProblemStr = str(purl) + '\t' + str(rec['100']['a']) + '\t' + str(oldBib)
                print('\tfound potentially bad url at: ' + urlProblemStr)
            if debugMode == '1':
                print('\tdone checking URL')


            # delete the MARC 035, 001, 003, 005 values
            rec.remove_field(rec.get_fields('035')[0])
            rec.remove_field(rec.get_fields('001')[0])
            rec.remove_field(rec.get_fields('003')[0])
            rec.remove_field(rec.get_fields('005')[0])

            # write updated MARC to file
            writeNewMARC(rec, outputFile)

            if debugMode == '1':
                stops = input('stop? press "n"')
                if stops == 'n':
                    return rec

readETDs()