/* -*- coding: utf-8 -*- */
/*
Copyright 2014 Brno University of Technology

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/
/*
 * Soubor:  libKB_shm.h
 * Datum:   2013/08/29
 * Autor:   Jan Doležal, xdolez52@stud.fit.vutbr.cz
 * Projekt: Decipher - Knowledge Base daemon
 * Popis:   Program ze souboru načte matici stringů,
 *          drží ji efektivně v paměti a efektivně v ní hledá
 *          a tuto paměť sdílí read-only pro další programy.
 */
/**
 * @file	libKB_shm.h
 * @date	2013/08/29
 * @author	Jan Doležal, xdolez52@stud.fit.vutbr.cz
 * @brief	Decipher - Knowledge Base daemon
 */

#ifndef KB_SHM_H
#define KB_SHM_H

// práce se vstupem/výstupem
#include <stdio.h>

// obecné funkce jazyka C
#include <stdlib.h>
#include <stdbool.h>

// kvůli funkci strtoul a dalších
#include <string.h>

// ošetření přetečení
#include <limits.h>

// proměnná errno
#include <errno.h>
#include <assert.h>

// často potřebný hlavičkový soubor
#include <unistd.h>

/*       _\|/_
         (o o)
 +----oOO-{_}-OOo----+
 | Makra             |
 +------------------*/
#define FREE(pointer) { free(pointer); pointer = NULL; }

#define ERROR(message) \
  fprintf(stderr,"%s (%s:%s:%d)\n",(message),__FILE__,__FUNCTION__,__LINE__)

#define OFFSET_GIVE(origin, pointer) ( (void *)((size_t)(pointer) - (size_t)(origin)) )
#define OFFSET_2_P(pointer, offset) ( (void *)((size_t)(pointer) + (size_t)(offset)) )

/*       _\|/_
         (o o)
 +----oOO-{_}-OOo----+
 | Globální proměnné |
 +------------------*/
extern const char *KB_shm_name;

/*       _\|/_
         (o o)
 +----oOO-{_}-OOo-----------+
 | Struktury a výčtové typy |
 +-------------------------*/
typedef struct SStringVector StringVector;

/**
 * Řetězec
 */
typedef struct {
	char *str;
	unsigned length;
	unsigned capacity;
} String;

/**
 * Struktura držící vektor typu String
 */
struct SStringVector {
	String *array;
	
	bool is_offset; /// určuje zda-li ukazatele uvnitř jsou offsety.
	unsigned length;
	unsigned capacity;
};

/**
 * Sdílená paměť
 * Ve sdílené paměti mají všechny ukazatele funkci offsetu od začátku sdílené paměti.
 */
typedef struct {
	StringVector head;
	StringVector data;
	size_t capacity;
} KBSharedMem;

/*       _\|/_
         (o o)
 +----oOO-{_}-OOo-------------------------+
 | Následují funkce pro typ StringVector. |
 +---------------------------------------*/
/**
 * Vrací ukazatel na \a n prvek v poli StringVector \a vector.
 */
String * StringVectorAt(StringVector *vector, unsigned n);

/**
 * Vrací ukazatel na \a n prvek v poli StringVector \a vector.
 */
char * StringVectorDataAt(StringVector *vector, unsigned n);

/*       _\|/_
         (o o)
 +----oOO-{_}-OOo------------------------+
 | Následují funkce pro typ KBSharedMem. |
 +--------------------------------------*/
/**
 * Číslování řádků od 1.
 * Vrací hlavičku na řádku \a line.
 */
char * KBSharedMemHeadAt(KBSharedMem *kb, unsigned line);

/**
 * Vrací hlavičku podle prefixu \a prefix.
 */
char * KBSharedMemHeadFor(KBSharedMem *kb, char prefix);

/**
 * Pokud je parametr \a line != NULL, zapíše se do něj řádek, na kterém se nachází onen prefix.
 * Vrací hlavičku podle prefixu \a prefix.
 */
char * KBSharedMemHeadFor_Boost(KBSharedMem *kb, char prefix, unsigned *line);

/**
 * Číslování řádků od 1.
 * Vrací data na řádku \a line.
 */
char * KBSharedMemDataAt(KBSharedMem *kb, unsigned line);

/*       _\|/_
         (o o)
 +----oOO-{_}-OOo------------+
 | Následují ostatní funkce. |
 +--------------------------*/

// Pro jazyky C/C++
/**
 * Připojí sdílenou paměť READ_ONLY do \a dest a do \a KB_shm_fd uloží file descriptor.
 * @return Pokud vše proběhlo v pořádku vrací 0, jinak číslo != 0.
 */
int connectKBSharedMem(KBSharedMem **dest, int *KB_shm_fd);

/**
 * Odpojí (odmapuje) sdílenou paměť na \a dest, zavře file descriptor \a KB_shm_fd.
 * Po odpojení \a dest = NULL a \a KB_shm_fd = -1.
 * @return Pokud vše proběhlo v pořádku vrací 0, jinak číslo != 0.
 */
int disconnectKBSharedMem(KBSharedMem **dest, int *KB_shm_fd);

// Pro jazyky Java, Python, ...
/**
 * Připojí sdílenou paměť READ_ONLY.
 * @return Pokud vše proběhlo v pořádku vrací nezáporný file descriptor, při chybě vrací -1.
 */
int connectKB_shm(void);

/**
 * Namapuje sdílenou paměť READ_ONLY.
 * @return Pokud vše proběhlo v pořádku vrací ukazatel do namapované paměti, při chybě vrací NULL.
 */
KBSharedMem *mmapKB_shm(int KB_shm_fd);

/**
 * Odpojí (odmapuje) sdílenou paměť na \a dest a zavře file descriptor \a KB_shm_fd.
 * Parametr \a dest může být NULL.
 * @return Pokud vše proběhlo v pořádku vrací 0, jinak číslo != 0.
 */
int disconnectKB_shm(KBSharedMem *dest, int KB_shm_fd);

#endif
/* konec souboru libKB_shm.h */
