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
 * Soubor:  KB_shm.h
 * Datum:   2013/08/29
 * Autor:   Jan Doležal, xdolez52@stud.fit.vutbr.cz
 * Projekt: Decipher - Knowledge Base daemon
 * Popis:   Program ze souboru načte matici stringů,
 *          drží ji efektivně v paměti a efektivně v ní hledá
 *          a tuto paměť sdílí read-only pro další programy.
 */
/**
 * @file	KB_shm.h
 * @date	2013/08/29
 * @author	Jan Doležal, xdolez52@stud.fit.vutbr.cz
 * @brief	Decipher - Knowledge Base daemon
 */

#ifndef KB_SHM_H
#define KB_SHM_H

#define OFFSET_GIVE(origin, pointer) ( (void *)((size_t)(pointer) - (size_t)(origin)) )
#define OFFSET_2_P(pointer, offset) ( (void *)((size_t)(pointer) + (size_t)(offset)) )

#include "global.h"

/*       _\|/_
         (o o)
 +----oOO-{_}-OOo----+
 | Globální proměnné |
 +------------------*/
extern char *KB_shm_name;
extern int KB_shm_fd;

/*       _\|/_
         (o o)
 +----oOO-{_}-OOo-----------+
 | Struktury a výčtové typy |
 +-------------------------*/
typedef unsigned short TStrLen;
typedef struct SKBStringVector KBStringVector;
typedef struct SKBString KBString;

struct SKBString {
	char *str;
	TStrLen length;
	TStrLen *offsets;
	TStrLen num_offsets;
	
	bool is_offset; /// určuje zda-li ukazatele uvnitř jsou offsety.
};

/**
 * Struktura držící vektor typu KBString
 */
struct SKBStringVector {
	KBString *array;
	
	bool is_offset; /// určuje zda-li ukazatele uvnitř jsou offsety.
	unsigned length;
	unsigned capacity;
};

/**
 * Sdílená paměť
 * Ve sdílené paměti mají všechny ukazatele funkci offsetu od začátku sdílené paměti.
 */
typedef struct {
	KBStringVector head;
	KBStringVector data;
	size_t capacity;
	unsigned version;
} KBSharedMem;

/*       _\|/_
         (o o)
 +----oOO-{_}-OOo---------------------------+
 | Následují funkce pro typ KBStringVector. |
 +-----------------------------------------*/
/**
 * Inicializuje KBStringVector \a vector.
 */
int KBStringVectorInit(KBStringVector *vector);

/**
 * "Destruktor" KBStringVectoru.
 */
void deleteKBStringVector(KBStringVector *vector);

/**
 * Vloží na konec KBStringVectoru \a vector KBString \a item.
 */
int KBStringVectorPushBack(KBStringVector *vector, KBString *item);

/**
 * Zkopíruje do nachystané sdílené paměti.
 * @param dest Adresa do sdílené paměti.
 * @param source Zdroj dat.
 * @param freespace Ukazatel na volné místo ve sdílené paměti.
 */
void KBStringVectorCopyToShm(KBStringVector *dest, KBStringVector *source, void **freespace);

/**
 * Zjistí počet celé obsazené paměti bez sizeof(KBStringVector).
 */
size_t KBStringVectorSizeOf(KBStringVector *vector);

/**
 * Vrací ukazatel na \a n prvek v poli KBStringVector \a vector.
 */
KBString * KBStringVectorAt(KBStringVector *vector, unsigned n);

/*       _\|/_
         (o o)
 +----oOO-{_}-OOo---------------------+
 | Následují funkce pro typ KBString. |
 +-----------------------------------*/
/**
 * Inicializuje KBString \a kb_str Stringem \a str.
 * Každý oddělovací znak \a delim v řetězci bude vyhledán, nahrazen znakem '\0' a za něj bude směrován offset.
 */
int KBStringInit(KBString *kb_str, String *str, char delim);

/**
 * Inicializuje prázdný KBString \a kb_str.
 */
void KBStringInitEmpty(KBString *kb_str);

/**
 * "Destruktor" KBString.
 */
void deleteKBString(KBString *kb_str);

/**
 * Zkopíruje do nachystané sdílené paměti.
 * @param dest Adresa do sdílené paměti.
 * @param source Zdroj dat.
 * @param freespace Ukazatel na volné místo ve sdílené paměti.
 */
void KBStringCopyToShm(KBString *dest, KBString *source, void **freespace);

/**
 * Zjistí počet celé obsazené paměti bez sizeof(KBString).
 */
size_t KBStringSizeOf(KBString *kb_str);

/*       _\|/_
         (o o)
 +----oOO-{_}-OOo------------------------+
 | Následují funkce pro typ KBSharedMem. |
 +--------------------------------------*/
/**
 * Inicializuje buffer pro vytvoření sdílené paměti.
 */
int KBSharedMemInit(KBSharedMem *kb);

/**
 * "Destruktor" KBSharedMem.
 */
void deleteKBSharedMem(KBSharedMem *kb);

/**
 * Zjistí počet obsazené paměti celé \a kb.
 */
size_t KBSharedMemSizeOf(KBSharedMem *kb);

/**
 * Funkce copy_KB_to_shm
 * Zkopíruje \a source do \a dest. Předpokládá se, že \a source není roven NULL.
 * @param **dest Cíl uložený ve sdílené paměti.
 * @param *source Zdroj uložený v paměti programu.
 * @return Vrací chybový kód.
 */
int copy_KB_to_shm(KBSharedMem **dest, KBSharedMem *source);

#endif
/* konec souboru KB_shm.h */
