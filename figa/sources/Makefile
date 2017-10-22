UNAME := $(shell uname -m)

ifeq ($(UNAME), x86_64)
  SWIG_F=
  GPP_F=-m64
else
  SWIG_F=-classic
  GPP_F=
endif

CFLAGS=-g -ftree-vectorize -fPIC -DFLEXIBLE -DSTOPBIT -DNEXTBIT -std=c++11
#OBJ=figa.o common.o nstr.o spell.o one_word_io.o figa_cedar.o
OBJ=figa_cedar.o
HEAD=figa_cedar.h figa_cedar.tpp figa.h cedar.h darts.h
program=../figav1.0
.PHONY: build figa nstr

build: $(program) $(OBJ) _marker.so kb_loader.so

$(program): main.o $(OBJ)
	g++ -g -std=c++11 main.o $(OBJ) -o $(program)
main.o: main.cpp $(HEAD)
	g++ -g -std=c++11 -c main.cpp
figa_cedar.o: figa_cedar.cpp $(HEAD)
	g++ -c figa_cedar.cpp $(CFLAGS)
nstr.o: nstr.cc nstr.h $(HEAD)
	g++ -c nstr.cc  $(CFLAGS)
#figa.o: figa.cc $(HEAD)
#	g++ -c figa.cc $(CFLAGS)
common.o: common.cc common.h $(HEAD)
	g++ -c common.cc $(CFLAGS)
spell.o: spell.cc spell.h $(HEAD)
	g++ -c spell.cc $(CFLAGS)
one_word_io.o: one_word_io.cc $(HEAD)
	g++ -c one_word_io.cc $(CFLAGS)
figa.o: figa.cpp $(HEAD)
	g++ -c figa.cpp $(CFLAGS)
#build: main.cpp
#	g++ -std=c++11 -c main.cpp `python3.4m-config --cflags` 
#	g++ main.o nstr.o figa.o -o main `python3.4m-config --ldflags` 

_marker.so: figa_cedar.o figa.o
	swig -c++ -python $(SWIG_F) -o marker_wrap.cc marker.i
	$(CXX) -fPIC -c marker_wrap.cc $$(python-config --includes) $(CFLAGS)
	$(CXX) $(GPP_F) -shared figa_cedar.o figa.o marker_wrap.o -o _marker.so $(CFLAGS)

# fast uklada entity na radky | slow po jednotlivych prvcich entity
# -> pristup pouze k entite   | -> pristup k entite a jeho prvkum
# mem: 90 MB RAM              | mem: 317 MB RAM 

kb_loader.so: kb_loader_slow

kb_loader_slow: kb_loader_slow.o
	g++ -shared -Wl,-soname,kb_loader.so -o kb_loader.so kb_loader_slow.o
	touch kb_loader_slow

kb_loader_fast: kb_loader_fast.o
	g++ -shared -Wl,-soname,kb_loader.so -o kb_loader.so kb_loader_fast.o
	touch kb_loader_fast

kb_loader_slow.o: kb_loader_slow.cc
	g++ -c -fPIC kb_loader_slow.cc -o kb_loader_slow.o

kb_loader_fast.o: kb_loader_fast.cc
	g++ -c -fPIC kb_loader_fast.cc -o kb_loader_fast.o

clean: 
	rm -f *.o *.pyc
	rm -f *.so $(program)
	rm -f kb_loader_slow kb_loader_fast

# EOF
