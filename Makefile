.PHONY: all clean

all:
	make -C ./SharedKB/var2/
	make -C ./figa/

clean:
	make -C ./SharedKB/var2/ clean
	make -C ./figa/ clean
