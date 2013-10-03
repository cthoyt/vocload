#!/usr/local/bin/python

#
# Purpose
#
#	Convert the disease-cluster OBO file to
#	a Synonym-input file (to be used by loadSynonym.sh/py)
#
# Input:
#	The DC-OBO file
#	
#	[Term]
#	=> id: OMIM:615031
#	name: SPASTIC PARAPLEGIA 49, AUTOSOMAL RECESSIVE
#	=> is_a: DC:0000410 ! Spastic paraplegia
#
#	[Term]
#	id: MESH:C537832
#	name: Macular dystrophy, atypical vitelliform
#	=> alt_id: OMIM:153840
#	=> is_a: DC:0000263 ! Macular Dystrophy
#
#	we are only interested in:
#		"id: OMIM:" / "is_a: DC:" for that OMIM id
#		"alt_id: OMIM:" / "is_a: DC:" for that OMIM id
#
# Outpuf:
#	A file in the format for loadSynonym.py
#
#	tab-delimited file:
#		omim id
#		'disease cluster' : name of the disease-cluster synonym type
#		disease-cluster name : from the DC-OBO input file

import sys 
import os
import db

# save list to check for duplicates
omimList = set([])

def createSynonymFile():
	#
	# translate the DC-OBO file into a loadSynonym-input file
	#

	global omimList

	outFile = open(os.environ['DCLUSTERSYN_FILE'], 'w')

	# the omim ids are they are stored in the DC-OBO file
	# returns both "id: OMIM:" and "alt_id: OMIM"
	omimSearch = 'id: OMIM:'

	# the cluster name for the omim id found before it in the DC-OBO file
	CLUSTERNAME = 'is_a: DC:'

	omimID = ''
	synonym = ''

	for line in inFile.readlines():
	
		# looking for OMIM id
		if line.find(omimSearch) >= 0:
			omimID = line[:-1].split(':')[2].strip()
	
		# look for cluster-name associated with the most recent OMIM id
		if line.find(CLUSTERNAME) >= 0:

			synonym = line[:-1].split('!')[1].strip()
	
			# skip duplicates
			if (omimID, synonym) in omimList:
				continue

			if synonym != 'Disease Cluster':
				outFile.write(omimID + '\tdisease cluster\t' + synonym + '\n')

			omimList.add((omimID, synonym))

	outFile.close()
	return 0

def createDiffFile():
	#
	# check if the omim ID is in MGD but not in the cluster file
	# a one-time-only report?
	#

	global omimList

	outFile = open(os.environ['DCLUSTERALL_FILE'], 'w')

	results = db.sql('''
		select a.accID, t.term
		from VOC_Term t, ACC_Accession a 
		where t._Vocab_key = 44
		and t._Term_key = a._Object_key
		and a._MGIType_key = 13
		and a.preferred = 1
		''', 'auto')
	for r in results:
		if r['accID'] not in omimList:
			outFile.write(r['accID'] + '\t' + r['term'] + '\n')

	outFile.close()
	return 0

#
# main
#

inFile = open(os.environ['DCLUSTER_FILE'], 'r')

if createSynonymFile() > 0:
	sys.exit(1)

if createDiffFile() > 0:
	sys.exit(1)

inFile.close()

sys.exit(0)

