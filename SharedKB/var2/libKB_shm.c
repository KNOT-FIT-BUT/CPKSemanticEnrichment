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

#include "global.h"
#include "libKB_shm.h"

/*       _\|/_
         (o o)
 +----oOO-{_}-OOo----+
 | Globální proměnné |
 +------------------*/
char *KB_shm_name = "/decipherKB-daemon_shm";

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

unsigned KBSharedMemVersion(KBSharedMem *kb)
{
	return kb->version;
}

/*       _\|/_
         (o o)
 +----oOO-{_}-OOo------------+
 | Následují ostatní funkce. |
 +--------------------------*/
int connectKBSharedMem(KBSharedMem **dest, int *KB_shm_fd, char *kb_shm_name)
{
	if ( (*KB_shm_fd = connectKB_shm(kb_shm_name)) == -1 )
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



int checkKB_shm(char *kb_shm_name)
{
	int KB_shm_fd;

	if (kb_shm_name == NULL) {
		kb_shm_name = KB_shm_name;
	}

	KB_shm_fd = shm_open(kb_shm_name, O_RDONLY, 0);
	if (KB_shm_fd < 0 || close(KB_shm_fd) == -1) {
		return EXIT_FAILURE;
	} else {
		return EXIT_SUCCESS;
	}
}

int connectKB_shm(char *kb_shm_name)
{
	int KB_shm_fd;

	if (kb_shm_name == NULL) {
		kb_shm_name = KB_shm_name;
	}
	
	/* Inicializace sdílené paměti */
	KB_shm_fd = shm_open(kb_shm_name, O_RDONLY, 0);
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
	
	KBSharedMem *shared = NULL;
	struct stat buf;
	
	#define CHECK_M_FREE() \
	{ \
		if (shared != NULL && shared != MAP_FAILED) \
		{ \
			munmap(shared, (size_t) buf.st_size ); \
		} \
	}
	
	#define CHECK(cond) \
	if ( cond ) \
	{ \
		perror( #cond ); \
		CHECK_M_FREE(); \
		return EXIT_FAILURE; \
	}
	
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
		CHECK_M_FREE();
		return NULL;
	}
	
	if (errno != 0) {
		CHECK_M_FREE();
		return NULL;
	}
	
	#undef CHECK
	#undef CHECK_M_FREE
	
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


int getVersionFromSrc(char *KB_path)
{
	char *FILENAME = KB_path;
	int last_letter = 0;  // Poslední načtené písmeno z fce read_line() pro zjištění konce souboru.
	FILE *infile = NULL;
	String str_buf;
	const char *VERSION_PREFIX = "VERSION=";
	const size_t VERSION_PREFIX_LEN = strlen(VERSION_PREFIX);
	const int FAIL = -1;
	unsigned int version;
	
	int saved_errno = errno;
	errno = 0;
	
	/* Otevření souboru pro čtení */
	infile = open_file_to_read(FILENAME);
	if (infile == NULL) {
		perror("open");
		return EXIT_FAILURE;
	}
	
	/* Inicializace */
	StringInitEmpty( &str_buf );
	
	#define CHECK_M_FREE() \
	{ \
		deleteString( &str_buf ); \
		close_file(FILENAME, infile); \
	}
	
	#define CHECK(cond) \
	if ( cond ) \
	{ \
		perror( #cond ); \
		CHECK_M_FREE(); \
		return FAIL; \
	}
	
	/* Načtení verze */
	if (last_letter != EOF) {
		// Zde probíhá alokace, která bude uvolňena při chybě, nebo na konci funkce.
		CHECK( read_line( &str_buf, infile, &last_letter ) );
		
		if (strncmp(VERSION_PREFIX, str_buf.str, VERSION_PREFIX_LEN) == 0) {
			CHECK( get_num_arg(str_buf.str + VERSION_PREFIX_LEN, &version) );
			deleteString( &str_buf );
		}
	}
	
	#undef CHECK
	#undef CHECK_M_FREE
	
	/* Uzavření souboru */
	if ( close_file(FILENAME, infile) == EXIT_FAILURE )
	{
		perror("close_file");
		return FAIL;
	}
	
	errno = saved_errno;
	return (int) version;
}

int getVersionFromBin(char *KB_bin_path)
{
	int KB_bin_fd = -1;
	KBSharedMem *KB_bin = NULL;
	const int FAIL = -1;
	unsigned int version;
	
	int saved_errno = errno;
	errno = 0;
	
	#define CHECK_M_FREE() \
	{ \
		if (KB_bin_fd != -1) \
		{ \
			close(KB_bin_fd); \
		} \
	}
	
	#define CHECK(cond) \
	if ( cond ) \
	{ \
		perror( #cond ); \
		CHECK_M_FREE(); \
		return FAIL; \
	}
	
	/* Připojení binárního souboru */
	CHECK( (KB_bin_fd = open(KB_bin_path, O_RDONLY)) == -1 );
	CHECK( (KB_bin = mmapKB_shm(KB_bin_fd)) == NULL );
	version = KBSharedMemVersion(KB_bin);
	CHECK( disconnectKB_shm(KB_bin, KB_bin_fd) );
	
	#undef CHECK
	#undef CHECK_M_FREE
	
	errno = saved_errno;
	return (int) version;
}

/* konec souboru libKB_shm.c */
