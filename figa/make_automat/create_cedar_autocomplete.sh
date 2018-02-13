#!/bin/sh

export LC_ALL="C.UTF-8"

# default values
KB="KBstatsMetrics.all"
KB_GIVEN=false
CEDAR=false
DARTS=false
EXT=".ct"

# saved values
LAUNCHED=$0
KB_WORKDIR=$PWD

#=====================================================================
# nastavovani parametru prikazove radky

usage()
{
    echo "Usage: create_cedar_autocomplete.sh [-h] [-c|-d] --knowledge-base=KBstatsMetrics.all"
    echo ""
    echo "\t-h --help"
    echo "\t-c --cedar (default)"
    echo "\t-d --darts"
    echo "\t-k --knowledge-base=$KB"
    echo ""
}

while [ "$1" != "" ]; do
    PARAM=`echo $1 | awk -F= '{print $1}'`
    VALUE=`echo $1 | awk -F= '{print $2}'`
    case $PARAM in
        -h | --help)
            usage
            exit
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

#======================================================================
# vytvorenie zoznamu klucov entit v KB a vyhodenie fragmentov zo zoznamu
python3 KB2namelist.py -a < "$KB" | tr -s ' ' | grep -v -e "[^;]N" > intext_auto
cat intext_auto | grep "^person:" | sed 's/^person:\t//' > p_intext
cat intext_auto | grep "^artist:" | sed 's/^artist:\t//' > a_intext
cat intext_auto | grep "^location:" | sed 's/^location:\t//' > l_intext
cat intext_auto | grep "^artwork:" | sed 's/^artwork:\t//' > w_intext
cat intext_auto | grep "^museum:" | sed 's/^museum:\t//' > c_intext
cat intext_auto | grep "^event:" | sed 's/^event:\t//' > e_intext
cat intext_auto | grep "^visual_art_form:" | sed 's/^visual_art_form:\t//' > f_intext
cat intext_auto | grep "^visual_art_medium:" | sed 's/^visual_art_medium:\t//' > d_intext
cat intext_auto | grep "^art_period_movement:" | sed 's/^art_period_movement:\t//' > m_intext
cat intext_auto | grep "^visual_art_genre:" | sed 's/^visual_art_genre:\t//' > g_intext
cat intext_auto | grep "^nationality:" | sed 's/^nationality:\t//' > n_intext
cat intext_auto | grep "^mythology:" | sed 's/^mythology:\t//' > y_intext
cat intext_auto | grep "^family:" | sed 's/^family:\t//' > i_intext
cat intext_auto | grep "^group:" | sed 's/^group:\t//' > r_intext
cut -f2- intext_auto > x_intext

#======================================================================
# parsovanie confidence hodnot do samostatneho suboru + stop list
cat "$KB" | awk '{print $(NF)}' > KB_confidence
cp stop_list stop_list.all.sorted

#======================================================================
# skript, ktery slouci duplicty (cisla radku do jednoho)
python uniq_namelist.py -s "KB_confidence" < p_intext > p_namelist
python uniq_namelist.py -s "KB_confidence" < a_intext > a_namelist
python uniq_namelist.py -s "KB_confidence" < l_intext > l_namelist
python uniq_namelist.py -s "KB_confidence" < w_intext > w_namelist
python uniq_namelist.py -s "KB_confidence" < c_intext > c_namelist
python uniq_namelist.py -s "KB_confidence" < e_intext > e_namelist
python uniq_namelist.py -s "KB_confidence" < f_intext > f_namelist
python uniq_namelist.py -s "KB_confidence" < d_intext > d_namelist
python uniq_namelist.py -s "KB_confidence" < m_intext > m_namelist
python uniq_namelist.py -s "KB_confidence" < g_intext > g_namelist
python uniq_namelist.py -s "KB_confidence" < n_intext > n_namelist
python uniq_namelist.py -s "KB_confidence" < x_intext > x_namelist
python uniq_namelist.py -s "KB_confidence" < y_intext > y_namelist
python uniq_namelist.py -s "KB_confidence" < i_intext > i_namelist
python uniq_namelist.py -s "KB_confidence" < r_intext > r_namelist

#======================================================================
# vytvoreni konecneho automatu
../figav1.0 -d p_namelist -n -w ../p_automata"$EXT"
../figav1.0 -d a_namelist -n -w ../a_automata"$EXT"
../figav1.0 -d l_namelist -n -w ../l_automata"$EXT"
../figav1.0 -d w_namelist -n -w ../w_automata"$EXT"
../figav1.0 -d c_namelist -n -w ../c_automata"$EXT"
../figav1.0 -d e_namelist -n -w ../e_automata"$EXT"
../figav1.0 -d f_namelist -n -w ../f_automata"$EXT"
../figav1.0 -d d_namelist -n -w ../d_automata"$EXT"
../figav1.0 -d m_namelist -n -w ../m_automata"$EXT"
../figav1.0 -d g_namelist -n -w ../g_automata"$EXT"
../figav1.0 -d n_namelist -n -w ../n_automata"$EXT"
../figav1.0 -d x_namelist -n -w ../x_automata"$EXT"
../figav1.0 -d y_namelist -n -w ../y_automata"$EXT"
../figav1.0 -d i_namelist -n -w ../i_automata"$EXT"
../figav1.0 -d r_namelist -n -w ../r_automata"$EXT"

#=====================================================================
# smazani mezivysledku
rm -f intext_auto *_intext
rm -f *_namelist
rm -f KB_confidence

