#!/bin/sh
#
#  loadOBO-DC.sh
###########################################################################
#
#  Purpose:
#
#      Load the OBO-Diseaes-Cluster "Synonyms" file into the VOC_Synonym table 
#      and call the Python script that uses this data to add synonym for the given terms.
#
#  Usage:
#
#      loadOBO-DC.sh  ConfigFile
#
#      where
#
#          ConfigFile is the name of the configuration file for the
#                     specific vocabulary load (e.g. OMIM.config).
#
#  Env Vars:
#
#      See the configuration files
#
#  Inputs:
#
#      - OBO-DC-Synonym file - contains accession IDs for each term, along with
#                       a synonym type and synonym to be added for the term;
#			in OBO format
#
#  Outputs:
#
#      - Log file (${FULL_LOG_FILE})
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
#      This script will perform following steps to add the synonyms for the
#      given terms:
#
#      1) Translate the OBO-DC input file into Synonym-format
#      2) Truncate the VOC_Synonym table in the RADAR database.
#      3) Use bcp to load the Synonym-formateted file into the VOC_Synonym table.
#      3) Call the loadSynonym.py script to add the synonyms for the terms.
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
#  10/02/2013  lec  TR11423/human disease portal (HDP)
#		     copied this from loadSynonym.csh and modified accordingly
#
###########################################################################

if [ $# -ne 1 ]
then
    echo "Usage:  $0  ConfigFile"
    exit 1
fi
LOAD_CONFIG=$1

#
#  Source the configuration files to establish the environment.
#
cd `dirname $0`
. ${LOAD_CONFIG}
. ./Configuration

#
# convert the OBO-DC file to a Synonym-input file
#
./loadOBO-DC.py >> ${FULL_LOG_FILE}

#
# re-set the SYNONYM_FILE to the disease-cluster synonym file name
# so we can use the loadSynonym.py script
#
SYNONYM_FILE=${DCLUSTERSYN_FILE}

echo "**************************************************" >> ${FULL_LOG_FILE}
echo "Start synonym file processing: ${SYNONYM_FILE}" >> ${FULL_LOG_FILE}

#
#  Truncate the VOC_Synonym table in the RADAR database to remove any
#  current records.
#
echo "Truncate VOC_Synonym table" >> ${FULL_LOG_FILE}
${RADAR_DBSCHEMADIR}/table/VOC_Synonym_truncate.object >> ${FULL_LOG_FILE}

#
#  Load the VOC_Synonym table from the synonym file using bcp.
#
echo "Load the synonym file into the VOC_Synonym table" >> ${FULL_LOG_FILE}
${MGI_DBUTILS}/bin/bcpin.csh ${RADAR_DBSERVER} ${RADAR_DBNAME} VOC_Synonym ${RUNTIME_DIR} ${DCLUSTER_FILENAME} "\t" "\n" >> ${FULL_LOG_FILE}

#
#  Call the Python script.
#

echo "Start loadSynonym.py" >> ${FULL_LOG_FILE}
loadSynonym.py >> ${FULL_LOG_FILE}
echo "End loadSynonym.py" >> ${FULL_LOG_FILE}

echo "End synonym file processing" >> ${FULL_LOG_FILE}
echo "**************************************************" >> ${FULL_LOG_FILE}

exit 0