	#!bin/bash

## generate list of entities in kb

# create person lists
# combining multiple sources, using extern script
#bash ./name_list.sh KB_cs.all

#

grep KB_cs.all -ne person | cut -f1,2 $1| awk -F: '{print $2"|"$1}'| cut -f2  | sort -u > lists/PersonListSorted.txt

grep KB_cs.all -ne organisation | cut -f1,2| awk -F: '{print $2"|"$1}'| cut -f2 | sort -u > lists/OrganisationListSorted.txt

#
grep KB_cs.all -ne event | cut -f1,2| awk -F: '{print $2"|"$1}'| cut -f2 | sort -u > lists/EventListSorted.txt


#### GEO LISTS
#
grep KB_cs.all -ne populatedPlace | cut -f1,2| awk -F: '{print $3"|"$1}'| cut -f2 | sort -u > lists/LocationListSorted.txt

#
grep KB_cs.all -ne protectedArea | cut -f1,2| awk -F: '{print $3"|"$1}'| cut -f2 | sort -u  > lists/PAListSorted.txt

#
grep KB_cs.all -ne conservationArea | cut -f1,2| awk -F: '{print $3"|"$1}'| cut -f2 | sort -u  > lists/CAListSorted.txt

#
grep KB_cs.all -ne mountain | cut -f1,2| awk -F: '{print $3"|"$1}'| cut -f2 | sort -u  > lists/MountainListSorted.txt

#
grep KB_cs.all -ne castle | cut -f1,2| awk -F: '{print $2"|"$1}'| cut -f2 | sort -u  > lists/CastleListSorted.txt

#
grep KB_cs.all -ne lake | cut -f1,2| awk -F: '{print $3"|"$1}'| cut -f2 | sort -u  > lists/LakeListSorted.txt

#
grep KB_cs.all -ne forest | cut -f1,2| awk -F: '{print $3"|"$1}'| cut -f2 | sort -u  > lists/ForestListSorted.txt

#
grep KB_cs.all -ne mountainPass | cut -f1,2| awk -F: '{print $3"|"$1}'| cut -f2 | sort -u  > lists/MPListSorted.txt

#
grep KB_cs.all -ne mountainRange | cut -f1,2| awk -F: '{print $3"|"$1}'| cut -f2 | sort -u  > lists/MRListSorted.txt

#
grep KB_cs.all -ne river | cut -f1,2| awk -F: '{print $3"|"$1}'| cut -f2 | sort -u  > lists/RiverListSorted.txt

#
grep KB_cs.all -ne observationTower | cut -f1,2| awk -F: '{print $3"|"$1}'| cut -f2 | sort -u  > lists/OTListSorted.txt

#
grep KB_cs.all -ne waterfall | cut -f1,2| awk -F: '{print $3"|"$1}'| cut -f2 | sort -u  > lists/WaterfallListSorted.txt

##### GEO LISTS END

## MERGE GEO ENTITIES TO ONE LIST

cat lists/LocationListSorted.txt > lists/GEOEntitiesList.txt
cat lists/PAListSorted.txt      >> lists/GEOEntitiesList.txt
cat lists/CAListSorted.txt      >> lists/GEOEntitiesList.txt
cat lists/MountainListSorted.txt      >> lists/GEOEntitiesList.txt
cat lists/CastleListSorted.txt      >> lists/GEOEntitiesList.txt
cat lists/LakeListSorted.txt      >> lists/GEOEntitiesList.txt
cat lists/ForestListSorted.txt      >> lists/GEOEntitiesList.txt
cat lists/MPListSorted.txt      >> lists/GEOEntitiesList.txt
cat lists/MRListSorted.txt      >> lists/GEOEntitiesList.txt
cat lists/RiverListSorted.txt      >> lists/GEOEntitiesList.txt
cat lists/OTListSorted.txt      >> lists/GEOEntitiesList.txt
cat lists/WaterfallListSorted.txt      >> lists/GEOEntitiesList.txt

cat lists/GEOEntitiesList.txt | sort -u > lists/GEOEntitiesListSorted.txt

rm lists/GEOEntitiesList.txt

cat lists/GEOEntitiesListSorted.txt > lists/finalList.txt
cat lists/PersonListSorted.txt >> lists/finalList.txt
cat lists/OrganisationListSorted.txt >> lists/finalList.txt
cat lists/EventListSorted.txt >> lists/finalList.txt

cat lists/finalList.txt | sort -u > lists/finalListSorted1.txt

cat lists/finalListSorted1.txt | sed 's/|/\t/' > lists/finalListSorted.txt

rm lists/finalList.txt lists/finalListSorted1.txt

python list_correction.py -i lists/finalListSorted.txt

## MERGE END
