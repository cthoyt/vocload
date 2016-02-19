#!/bin/sh
#
#  emapQC.sh
###########################################################################
#
#  Purpose:
#
#      This script is a wrapper around the process that does sanity
#      checks for the EMAPA/EMAPS load
#
#  Usage:
#
#      emapQC.sh  filename  
#
#      where
#          filename = path to the input file
#
#  Env Vars:
#
#      See the configuration file
#
#  Inputs:
#	EMAPA obo file
#
#  Outputs:
#
#      - sanity report for the input file.
#
#      - Log file (${QC_LOGFILE})
#
#  Exit Codes:
#
#      0:  Successful completion
#      1:  Fatal error occurred
#
#  Assumes:  Nothing
#
#  Implementation:
#
#      This script will perform following steps:
#
#      ) Validate the arguments to the script.
#      ) Validate & source the configuration files to establish the environment.
#      ) Verify that the input file exists.
#      ) Initialize the log and report files.
#      ) Call sanity.sh and emapload.sh to generate the sanity/QC report.
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
#  10/17/2013  sc  Initial development
#
###########################################################################

cd `dirname $0`

CURRENTDIR=`pwd`

CONFIG=emapload.config
USAGE='Usage: emapQC.sh  filename'

# this is a sanity check only run, set LIVE_RUN accordingly
LIVE_RUN=0; export LIVE_RUN

#
# Make sure an input file was passed to the script. 
#
if [ $# -eq 1 ]
then
    INPUT_FILE=$1
else
    echo ${USAGE}; exit 1
fi

#
# Make sure the configuration file exists and source it.
#
if [ -f ${CONFIG} ]
then
    . ${CONFIG}
else
    echo "Missing configuration file: ${CONFIG}"
    exit 1
fi

#
# Make sure the input file exists (regular file or symbolic link).
#
if [ "`ls -L ${INPUT_FILE} 2>/dev/null`" = "" ]
then
    echo "Missing input file: ${INPUT_FILE}"
    exit 1
fi

#
# Initialize the log file.
#
QC_LOGFILE=${CURRENTDIR}/`basename ${QC_LOGFILE}`
LOG=${QC_LOGFILE}
rm -rf ${LOG}
touch ${LOG}

#
# Initialize the report files to make sure the current user can write to them.
#
rm -f ${QC_ERROR_RPT} >${QC_ERROR_RPT}
rm -f ${QC_WARNING_RPT}; >${QC_WARNING_RPT}

#
# Run sanity checks on EMAPA obo file
#
echo "" >> ${LOG}
date >> ${LOG}
echo "Run sanity checks on the input file" >> ${LOG}

# run the first set of sanity checks (non well-formed obo file or proprietary
# EMAPA obo file checks)
${VOCLOAD}/emap/sanity.sh ${INPUT_FILE}
STAT=$?
if [ ${STAT} -ne 0 ]
then
    echo ""
    echo "Invalid OBO format $1"
    echo "Version ${OBO_FILE_VERSION} expected"
    echo ""
    exit ${STAT}
fi

# the DEFAULT input file is the file passed to this script
INPUT_FILE_DEFAULT=${INPUT_FILE}
export INPUT_FILE_DEFAULT

# run emapload.py in sanity check only mode (LIVE_RUN = 0)
FILE_ERROR=0
${VOCLOAD}/emap/emapload.py
if [ $? -ne 0 ]
then
    FILE_ERROR=1
fi

date >> ${LOG}
cp ${QC_ERROR_RPT} ${CURRENTDIR}
cp ${QC_WARNING_RPT} ${CURRENTDIR}

if [ ${FILE_ERROR} -ne 0 ]
then
    echo "Finished sanity checks: failed" >> ${LOG}
    exit 1
else
    echo "Finished sanity checks: successful" >> ${LOG}
    exit 0
fi

