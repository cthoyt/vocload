#!/bin/sh

#
# Main Wrapper Script for Downloading OMIM files and loading OMIM terms
#

# Define return codes
SUCCESS=0
FAILURE=1

# These environment variables should really be placed inside the omim.rcd; however,
# since the omim.rcd is python-based they are temporarily placed here.  To address
# this problem in the future, we should write a python program which reads
# and exports all environment variables in an .rcd file, placing the call
# to the program inside the shell script. For now, the variables are placed here.
RUNTIME_DIR="./runTimeOMIM/"
ARCHIVE_DIR="./archiveOMIM/"

SYBASE=/opt/sybase/12.5
PYTHONPATH=/usr/local/mgi/lib/python
PATH=$PATH:.:/usr/bin:$SYBASE/ASE-12_5/bin:$SYBASE/OCS-12_5/bin:/usr/java/bin
FULL_LOG_FILE=$RUNTIME_DIR"fullLog.txt"
MAINTAINER="lec@informatics.jax.org"
ARCHIVE_FILE_NAME=$ARCHIVE_DIR"vocload.`date +%Y%m%d:%H:%M`.jar"
LOAD_LOG_FILE=$RUNTIME_DIR"log.txt"
LOAD_DATA_FILE="omim.tab"
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$SYBASE/OCS-12_5/lib

export RUNTIME_DIR
export SYBASE
export PYTHONPATH
export PATH
export LD_LIBRARY_PATH

die()
{
   echo $1
   cat $FULL_LOG_FILE | mailx -s "OMIM Load Catastrophic FAILURE" $MAINTAINER 
   exit $FAILURE
}

changeToRunDirectory()
{
   APPDIR=`dirname $0`
   if test $APPDIR != "."
   then
      cd "$APPDIR"
   fi
}

createDir()
{
   if [ ! -d $1 ]
   then
      echo "...creating data directory $1"
      mkdir $1
   fi
}

writePgmExecutionHeaders()
{
   echo "Running $1 Program..."
   echo "*****************************************" >> $FULL_LOG_FILE 2>&1
   echo "Running $1 Program..."                     >> $FULL_LOG_FILE 2>&1
   echo "*****************************************" >> $FULL_LOG_FILE 2>&1
   echo "Program call:"                             >> $FULL_LOG_FILE 2>&1
}

writePgmLogFile()
{
   echo "$1 Log File:"                              >> $FULL_LOG_FILE 2>&1
   cat $2                                           >> $FULL_LOG_FILE 2>&1
   echo "*****************************************" >> $FULL_LOG_FILE 2>&1
   echo "*****************************************" >> $FULL_LOG_FILE 2>&1
}

JOB_SUCCESSFUL="false"

changeToRunDirectory
umask 002
createDir $RUNTIME_DIR
createDir $ARCHIVE_DIR
echo "Job Started: `date`"
echo "Job Started: `date`"                          > $FULL_LOG_FILE 2>&1
echo "Directory is: `pwd`"
#################################################################################
# Check Usage and options
#################################################################################
USAGE_STRING="Incorrect Usage\nCorrect Usage: $0 [load|noload] [full|incremental] \nExample: $0 load incremental"

if [ $# -ne 2 ] 
then
   die "$USAGE_STRING"
fi

echo "*****************************************" >> $FULL_LOG_FILE 2>&1
case $1 in
   load) LOAD_FLAG=""        
   echo  "DATABASE LOAD STATUS is LOAD" >> $FULL_LOG_FILE 2>&1
   ;;
   noload) LOAD_FLAG=-n      
   echo  "DATABASE LOAD STATUS is NO LOAD" >> $FULL_LOG_FILE 2>&1
   ;;
   *) die "$USAGE_STRING"    ;;
esac
case $2 in
   incremental) MODE_FLAG=-i ;;
   full) MODE_FLAG=-f        ;;
   *) die "$USAGE_STRING"    ;;
esac
echo  "MODE STATUS is $2" >> $FULL_LOG_FILE 2>&1
echo "*****************************************" >> $FULL_LOG_FILE 2>&1

######################################################
# 1. Run omim.load program
######################################################
LOAD_PROGRAM=omim.load
LOAD_PROGRAM_CALL="omim.load $LOAD_FLAG $MODE_FLAG -l $LOAD_LOG_FILE omim.rcd $LOAD_DATA_FILE"

writePgmExecutionHeaders $LOAD_PROGRAM
echo $LOAD_PROGRAM_CALL                       >> $FULL_LOG_FILE 2>&1
echo "*****************************************" >> $FULL_LOG_FILE 2>&1

msg=`$LOAD_PROGRAM_CALL 2>&1`
rc=$?

writePgmLogFile $LOAD_PROGRAM, $LOAD_LOG_FILE

case $rc in
     $FAILURE)
        ERROR_MSG="omim.load FAILED!!!! - Check Log File: $FULL_LOG_FILE"
        echo $ERROR_MSG
        echo $0:$ERROR_MSG                 >> $FULL_LOG_FILE 2>&1
        echo "$0:Ouput is: $msg" >> $FULL_LOG_FILE 2>&1
        die "$ERROR_MSG";;

     $SUCCESS)
        ERROR_MSG="omim.load Was Successful - No Errors Encountered"
        JOB_SUCCESSFUL="true"
        echo $ERROR_MSG
        echo $0:$ERROR_MSG                 >> $FULL_LOG_FILE 2>&1;;
esac
cat $LOAD_LOG_FILE                      >> $FULL_LOG_FILE 2>&1
LOAD_ERROR_MSG=$ERROR_MSG

######################################################
# 3. Finally, archive the files
######################################################
# We are using "jar" rather than "tar", because jar compressed
# the files to 6 times smaller than tar and its syntax is 
# identical to tar
# We are archiving everything at this point since this is the
# first release of the software and, for that reason it might
# be helpful to archive everything in case of problems; however,
# we might want to be more selective in the future.  We will
# also need an archival clean-up routine in the future as well
JAR_PROGRAM=jar
JAR_PROGRAM_CALL="jar cvf $ARCHIVE_FILE_NAME $RUNTIME_DIR/*"

writePgmExecutionHeaders $JAR_PROGRAM
echo $JAR_PROGRAM_CALL                           >> $FULL_LOG_FILE 2>&1
echo "*****************************************" >> $FULL_LOG_FILE 2>&1
msg=`$JAR_PROGRAM_CALL  2>&1`
rc=$?
case $rc in
     $FAILURE)
        ERROR_MSG="JAR Failed!!!! - Check Archive"
        echo $ERROR_MSG
        echo $0:$ERROR_MSG                 >> $FULL_LOG_FILE 2>&1
        echo "$0:JAR Ouput is: $msg"       >> $FULL_LOG_FILE 2>&1;;

     $SUCCESS)
        ERROR_MSG="JAR Was Successful - No Errors Encountered"
        echo $ERROR_MSG
        echo $0:$ERROR_MSG                 >> $FULL_LOG_FILE 2>&1;;
   
     *)
        ERROR_MSG="JAR Had Warnings!!!  Archive"
        echo $ERROR_MSG
        echo $0:$ERROR_MSG                 >> $FULL_LOG_FILE 2>&1
        echo "$0:JAR Ouput is: $msg"       >> $FULL_LOG_FILE 2>&1;;

esac
JAR_PROGRAM_ERROR_MSG=$ERROR_MSG
######################################################
# 4. Notify Job Completion
######################################################
if test $JOB_SUCCESSFUL = "true"
then
   SUBJECT="OMIM Load Successful"
else
   SUBJECT="OMIM Load Failed"
fi
echo $SUBJECT

echo "Run Summary:"                                                                  > $$.txt
echo "****************************************************************************" >> $$.txt
echo "OMIM Load Program Completion Status: $LOAD_ERROR_MSG"                         >> $$.txt
echo "****************************************************************************" >> $$.txt
echo "Archive Program Completion Status: $JAR_PROGRAM_ERROR_MSG"                    >> $$.txt
echo "****************************************************************************" >> $$.txt
echo ""   >> $$.txt
echo ""   >> $$.txt
echo ""   >> $$.txt
echo "Full Log File is as follows:"                                                 >> $$.txt
echo "************************************************************************"     >> $$.txt
echo "************************************************************************"     >> $$.txt


echo "Job Complete: `date`"
echo "Job Complete: `date`"                                                         >> $FULL_LOG_FILE 2>&1

cat $$.txt $FULL_LOG_FILE | mailx -s "$SUBJECT" $MAINTAINER 

rm -rf $$.txt