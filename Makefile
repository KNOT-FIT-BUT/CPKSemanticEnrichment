.PHONY: all clean

all: ./KB-HEAD.all
	make -C ./SharedKB/var2/
	make -C ./figa/

./KB-HEAD.all: ./VERSION ./HEAD-KB ./KBstatsMetrics.all
	echo -n "VERSION=" | cat - ./VERSION ./HEAD-KB ./KBstatsMetrics.all > ./KB-HEAD.all

clean:
	rm -f ./KB-HEAD.all*
	make -C ./SharedKB/var2/ clean
	make -C ./figa/ clean
