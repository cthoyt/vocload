#!/usr/local/bin/python
#
#  loadOBO.py
###########################################################################
#
#  Purpose:
#
#      To load a vocabulary using an OBO format input file.
#
#  Usage:
#
#      loadOBO.py [-n] [-f|-i] [-l <log file>] <RcdFile>
#
#      where
#          -n is the "no load" option
#
#          -f is the option to do a full load
#
#          -i is the option to do an incremental load
#
#          -l is the option that is followed by the log file name
#
#          RcdFile is the rcd file for the vocabulary
#
#  Env Vars:
#
#      See the configuration files
#
#  Inputs:
#
#      - An OBO format input file
#
#  Outputs:
#
#      - Log file
#      - File of terms (Termfile)
#      - 1 or more DAG files (one for each namespace)
#      - Bcp files
#
#  Exit Codes:
#
#      0:  Successful completion
#      1:  An exception occurred
#
#  Assumes:  Nothing
#
#  Implementation:
#
#      This script will perform following steps:
#
#      1) Use the OBOParser module to parse the input file and create
#         the Termfile and DAG file(s).
#
#      2) Invoke the loadVOC module to load the vocabulary.
#
#  Notes:  None
#
###########################################################################
#
#  Modification History:
#
#  Date        SE   Change Description
#  ----------  ---  -------------------------------------------------------
#
#  10/25/2006  DBM  Initial development
#
###########################################################################

import sys 
import os
import string
import re
import getopt

import db
import rcdlib
import Log
import OBOParser
import vocloadlib
import loadVOC

USAGE = 'Usage:  %s [-n] [-f|-i] [-l <log file>] <RcdFile>' % sys.argv[0]

TERM_ABBR = ''
DAG_CHILD_LABEL = ''


# Purpose: Write a status to the log, close the log and exit.
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def exit (status):
    if status == 0:
        log.writeline('OBO load completed successfully')
    else:
        log.writeline('OBO load failed')

    log.close()

    sys.exit(status)


# Purpose: Initialize global variables.
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def initialize():
    global validNamespace
    global validRelationshipType, validSynonymType

    # Create a list of namespaces from the RCD file.
    #
    validNamespace = []
    for (key, record) in config.items():
        validNamespace.append(record['NAME_SPACE'])

    # Get the relationship types and synonym types from the database to
    # use for validation.
    #
    cmds = []
    cmds.append('select label ' + \
                'from DAG_Label ' + \
                'where _Label_key > 0')

    cmds.append('select synonymType ' + \
                'from MGI_SynonymType ' + \
                'where _MGIType_key = 13 and ' + \
                      'allowOnlyOne = 0')

    results = db.sql(cmds, 'auto')

    # Create a list of valid relationship types.  Strip out any characters
    # that are non-alphanumeric to allow for a more accurate comparison to
    # values from the input file.
    #
    validRelationshipType = {}
    for r in results[0]:
        label = re.sub('[^a-zA-Z0-9]', '', r['label'])
        validRelationshipType[label] = r['label']

    # Create a list of valid synonym types.
    #
    validSynonymType = []
    for r in results[1]:
        validSynonymType.append(r['synonymType'])


# Purpose: Open all the input and output files.
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def openFiles():
    global fpOBO, fpValid, fpTerm, fpDAG

    oboFile = os.environ['OBO_FILE']
    validFile = os.environ['VALIDATION_LOG_FILE']
    termFile = os.environ['TERM_FILE']

    # Open the OBO input file.
    #
    try:
        fpOBO = open(oboFile, 'r')
    except:
        log.writeline('Cannot open OBO file: ' + oboFile)
        exit(1)

    # Open the validation log.
    #
    try:
        fpValid = open(validFile, 'w')
    except:
        log.writeline('Cannot open validation log: ' + validFile)
        exit(1)

    # Open the Termfile.
    #
    try:
        fpTerm = open(termFile, 'w')
    except:
        log.writeline('Cannot open term file: ' + termFile)
        exit(1)

    log.writeline('OBO File = ' + oboFile)
    log.writeline('Termfile = ' + termFile)

    # Open a DAG file for each namesapce.
    #
    fpDAG = {}
    for (key, record) in config.items():
        dagFile = record['LOAD_FILE']

        try:
            fpDAG[record['NAME_SPACE']] = open (dagFile, 'w')
        except:
            log.writeline('Cannot open DAG file: ' + dagFile)
            exit(1)

        log.writeline('DAG file = ' + dagFile)


# Purpose: Close all the input and output files.
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def closeFiles():
    fpOBO.close()
    fpValid.close()
    fpTerm.close()
    for i in fpDAG.values():
        i.close()


# Purpose: Use an OBOParser object to get header/term attributes from the
#          OBO input file and use this information to create the Termfile
#          and DAG file(s).
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def parseOBOFile():
    openFiles()

    # Get the expect version for the OBO input file.
    #
    expectedVersion = os.environ['OBO_FILE_VERSION']

    # If there is a root ID for the vocabulary, write it to each DAG file.
    # Even though the root term may be defined in the OBO input file, it
    # will not have any relationships defined, so it would not get added
    # to the DAG file when the term is process below.
    #
    dagRootID = os.environ['DAG_ROOT_ID']
    if dagRootID:
        for i in validNamespace:
            fpDAG[i].write(dagRootID + '\t' + '\t' + '\t' + '\n')

    log.writeline('Parse OBO file')

    # Create an OBO parser that will return attributes from the OBO
    # input file.
    #
    parser = OBOParser.Parser(fpOBO)

    # Get the header from the parser and save its attributes.
    #
    header = parser.getHeader()
    version = header.getVersion()
    defaultNamespace = header.getDefaultNamespace()

    # If the OBO input file does not have the expected version number,
    # write a validation message and terminate the load.
    #
    if version != expectedVersion:
        log.writeline('Invalid OBO format version: ' + version + \
                      ' (Expected: ' + expectedVersion + ')')
        closeFiles()
        return 1

    # Get the first term from the parser.
    #
    term = parser.nextTerm()

    # Process each term returned by the parser.
    #
    while term != None:

        # Get the attributes of the term.
        #
        termID = term.getTermID()
        name = term.getName()
        namespace = term.getNamespace()
        comment = term.getComment()
        definition = term.getDefinition()
        obsolete = term.getObsolete()
        altID = term.getAltID()
        relationship = term.getRelationship()
        relationshipType = term.getRelationshipType()
        synonym = term.getSynonym()
        synonymType = term.getSynonymType()

        isValid = 1

        # Validate the namespace.  The namespace is used to determine which
        # DAG file to write to for cases where there are multiple DAG for
        # a vocabulary (e.g. GO vocabulary).  If the term does not define
        # a namespace, use the default namespace that came from the header.
        #
        if namespace != '':
            if namespace not in validNamespace:
                fpValid.write('(' + termID + ') Invalid namespace: ' + namespace + '\n')
                isValid = 0
        else:
            namespace = defaultNamespace

        # Validate the relationship type(s).  Strip out any characters that
        # are non-alphanumeric so they can be compared to the values from
        # the database.  This will allow a match on relationship types such
        # "is_a" vs "is-a".
        #
        for r in relationshipType:
            label = re.sub('[^a-zA-Z0-9]','',r)
            if not validRelationshipType.has_key(label):
                fpValid.write('(' + termID + ') Invalid relationship type: ' + r + '\n')
                isValid = 0

        # Validate the synonym type(s).
        #
        for s in synonymType:
            if string.lower(s) not in validSynonymType:
                fpValid.write('(' + termID + ') Invalid synonym type: ' + s + '\n')
                isValid = 0

        # If there are no validation errors, the term can be processed
        # further.
        #
        if isValid:

            # Remove any tabs from the definition, so it does not mess up
            # the formatting of the Termfile.
            #
            definition = re.sub('\t', '', definition)

            # Determine what status to use in the Termfile.
            #
            if obsolete:
                status = 'obsolete'
            else:
                status = 'current'

            # Write the term information to the Termfile.
            #
            fpTerm.write(name + '\t' + \
                         termID + '\t' + \
                         status + '\t' + \
                         TERM_ABBR + '\t' + \
                         definition + '\t' + \
                         comment + '\t' + \
                         string.join(synonym,'|') + '\t' + \
                         string.join(synonymType,'|') + '\t' + \
                         string.join(altID,'|') + '\n')

            # If the term name is the same as the namespace AND there is a
            # root ID, write a record to the DAG file that relates this
            # term to the root ID.
            #
            if name == namespace and dagRootID:
                fpDAG[namespace].write(termID + '\t' + '\t' + 'is-a' + '\t' + \
                                       dagRootID + '\n')

            # Write to the DAG file.
            #
            for i in range(len(relationship)):
                fpDAG[namespace].write(termID + '\t' + \
                                        DAG_CHILD_LABEL + '\t' + \
                                        validRelationshipType[re.sub('[^a-zA-Z0-9]','',relationshipType[i])] + '\t' + \
                                        relationship[i] + '\n')

        # Get the next term from the parser.
        #
        term = parser.nextTerm()

    closeFiles()
    return 0


#
#  MAIN
#

# Get the options that were passed to the script.
#
try:
    options, args = getopt.getopt(sys.argv[1:], 'nfil:')
except:
    print USAGE
    sys.exit(1)

# After getting the options, only the RCD file should be left in the
# argument list.
#
if len(args) > 1:
    print USAGE
    sys.exit(1)

rcdFile = args[0]

# Process the options to get the mode for the loadVOC module, the "noload"
# indicator and the log file.
#
noload = 0
for (option, value) in options:
    if option == '-f':
        mode = 'full'
    elif option == '-i':
        mode = 'incremental'
    elif option == '-n':
        vocloadlib.setNoload()
        noload = 1
    elif option == '-l':
        log = Log.Log (filename = value, toStderr = 0)
    else:
        pass

if not log:
    log = Log.Log(toStderr = 0)

# Create a configuration object from the RCD file.
#
config = rcdlib.RcdFile (rcdFile, rcdlib.Rcd, 'NAME')

# Perform initialization tasks.
#
initialize()

# Parse the OBO input file.
#
if parseOBOFile() != 0:
    exit(1)

# Invoke the loadVOC module to load the terms and build the DAG(s).
#
vocload = loadVOC.VOCLoad(config, mode, log)
vocload.go()

exit(0)