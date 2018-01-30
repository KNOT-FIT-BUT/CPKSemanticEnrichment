#!/bin/sh

# Author: Lubomir Otrusina, iotrusina@fit.vutbr.cz

export LC_ALL="C.UTF-8"

# default values
KB="KBstatsMetrics.all"
KB_GIVEN=false
LOWERCASE=false
URI=false
CEDAR=false
DARTS=false
EXT=".ct"

#=====================================================================
# nastavovani parametru prikazove radky

usage()
{
    echo "Usage: create_cedar.sh [-h] [-l|-u] [-c|-d] --knowledge-base=KBstatsMetrics.all"
    echo ""
    echo "\t-h --help"
    echo "\t-l --lowercase"
    echo "\t-u --uri"
    echo "\t-c --cedar (default)"
    echo "\t-d --darts"
    echo "\t-k --knowledge-base=$KB"
    echo ""
}

LAUNCHED=$0
KB_WORKDIR=$PWD

while [ "$1" != "" ]; do
    PARAM=`echo $1 | awk -F= '{print $1}'`
    VALUE=`echo $1 | awk -F= '{print $2}'`
    case $PARAM in
        -h | --help)
            usage
            exit
            ;;
        -l | --lowercase)
            LOWERCASE=true
            ;;
        -u | --uri)
            URI=true
            ;;
        -c | --cedar)
            CEDAR=true
            ;;
        -d | --darts)
            DARTS=true
            ;;
        -k | --knowledge-base)
            if [ "$PARAM" = "-k" ]; then
              if [ "$2" = "" ]; then
                usage
                exit
              else
                VALUE="$2"
                shift
              fi
            fi

            KB=$VALUE
            KB_GIVEN=true
            ;;
        *)
            echo "ERROR: unknown parameter \"$PARAM\""
            usage
            exit 1
            ;;
    esac
    shift
done

if $CEDAR && $DARTS ; then
  usage
  exit
elif [ ! -f "$KB" ]; then
  echo "ERROR: Could not found KB on path: ${KB}" >&2
  if ! $KB_GIVEN ; then
    echo "Did you forget to set the parameter \"-k\"? (Default \"${KB}\" was used.)\n" >&2
    
    usage
  fi
  exit
elif $DARTS ; then
  EXT=".dct"
fi

#=====================================================================
# zmena spousteci cesty na tu, ve ktere se nachazi create_cedar.sh
cd `dirname "${LAUNCHED}"`
# ale soucasne je treba zmenit cestu ke KB, jinak bychom problem posunuli jinam
KB="${KB_WORKDIR}/${KB}"


#=====================================================================
python get_persons_with_genders.py -p "$KB" > persons_with_genders
python3 czechnames/namegen.py -o czechnames.out persons_with_genders


#=====================================================================
# vytvoreni seznamu klicu entit v KB

if $LOWERCASE ; then
  python KB2namelist.py -l < "$KB" | tr -s ' ' > intext
elif $URI ; then
  python KB2namelist.py -u < "$KB" > intext
else
  python KB2namelist.py < "$KB" | tr -s ' ' > intext
fi

#=====================================================================
# pridani fragmentu jmen a prijmeni entit

if ! $URI ; then
  python get_names.py > names
  sort -u < names | sed 's/$/\tN/' > fragments
  cat fragments >> intext
fi

#=====================================================================
# uprava stoplistu (kapitalizace a razeni)

if ! $URI ; then
  python get_morphological_forms.py < Czech.txt | sort -u > stop_list.var
  cp stop_list.var stop_list.all
  sed -e 's/\b\(.\)/\u\1/g' < stop_list.var >> stop_list.all
  tr 'a-z' 'A-Z' < stop_list.var >> stop_list.all
  tr 'A-Z' 'a-z' < stop_list.var >> stop_list.all
  sort -u stop_list.all > stop_list.all.sorted
fi

#=====================================================================
# parsovanie confidence hodnot do samostatneho suboru
# redukcia duplicit, abecedne zoradenie entit
# odstranovani slov ze stop listu

if ! $URI ; then
  awk '{print $(NF)}' < "$KB" > KB_confidence
  python uniq_namelist.py -s "KB_confidence" < intext > namelist
else
  python uniq_namelist.py < intext > namelist
fi

#=====================================================================
# vytvoreni konecneho automatu

if $LOWERCASE ; then
  ../figav1.0 -d namelist -n -w ../automata-lower"$EXT"
elif $URI ; then
  ../figav1.0 -d namelist -n -w ../automata-uri"$EXT"
else
  ../figav1.0 -d namelist -n -w ../automata"$EXT"
fi

#=====================================================================
# smazani pomocnych souboru

#rm -f names
#rm -f fragments
#rm -f intext
#rm -f stop_list.all stop_list.var stop_list.all.sorted
#rm -f namelist
#rm -f KB_confidence

