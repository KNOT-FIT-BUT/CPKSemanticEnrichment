#/bin/sh

# default values
SAVE_PARAMS=$*
LOG=false
ONLY_DICT=false

# saved values
LAUNCHED=$0

#=====================================================================
# nastavovani parametru prikazove radky

usage()
{
    echo "Usage: start.sh [-h] [--log] [--only_dict]"
    echo ""
    echo -e "\t-h --help      show this help message and exit"
    echo -e "\t--log          log to start.sh.stdout, start.sh.stderr and start.sh.stdmix"
    echo -e "\t--only_dict    rebuild only dictionaries, not KB"
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
        --log)
            LOG=true
            ;;
        --only_dict)
            ONLY_DICT=true
            ;;
        *)
            echo "ERROR: unknown parameter \"$PARAM\""
            usage
            exit 1
            ;;
    esac
    shift
done

# zmena spousteci cesty na tu, ve ktere se nachazi start.sh
cd `dirname "${LAUNCHED}"`

if $LOG; then
	rm -f start.sh.fifo.stdout start.sh.fifo.stderr start.sh.fifo.stdmix
	mkfifo start.sh.fifo.stdout start.sh.fifo.stderr start.sh.fifo.stdmix
	
	cat start.sh.fifo.stdout | tee start.sh.stdout > start.sh.fifo.stdmix &
	cat start.sh.fifo.stderr | tee start.sh.stderr > start.sh.fifo.stdmix &
	cat start.sh.fifo.stdmix > start.sh.stdmix &
	exec > start.sh.fifo.stdout 2> start.sh.fifo.stderr
fi

if ! $ONLY_DICT; then
	#=====================================================================
	# download KB?

	#=====================================================================
	# creating KB

	echo "creating KB"
	./prepare_data.sh
fi

echo
echo "= make clean ==================="
make clean
echo "================================"
echo
echo "= make ========================="
make
echo "================================"
echo

#=====================================================================
# creating automaton for NER

echo "creating CedarTree for NER"
./figa/make_automat/create_cedar.sh -c -k KBstatsMetrics.all
