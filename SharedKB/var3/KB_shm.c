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
 +----oOO-{_}-OOo---------------------------+
 | Následují funkce pro typ KBStringVector. |
 +-----------------------------------------*/
int KBStringVectorInit(KBStringVector *vector)
{
	/* Inicializace dat */
	vector->array = NULL;
	vector->is_offset = false;
	vector->length = 0;
	vector->capacity = 32;	// Skutečná velikost pole jenž začíná 2⁵.
	
	/* Alokace prostoru */
	vector->array = malloc( (vector->capacity) * sizeof(KBString) );	// počáteční velikost pole
	if (vector->array == NULL) {
		perror("malloc");
		return EXIT_FAILURE;
	}
	
	/* Nulování */
	memset(vector->array, 0, (vector->capacity) * sizeof(KBString));
	
	return EXIT_SUCCESS;
}

void deleteKBStringVector(KBStringVector *vector)
{
	if (vector->array == NULL)
		return;
	
	for (unsigned i=0; i < vector->length; i++) {
		deleteKBString( &vector->array[i] );
	}
	
	FREE(vector->array);
}

int KBStringVectorPushBack(KBStringVector *vector, KBString *item)
{
	KBString *rebuf = NULL; // Proměnná pro zvětšení bufferu.
	
	if (vector->length >= vector->capacity)
	{				// Když jsme za hranicí pole je třeba...
		vector->capacity <<= 1;		// ... zvětšení velikosti bufferu na dvojnásobek.
		rebuf = realloc( vector->array, (vector->capacity) * sizeof(KBString) );
		if (rebuf == NULL) {	// Pokud není další místo, konec.
			perror("realloc");
			deleteKBStringVector(vector);
			return EXIT_FAILURE;
		}
		vector->array = rebuf;	// Předání nové adresy tabulky.
	}
	
	memcpy( OFFSET_2_P(vector->array, vector->length++ * sizeof(KBString)), item, sizeof(KBString) );
	
	return EXIT_SUCCESS;
}

void KBStringVectorCopyToShm(KBStringVector *dest, KBStringVector *source, void **freespace)
{
	/* Inicializace dat */
	dest->length = source->length;
	dest->capacity = source->length;
	dest->is_offset = true;
	dest->array = NULL;
	
	/* Zkopírování dat */
	dest->array = OFFSET_GIVE(dest, *freespace);
	*freespace = OFFSET_2_P( *freespace, (dest->length) * sizeof(KBString)); // pole předmětů
	
	// zkopírování obsahu KBString
	for (unsigned i=0; i < dest->length; i++) {
		KBStringCopyToShm( KBStringVectorAt(dest, i), KBStringVectorAt(source, i), freespace );
	}
}

size_t KBStringVectorSizeOf(KBStringVector *vector)
{
	size_t sizeOf = 0;
	
	sizeOf += (vector->length) * sizeof(KBString); // pole předmětů
	
	// velikost obsahu KBString
	for (unsigned i=0; i < vector->length; i++) {
		sizeOf += KBStringSizeOf( &vector->array[i] );
	}
	
	return sizeOf;
}

KBString * KBStringVectorAt(KBStringVector *vector, unsigned n)
{
	KBString *result;
	
	if (n >= vector->length)
	{
		result = NULL;
	}
	else
	{
		if (vector->is_offset)
			result = OFFSET_2_P( vector, (size_t)vector->array + (n * sizeof(KBString)) );
		else
			result = OFFSET_2_P(vector->array, n * sizeof(KBString));
	}
	
	return result;
}

/*       _\|/_
         (o o)
 +----oOO-{_}-OOo---------------------+
 | Následují funkce pro typ KBString. |
 +-----------------------------------*/
int KBStringInit(KBString *kb_str, String *string, char delim)
{
	/* Inicializace dat */
	kb_str->str = NULL;
	kb_str->length = string->length;
	kb_str->offsets = NULL;
	kb_str->num_offsets = 1;
	kb_str->is_offset = false;
	
	TStrLen capacity = 32;	// Skutečná velikost začíná 2⁵.
	
	/* Alokace prostoru */
	// Pro offsety
	kb_str->offsets = malloc( (capacity) * sizeof(TStrLen) );
	if (kb_str->offsets == NULL) {
		perror("malloc");
		return EXIT_FAILURE;
	}
	
	// Pro řetězec
	size_t str_size = (string->length + 1) * sizeof(char); // +1 pro znak '\0'
	
	kb_str->str = malloc( str_size );
	if (kb_str->str == NULL) {
		perror("malloc");
		FREE(kb_str->offsets);
		return EXIT_FAILURE;
	}
	
	/* Naplnění řetězcem */
	memcpy( kb_str->str, string->str, str_size );
	
	/* Vyhledání oddělovačů a přiřazení offsetů */
	kb_str->offsets[0] = 0;
	for (TStrLen c=0; c < kb_str->length; c++)
	{
		if (kb_str->str[c] == delim)
		{
			kb_str->str[c] = '\0';
			
			if (kb_str->num_offsets >= capacity)
			{				// Když jsme za hranicí pole je třeba...
				capacity <<= 1;		// ... zvětšení velikosti bufferu na dvojnásobek.
				void *rebuf = realloc( kb_str->offsets, (capacity) * sizeof(TStrLen) );
				if (rebuf == NULL) {	// Pokud není další místo, konec.
					perror("realloc");
					deleteKBString(kb_str);
					return EXIT_FAILURE;
				}
				kb_str->offsets = rebuf;	// Předání nové adresy tabulky.
			}
			
			kb_str->offsets[kb_str->num_offsets] = c+1;
			
			kb_str->num_offsets += 1;
		}
	}
	
	return EXIT_SUCCESS;
}

void KBStringInitEmpty(KBString *kb_str)
{
	/* Inicializace dat */
	kb_str->str = NULL;
	kb_str->length = 0;
	kb_str->offsets = NULL;
	kb_str->num_offsets = 0;
	kb_str->is_offset = false;
}

void deleteKBString(KBString *kb_str)
{
	FREE( kb_str->offsets );
	FREE( kb_str->str );
	kb_str->length = 0;
	kb_str->num_offsets = 0;
	kb_str->is_offset = false;
}

void KBStringCopyToShm(KBString *dest, KBString *source, void **freespace)
{
	size_t sizeOf = 0;
	
	/* Inicializace dat */
	dest->str = NULL;
	dest->length = source->length;
	dest->offsets = NULL;
	dest->num_offsets = source->num_offsets;
	dest->is_offset = true;
	
	if (source->str != NULL)
	{
		/* Zkopírování dat */
		// délka řetězce
		sizeOf = (dest->length + 1) * sizeof(char); // +1 pro znak '\0'
		
		dest->str = OFFSET_GIVE(dest, *freespace);
		*freespace = OFFSET_2_P( *freespace, sizeOf);
		
		memcpy( OFFSET_2_P( dest, dest->str ), source->str, sizeOf );
		
		// délka pole offsetů
		sizeOf = (dest->num_offsets) * sizeof(TStrLen);
		
		dest->offsets = OFFSET_GIVE(dest, *freespace);
		*freespace = OFFSET_2_P( *freespace, sizeOf);
		
		memcpy( OFFSET_2_P( dest, dest->offsets ), source->offsets, sizeOf );
	}
}

size_t KBStringSizeOf(KBString *kb_str)
{
	size_t sizeOf = 0;
	
	if (kb_str->str != NULL)
	{
		sizeOf += (kb_str->num_offsets) * sizeof(TStrLen); // offsety
		sizeOf += (kb_str->length + 1) * sizeof(char); // řetězec (+1 pro znak '\0')
	}
	
	return sizeOf;
}

/*       _\|/_
         (o o)
 +----oOO-{_}-OOo--------------------+
 | Následují funkce pro typ KBTable. |
 +----------------------------------*/
int KBTableInit(KBTable *table)
{
	/* Inicializace dat */
	table->array = NULL;
	table->is_offset = false;
	table->length = 0;
	table->capacity = 32;	// Skutečná velikost pole jenž začíná 2⁵.
	
	/* Alokace prostoru */
	table->array = malloc( (table->capacity) * sizeof(TKBTable_value *) );	// počáteční velikost pole
	if (table->array == NULL) {
		perror("malloc");
		return EXIT_FAILURE;
	}
	
	/* Nulování */
	memset(table->array, 0, (table->capacity) * sizeof(TKBTable_value *));
	
	return EXIT_SUCCESS;
}

void deleteKBTable(KBTable *table)
{
	if (table->array == NULL)
		return;
	
	for (unsigned i=0; i < table->length; i++) {
		FREE( table->array[i] );
	}
	
	FREE(table->array);
}

int KBTablePushBack(KBTable *table, TKBTable_value *item)
{
	TKBTable_value **rebuf = NULL; // Proměnná pro zvětšení bufferu.
	
	if (table->length >= table->capacity)
	{				// Když jsme za hranicí pole je třeba...
		table->capacity <<= 1;		// ... zvětšení velikosti bufferu na dvojnásobek.
		rebuf = realloc( table->array, (table->capacity) * sizeof(TKBTable_value *) );
		if (rebuf == NULL) {	// Pokud není další místo, konec.
			perror("realloc");
			deleteKBTable(table);
			return EXIT_FAILURE;
		}
		table->array = rebuf;	// Předání nové adresy tabulky.
	}
	
	table->array[table->length++] = item;
	
	return EXIT_SUCCESS;
}

void KBTableCopyToShm(KBTable *dest, KBTable *source, void **freespace)
{
	/* Inicializace dat */
	dest->length = source->length;
	dest->capacity = source->length;
	dest->is_offset = true;
	dest->array = NULL;
	
	/* Zkopírování dat */
	dest->array = OFFSET_GIVE(dest, *freespace);
	*freespace = OFFSET_2_P( *freespace, (dest->length) * sizeof(TKBTable_value *)); // pole předmětů
	
	// zkopírování obsahu TKBTable_value *
	for (unsigned i=0; i < source->length; i++) {
		size_t sizeOf = source->array[i][0] * sizeof(TKBTable_value);
		TKBTable_value **dest_array;
		TKBTable_value *dest_row;
		
		dest_array = KBTableAt(dest, i);
		*dest_array = OFFSET_GIVE(dest, *freespace);
		dest_row = KBTableRow(dest, i);
		*freespace = OFFSET_2_P( *freespace, sizeOf );
		
		memcpy( dest_row, source->array[i], sizeOf );
	}
}

size_t KBTableSizeOf(KBTable *table)
{
	size_t sizeOf = 0;
	
	sizeOf += (table->length) * sizeof(TKBTable_value *); // pole předmětů
	
	// velikost obsahu TKBTable_value *
	for (unsigned i=0; i < table->length; i++) {
		sizeOf += table->array[i][0] * sizeof(TKBTable_value);
	}
	
	return sizeOf;
}

TKBTable_value ** KBTableAt(KBTable *table, unsigned n)
{
	TKBTable_value **result;
	
	if (n >= table->length)
	{
		result = NULL;
	}
	else
	{
		if (table->is_offset)
			result = OFFSET_2_P( table, (size_t)table->array + (n * sizeof(TKBTable_value *)) );
		else
			result = OFFSET_2_P(table->array, n * sizeof(TKBTable_value *));
	}
	
	return result;
}

TKBTable_value * KBTableRow(KBTable *table, unsigned row)
{
	TKBTable_value *result;
	
	if (row >= table->length)
	{
		result = NULL;
	}
	else
	{
		if (table->is_offset)
			result = OFFSET_2_P( table, *KBTableAt(table, row) );
		else
			result = *KBTableAt(table, row);
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
	if ( KBStringVectorInit(&kb->head) )
	{
		return EXIT_FAILURE;
	}
	
	if ( KBStringVectorInit(&kb->data) )
	{
		deleteKBStringVector(&kb->head);
		return EXIT_FAILURE;
	}
	
	if ( KBTableInit(&kb->table) )
	{
		deleteKBStringVector(&kb->head);
		deleteKBStringVector(&kb->data);
		return EXIT_FAILURE;
	}
	
	kb->capacity = 0;
	return EXIT_SUCCESS;
}

void deleteKBSharedMem(KBSharedMem *kb)
{
	deleteKBStringVector(&kb->head);
	deleteKBStringVector(&kb->data);
	deleteKBTable(&kb->table);
	kb->capacity = 0;
}

size_t KBSharedMemSizeOf(KBSharedMem *kb)
{
	size_t sizeOf = 0;
	
	sizeOf = sizeof(KBSharedMem);
	sizeOf += KBStringVectorSizeOf(&kb->head);
	sizeOf += KBStringVectorSizeOf(&kb->data);
	sizeOf += KBTableSizeOf(&kb->table);
	
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
	KBStringVectorCopyToShm( &(*dest)->head, &source->head, &freespace );
	KBStringVectorCopyToShm( &(*dest)->data, &source->data, &freespace );
	KBTableCopyToShm( &(*dest)->table, &source->table, &freespace );
	
#ifdef DEBUG
	printf("sizeOfKbShm = %lu\n", sizeOfKbShm );
	printf("freespace   = %lu\n", (size_t)OFFSET_GIVE( (*dest), freespace) );
#endif
	
	return EXIT_SUCCESS;
}

/* konec souboru KB_shm.c */
