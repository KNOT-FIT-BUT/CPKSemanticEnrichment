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
 * Soubor:  libKB_shm.c
 * Datum:   2013/08/29
 * Autor:   Jan Doležal, xdolez52@stud.fit.vutbr.cz
 * Projekt: Decipher - Knowledge Base daemon
 * Popis:   Program ze souboru načte matici stringů,
 *          drží ji efektivně v paměti a efektivně v ní hledá
 *          a tuto paměť sdílí read-only pro další programy.
 */
/**
 * @file	libKB_shm.c
 * @date	2013/08/29
 * @author	Jan Doležal, xdolez52@stud.fit.vutbr.cz
 * @brief	Decipher - Knowledge Base daemon
 */

// pro správu sdílené paměti
#include <sys/mman.h>
#include <sys/stat.h>        /* For mode constants */
#include <fcntl.h>           /* For O_* constants */

#include "libKB_shm.h"

/*       _\|/_
         (o o)
 +----oOO-{_}-OOo----+
 | Globální proměnné |
 +------------------*/
const char *KB_shm_name = "/decipherKB-daemon_shm";

/*       _\|/_
         (o o)
 +----oOO-{_}-OOo---------------------------+
 | Následují funkce pro typ KBStringVector. |
 +-----------------------------------------*/
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

char * KBStringVectorDataAt(KBStringVector *vector, unsigned n, TStrLen col)
{
	char *result;
	KBString *string = KBStringVectorAt(vector, n);
	
	if (string == NULL)
	{
		result = NULL;
	}
	else
	{
		result = KBStringAt(string, col);
	}
	
	return result;
}

/*       _\|/_
         (o o)
 +----oOO-{_}-OOo---------------------+
 | Následují funkce pro typ KBString. |
 +-----------------------------------*/
char * KBStringAt(KBString *kb_str, TStrLen offset)
{
	char *result;
	TStrLen r_offset;
	
	if (offset >= kb_str->num_offsets)
	{
		result = NULL;
	}
	else
	{
		if (kb_str->is_offset)
		{
			r_offset = *(TStrLen *)OFFSET_2_P( kb_str, kb_str->offsets + offset );
			result = OFFSET_2_P( kb_str, kb_str->str + r_offset );
		}
		else
		{
			r_offset = kb_str->offsets[offset];
			result = (kb_str->str) + r_offset;
		}
	}
	
	return result;
}

/*       _\|/_
         (o o)
 +----oOO-{_}-OOo--------------------+
 | Následují funkce pro typ KBTable. |
 +----------------------------------*/
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
char * KBSharedMemHeadAt(KBSharedMem *kb, unsigned line, TStrLen col)
{
	return KBStringVectorDataAt(&kb->head, line-1, col-1);
}

char * KBSharedMemHeadFor(KBSharedMem *kb, char prefix, TStrLen col)
{
	return KBSharedMemHeadFor_Boost(kb, prefix, col, NULL);
}

char * KBSharedMemHeadFor_Boost(KBSharedMem *kb, char prefix, TStrLen col, unsigned *line)
{
	char *result = NULL;
	
	for (unsigned i=0; i < kb->head.length; i++)
	{
		result = KBStringVectorDataAt(&kb->head, i, 0);
		if (result[0] == prefix)
		{
			if (line != NULL)
			{
				*line = i + 1;
			}
			return KBStringVectorDataAt(&kb->head, i, col-1);
		}
	}
	
	return NULL;
}

char * KBSharedMemDataAt(KBSharedMem *kb, unsigned line, TStrLen col)
{
	return KBStringVectorDataAt(&kb->data, line-1, col-1);
}

TKBTable_value * KBSharedMemTableRowLength(KBSharedMem *kb, unsigned row)
{
	TKBTable_value *result = KBTableRow(&kb->table, row-1);
	if ( result )
		return result;
	else
		return NULL;
}

TKBTable_value * KBSharedMemTableRowColon(KBSharedMem *kb, unsigned row, unsigned n)
{
	TKBTable_value *result = KBTableRow(&kb->table, row-1);
	if (result && n > 0 && n < result[0])
		return result + n;
	else
		return NULL;
}

/*       _\|/_
         (o o)
 +----oOO-{_}-OOo------------+
 | Následují ostatní funkce. |
 +--------------------------*/
int connectKBSharedMem(KBSharedMem **dest, int *KB_shm_fd)
{
	if ( (*KB_shm_fd = connectKB_shm()) == -1 )
	{
		return EXIT_FAILURE;
	}
	
	if ( (*dest = mmapKB_shm(*KB_shm_fd)) == NULL )
	{
		disconnectKB_shm(NULL, *KB_shm_fd);
		return EXIT_FAILURE;
	}
	
	return EXIT_SUCCESS;
}

int disconnectKBSharedMem(KBSharedMem **dest, int *KB_shm_fd)
{
	int result = disconnectKB_shm(*dest, *KB_shm_fd);
	
	*dest = NULL;
	*KB_shm_fd = -1;
	
	return result;
}



int connectKB_shm(void)
{
	int KB_shm_fd;
	
	/* Inicializace sdílené paměti */
	KB_shm_fd = shm_open(KB_shm_name, O_RDONLY, 0);
	if (KB_shm_fd < 0)
	{
		perror("shm_open");
		return -1;
	}
	
	return KB_shm_fd;
}

KBSharedMem *mmapKB_shm(int KB_shm_fd)
{
	int saved_errno = errno;
	errno = 0;
	
	KBSharedMem *shared;
	struct stat buf;
	
	#define CHECK(cond) if ( cond ) { perror( #cond ); }
	
	if ( fstat(KB_shm_fd, &buf) )
	{
		perror("fstat");
		return NULL;
	}
	
	/* Připojení sdílené paměti */
	shared = (KBSharedMem *) mmap(NULL, (size_t) buf.st_size, PROT_READ,
								  MAP_SHARED, KB_shm_fd, 0);
	
    if (shared == MAP_FAILED)
	{
		perror("mmap");
		return NULL;
	}
	
	#undef CHECK
	
	if (errno != 0) {
		return NULL;
	}
	errno = saved_errno;
	return shared;
}

int disconnectKB_shm(KBSharedMem *dest, int KB_shm_fd)
{
	int saved_errno = errno;
	errno = 0;
	
	struct stat buf;
	int status_fstat = 0;
	
	#define CHECK(cond) if ( cond ) { perror( #cond ); }
	
	CHECK( (status_fstat = fstat(KB_shm_fd, &buf)) != 0 );
	
	if (KB_shm_fd >= 0)
	{
		CHECK( close(KB_shm_fd) == -1 );
		if (dest != NULL && status_fstat == 0)
		{
			CHECK( munmap(dest, (size_t) buf.st_size) );
		}
	}
	
	#undef CHECK
	
	if (errno != 0) {
		return EXIT_FAILURE;
	}
	errno = saved_errno;
	return EXIT_SUCCESS;
}

/* konec souboru libKB_shm.c */
