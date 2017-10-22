# -*- coding: utf-8 -*-

CXX=g++
CFLAGS=-g

.PHONY: all clean

all: utf2symbols utf8_valid

utf2symbols: utf2symbols.cc
	$(CXX) $(CFLAGS) utf2symbols.cc -o utf2symbols

utf8_valid: utf8_valid.cc
	$(CXX) $(CFLAGS) utf8_valid.cc -o utf8_valid

clean:
	rm -f utf2symbols
	rm -f utf8_valid

# EOF
