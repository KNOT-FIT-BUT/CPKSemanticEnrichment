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
extern const char *KB_shm_name;
extern int KB_shm_fd;

/*       _\|/_
         (o o)
 +----oOO-{_}-OOo-----------+
 | Struktury a výčtové typy |
 +-------------------------*/
typedef struct SStringVector StringVector;

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
 * Inicializuje StringVector \a vector.
 */
int StringVectorInit(StringVector *vector);

/**
 * "Destruktor" StringVectoru.
 */
void deleteStringVector(StringVector *vector);

/**
 * Vloží na konec StringVectoru \a vector String \a item.
 */
int StringVectorPushBack(StringVector *vector, String *item);

/**
 * Zkopíruje do nachystané sdílené paměti.
 * @param dest Adresa do sdílené paměti.
 * @param source Zdroj dat.
 * @param freespace Ukazatel na volné místo ve sdílené paměti.
 */
void StringVectorCopyToShm(StringVector *dest, StringVector *source, void **freespace);

/**
 * Zjistí počet celé obsazené paměti bez sizeof(StringVector).
 */
size_t StringVectorSizeOf(StringVector *vector);

/**
 * Vrací ukazatel na \a n prvek v poli StringVector \a vector.
 */
String * StringVectorAt(StringVector *vector, unsigned n);

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

/*       _\|/_
         (o o)
 +----oOO-{_}-OOo------------+
 | Následují ostatní funkce. |
 +--------------------------*/
/**
 * Zkopíruje do nachystané sdílené paměti.
 * @param dest Adresa do sdílené paměti.
 * @param source Zdroj dat.
 * @param freespace Ukazatel na volné místo ve sdílené paměti.
 */
void StringCopyToShm(String *dest, String *source, void **freespace);

#endif
/* konec souboru KB_shm.h */
