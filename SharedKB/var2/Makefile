# -*- coding: utf-8 -*-
#
# Makefile pro projekt Decipher - Knowledge Base daemon
#

# Jméno přeloženého programu
program=decipherKB-daemon

# Seznam objektových souborů.
OBJ=main.o global.o KB_shm.o
SRC=main.c global.c KB_shm.c
HEAD=global.h KB_shm.h ecodes.h
OTHER=Makefile

# Překladač C
CC=gcc

# Link
LINK=-lrt

# Makra
# MACROS=-D_XOPEN_SOURCE -D_XOPEN_SOURCE_EXTENDED
MACROS=-DSPACE_EN -DCOPY_TO_DISC_EN

# Nepovinné parametry překladače
BRUTAL=-Werror
CFLAGS=-std=gnu99 -Wall -Wextra $(BRUTAL) -pedantic $(LDB) $(MACROS)

.PHONY: build clean pack pack_nocz test speedtest valgrind kdbg debug lib reader_kdbg

# Zkompiluje program (výchozí)
build: $(program) lib

# Smaže všechny soubory co nemají být odevzdány
clean:
	rm -f *.o $(program) libKB_shm.so

# Zabalí program
pack:
	zip xdolez52.zip $(SRC) $(HEAD) $(OTHER)

pack_nocz:
	mkdir -p ./pack/
	cp $(SRC) $(HEAD) $(OTHER) ./pack/
	bash -c 'cd pack; for file in $(SRC); do /opt/odcesti.sh $$file; done'
	bash -c 'cd pack; for file in $(HEAD); do /opt/odcesti.sh $$file; done'
	bash -c 'cd pack; for file in $(OTHER); do /opt/odcesti.sh $$file; done'
	cd pack; zip ../xdolez52.zip $(SRC) $(HEAD) $(OTHER)

# Spustí testy
test: $(program)
	./$(program) $(ARG1)

# make speedtest ARG1=../../KB-HEAD.all 2>&1 | sed -rn 's/^real.*m(.*)s.*/\1/p'
speedtest:
	make -B "LDB=-DSPEEDTEST"
	bash -c "time ./$(program) -s SharedKB-speedtest $(ARG1)"

valgrind:
	make debug
	valgrind --tool=memcheck --leak-check=yes --show-reachable=yes ./$(program) $(ARG1)

kdbg:
	mkdir -p '/tmp/Decipher'; cp * '/tmp/Decipher'; cd '/tmp/Decipher'; make debug; kdbg ./$(program)

# Zkompiluje program s debugovacími informacemi
debug:
	make -B "LDB=-g3 -DDEBUG"

# Kompilace dynamické knihovny
lib: libKB_shm.so

libKB_shm.so: libKB_shm.c libKB_shm.h global.c global.h
# 	$(CC) -shared -fPIC libKB_shm.c -o libKB_shm.so
	$(CC) -shared -fPIC -std=gnu99 -Wall -Wextra $(BRUTAL) -pedantic libKB_shm.c global.c -o libKB_shm.so $(LINK)

# program pro ladění dynamické knihovny
reader_kdbg:
	mkdir -p '/tmp/Decipher'; cp * '/tmp/Decipher'; cd '/tmp/Decipher'; make reader -B "LDB=-g3 -DDEBUG"; kdbg ./reader

reader: libKB_shm.c libKB_shm.h global.c global.h reader.c
	$(CC) $(CFLAGS) reader.c libKB_shm.c global.c -o reader $(LINK)

reader_lib: lib reader.c
	$(CC) $(CFLAGS) reader.c -o reader -L. -lKB_shm $(LINK)

# Kompilace démonu
$(program): $(OBJ)
	$(CC) $(CFLAGS) $(OBJ) -o $(program) $(LINK)

$(OBJ): $(HEAD)
