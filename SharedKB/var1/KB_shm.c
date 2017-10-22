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
 * Soubor:  KB_shm.c
 * Datum:   2013/08/29
 * Autor:   Jan Doležal, xdolez52@stud.fit.vutbr.cz
 * Projekt: Decipher - Knowledge Base daemon
 * Popis:   Program ze souboru načte matici stringů,
 *          drží ji efektivně v paměti a efektivně v ní hledá
 *          a tuto paměť sdílí read-only pro další programy.
 */
/**
 * @file	KB_shm.c
 * @date	2013/08/29
 * @author	Jan Doležal, xdolez52@stud.fit.vutbr.cz
 * @brief	Decipher - Knowledge Base daemon
 */

// pro správu sdílené paměti
#include <sys/mman.h>
#include <sys/stat.h>        /* For mode constants */
#include <fcntl.h>           /* For O_* constants */

#include "KB_shm.h"

/*       _\|/_
         (o o)
 +----oOO-{_}-OOo-------------------------+
 | Následují funkce pro typ StringVector. |
 +---------------------------------------*/
int StringVectorInit(StringVector *vector)
{
	/* Inicializace dat */
	vector->array = NULL;
	vector->is_offset = false;
	vector->length = 0;
	vector->capacity = 32;	// Skutečná velikost pole jenž začíná 2⁵.
	
	/* Alokace prostoru */
	vector->array = malloc( (vector->capacity) * sizeof(String) );	// počáteční velikost pole
	if (vector->array == NULL) {
		perror("malloc");
		return EXIT_FAILURE;
	}
	
	/* Nulování */
	memset(vector->array, 0, (vector->capacity) * sizeof(String));
	
	return EXIT_SUCCESS;
}

void deleteStringVector(StringVector *vector)
{
	if (vector->array == NULL)
		return;
	
	for (unsigned i=0; i < vector->length; i++) {
		deleteString( &vector->array[i] );
	}
	
	FREE(vector->array);
}

int StringVectorPushBack(StringVector *vector, String *item)
{
	String *rebuf = NULL; // Proměnná pro zvětšení bufferu.
	
	if (vector->length >= vector->capacity)
	{				// Když jsme za hranicí pole je třeba...
		vector->capacity <<= 1;		// ... zvětšení velikosti bufferu na dvojnásobek.
		rebuf = realloc( vector->array, (vector->capacity) * sizeof(String) );
		if (rebuf == NULL) {	// Pokud není další místo, konec.
			perror("realloc");
			deleteStringVector(vector);
			return EXIT_FAILURE;
		}
		vector->array = rebuf;	// Předání nové adresy tabulky.
	}
	
	memcpy( OFFSET_2_P(vector->array, vector->length++ * sizeof(String)), item, sizeof(String) );
	
	return EXIT_SUCCESS;
}

void StringVectorCopyToShm(StringVector *dest, StringVector *source, void **freespace)
{
	/* Inicializace dat */
	dest->length = source->length;
	dest->capacity = source->length;
	dest->is_offset = true;
	dest->array = NULL;
	
	/* Zkopírování dat */
	dest->array = OFFSET_GIVE(dest, *freespace);
	*freespace = OFFSET_2_P( *freespace, (dest->length) * sizeof(String)); // pole předmětů
	
	// zkopírování obsahu String
	for (unsigned i=0; i < dest->length; i++) {
		StringCopyToShm( StringVectorAt(dest, i), StringVectorAt(source, i), freespace );
	}
}

size_t StringVectorSizeOf(StringVector *vector)
{
	size_t sizeOf = 0;
	
	sizeOf += (vector->length) * sizeof(String); // pole předmětů
	
	// velikost obsahu String
	for (unsigned i=0; i < vector->length; i++) {
		sizeOf += StringSizeOf( &vector->array[i] );
	}
	
	return sizeOf;
}

String * StringVectorAt(StringVector *vector, unsigned n)
{
	String *result;
	
	if (n >= vector->length)
	{
		result = NULL;
	}
	else
	{
		if (vector->is_offset)
			result = OFFSET_2_P( vector, (size_t)vector->array + (n * sizeof(String)) );
		else
			result = OFFSET_2_P(vector->array, n * sizeof(String));
	}
	
	return result;
}

/*       _\|/_
         (o o)
 +----oOO-{_}-OOo------------------------+
 | Následují funkce pro typ KBSharedMem. |
 +--------------------------------------*/
int KBSharedMemInit(KBSharedMem *kb)
{
	if ( StringVectorInit(&kb->head) )
	{
		return EXIT_FAILURE;
	}
	
	if ( StringVectorInit(&kb->data) )
	{
		deleteStringVector(&kb->head);
		return EXIT_FAILURE;
	}
	
	kb->capacity = 0;
	return EXIT_SUCCESS;
}

void deleteKBSharedMem(KBSharedMem *kb)
{
	deleteStringVector(&kb->head);
	deleteStringVector(&kb->data);
	kb->capacity = 0;
}

size_t KBSharedMemSizeOf(KBSharedMem *kb)
{
	size_t sizeOf = 0;
	
	sizeOf = sizeof(KBSharedMem);
	sizeOf += StringVectorSizeOf(&kb->head);
	sizeOf += StringVectorSizeOf(&kb->data);
	
	return sizeOf;
}

int copy_KB_to_shm(KBSharedMem **dest, KBSharedMem *source)
{
	size_t sizeOfKbShm = 0;
	void *freespace = NULL;
	
	/* Spočítání potřebné paměti */
	sizeOfKbShm = KBSharedMemSizeOf(source);
	
	/* Inicializace sdílené paměti */
	KB_shm_fd = shm_open(KB_shm_name, O_RDWR|O_CREAT, 0644);
	if (KB_shm_fd < 0)
	{
		perror("shm_open");
		return EXIT_FAILURE;
	}
	if ( ftruncate(KB_shm_fd, sizeOfKbShm) )
	{
		perror("ftruncate");
		return EXIT_FAILURE;
	}
	
	/* Připojení sdílené paměti */
	(*dest) = (KBSharedMem *) mmap(NULL, sizeOfKbShm, PROT_READ|PROT_WRITE,
								   MAP_SHARED, KB_shm_fd, 0);
    if (*dest == MAP_FAILED)
	{
		perror("mmap");
		return EXIT_FAILURE;
	}
	
	/* Inicializace dat v sdílené paměti */
	(*dest)->capacity = sizeOfKbShm;
	
	/* Kopírování dat */
	freespace = (*dest);
	freespace = OFFSET_2_P( freespace, sizeof(KBSharedMem) );
	StringVectorCopyToShm( &(*dest)->head, &source->head, &freespace );
	StringVectorCopyToShm( &(*dest)->data, &source->data, &freespace );
	
#ifdef DEBUG
	printf("sizeOfKbShm = %lu\n", sizeOfKbShm );
	printf("freespace   = %lu\n", (size_t)OFFSET_GIVE( (*dest), freespace) );
#endif
	
	return EXIT_SUCCESS;
}

/*       _\|/_
         (o o)
 +----oOO-{_}-OOo------------+
 | Následují ostatní funkce. |
 +--------------------------*/
void StringCopyToShm(String *dest, String *source, void **freespace)
{
	size_t str_size = 0;
	
	/* Inicializace dat */
	dest->length = source->length;
	dest->capacity = source->length;
	dest->str = NULL;
	
	if (source->str != NULL)
	{
		/* Zkopírování dat */
		// délka řetězce
		str_size = (dest->length + 1) * sizeof(char); // +1 pro znak '\0'
		
		dest->str = OFFSET_GIVE(dest, *freespace);
		*freespace = OFFSET_2_P( *freespace, str_size);
		
		memcpy( OFFSET_2_P( dest, dest->str ), source->str, str_size );
	}
}

/* konec souboru KB_shm.c */
