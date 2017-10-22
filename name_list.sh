#!bin/bash
function print_usage {
   echo "USAGE: bash name_list.sh kb_file_name authority_person.mrc";
   
}

if [ $# -ne 1 ]; then
    print_usage
fi

# process czech KB
cut -f1,2 $1 | grep -e "artist" -e "person" | awk -F: '{print $2"|"$1}'| cut -f2  | sort -u > csKB_PersonList.txt

# proces mrc file:
# preprocess
#grep -e " 1001 " $2 > mrc_pp.tmp
## parse
#python3 ./utils/getPersonsFromMRCfile.py mrc_pp.tmp > namelist.tmp
## rm tmp
#rm mrc_pp.tmp

# merge lists:

## with mrc
# cat namelist.tmp > PersonList.txt
# cat csKB_PersonList.txt >> PersonList.txt
## without mrc
cat csKB_PersonList.txt > PersonList.txt
##########################################
sort -u PersonList.txt -o PersonListSorted.txt
mv ./PersonListSorted.txt ./lists/

rm csKB_PersonList.txt PersonList.txt 
