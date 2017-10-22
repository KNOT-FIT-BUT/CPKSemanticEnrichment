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
 * Soubor:  main.c
 * Datum:   2013/08/29
 * Autor:   Jan Doležal, xdolez52@stud.fit.vutbr.cz
 * Projekt: Decipher - Knowledge Base daemon
 * Popis:   Program ze souboru načte matici stringů,
 *          drží ji efektivně v paměti a efektivně v ní hledá
 *          a tuto paměť sdílí read-only pro další programy.
 */
/**
 * @file	main.c
 * @date	2013/08/29
 * @author	Jan Doležal, xdolez52@stud.fit.vutbr.cz
 * @brief	Decipher - Knowledge Base daemon
 */

// pro správu sdílené paměti
#include <sys/mman.h>
#include <sys/stat.h>        /* For mode constants */
#include <fcntl.h>           /* For O_* constants */

// Argumenty programu
#include <unistd.h>

// Signály
#include <signal.h>

// Často potřebné hlavičky
#include "global.h"

// Struktura sdílené paměti
#include "KB_shm.h"

/*       _\|/_
         (o o)
 +----oOO-{_}-OOo----+
 | Globální proměnné |
 +------------------*/
char *KB_shm_name = "/decipherKB-daemon_shm";
int KB_shm_fd = -1;

/*       _\|/_
         (o o)
 +----oOO-{_}-OOo------------+
 | Hlavičky některých funkcí |
 +--------------------------*/
void wait_to_sig(sigset_t *s_mask);


/*       _\|/_
		 (o o)
 +----oOO-{_}-OOo----+
 | Struktury         |
 +------------------*/
struct SParseArgs {
	char *optarg;
	int optind;
	int opterr;
	int optopt;
};

struct SArguments {
	char *shm_name;
	char *bin_kb_path;
};

/*       _\|/_
         (o o)
 +----oOO-{_}-OOo----+
 | Funkce            |
 +------------------*/
/**
 * Uvolní všechny prostředky.
 */
int free_all()
{
	#define CHECK(cond) if ( cond ) { perror( #cond ); }
	
	int ret;

	if (KB_shm_fd >= 0) {
		CHECK( (ret = close(KB_shm_fd)) == -1 );
		CHECK( shm_unlink(KB_shm_name) == -1 );

		if (ret == 0) {
			KB_shm_fd = -1;
		}
	}
	
	if (errno != 0) {
		return EXIT_FAILURE;
	}
	return EXIT_SUCCESS;
	
	#undef CHECK
}

/**
 * Ukončí proces při chybě nebo signálu.
 */
void terminate(int sig)
{
	if (false)
		fprintf(stderr, "%d: %d\n", getpid(), sig);
	free_all();
	exit(2);
}

/**
 * Probudí proces po signálu.
 */
void sig_wake(int sig)
{
	if (false)
		fprintf(stderr, "%d: %d\n", getpid(), sig);
}

/**
 * Zkontroluje globální proměnnou errno. Pokud bude různá od nuly
 * uvolní všechny prostředky a ukončí proces.
 */
void check_errno(const char *str)
{
	// Pokud nedošlo k chybě nebudeme nic uvolňovat.
	if (errno == 0) {return;}
	
	// Pokud došlo k chybě, uvolníme všechny prostředky.
	perror(str);
	terminate(SIGTERM);
}

/**
 * Alokuje sdílenou paměť a naplní ji hodnotami.
 * @param KB_shm Ukazatel na sdílenou paměť.
 * @param KB_path Cesta ke znalostní bázi.
 */
int init_shm(KBSharedMem **KB_shm, char *KB_path)
{
	char *FILENAME = KB_path;
	int last_letter = 0;  // Poslední načtené písmeno z fce read_line() pro zjištění konce souboru.
	KBSharedMem KB_buf;   // Buffer pro KB.
	FILE *infile = NULL;
	String str_buf;
	KBString kb_str_buf;
	bool version_before = false;
	const char *VERSION_PREFIX = "VERSION=";
	const size_t VERSION_PREFIX_LEN = strlen(VERSION_PREFIX);
	
	/* Otevření souboru pro čtení */
	infile = open_file_to_read(FILENAME);
	if (infile == NULL) {
		perror("open");
		return EXIT_FAILURE;
	}
	
	/* Inicializace dat pro sdílenou paměť */
	StringInitEmpty( &str_buf );
	KBStringInitEmpty( &kb_str_buf );
	
	if ( KBSharedMemInit(&KB_buf) ) {
		perror("KBSharedMemInit");
		close_file(FILENAME, infile);
		return EXIT_FAILURE;
	}
	
	#define CHECK_M_FREE() \
	{ \
		deleteString( &str_buf ); \
		deleteKBString(&kb_str_buf); \
		deleteKBSharedMem(&KB_buf); \
		close_file(FILENAME, infile); \
	}
	
	#define CHECK(cond) \
	if ( cond ) \
	{ \
		perror( #cond ); \
		CHECK_M_FREE(); \
		return EXIT_FAILURE; \
	}
	
	/* Načtení verze */
	if (last_letter != EOF) {
		// Zde probíhá alokace, která bude uvolňena při chybě, nebo na konci funkce.
		CHECK( read_line( &str_buf, infile, &last_letter ) );
		
		if (strncmp(VERSION_PREFIX, str_buf.str, VERSION_PREFIX_LEN) == 0) {
			CHECK( get_num_arg(str_buf.str + VERSION_PREFIX_LEN, &KB_buf.version) );
			deleteString( &str_buf );
			CHECK( read_line( &str_buf, infile, &last_letter ) );
		}
		
		version_before = true; // Slouží jako informace, že již máme připraven další řádek v "str_buf" a tedy musíme jej zpracovat abychom mohli načítat další.
	}
	
	/* Načítání hlavičky */
	while (last_letter != EOF)
	{
		// Zde probíhá alokace, která bude uvolňena při chybě, nebo na konci funkce.
		if (version_before) {
			version_before = false;
		} else {
			CHECK( read_line( &str_buf, infile, &last_letter ) );
		}
		
		if (str_buf.str != NULL && str_buf.length == 0)
		{
			deleteString( &str_buf );
			break;
		}
		
		CHECK( KBStringInit( &kb_str_buf, &str_buf, '\t' ) );
		CHECK( KBStringVectorPushBack( &KB_buf.head, &kb_str_buf ) );
		
		// Vyprázdní se buffery
		deleteString( &str_buf );
		KBStringInitEmpty( &kb_str_buf );
	}
	
	if (last_letter == EOF)
	{
		ERROR("Early End Of File!");
		if (errno == 0) {errno = EINVAL;}
		CHECK_M_FREE();
		return EXIT_FAILURE;
	}
	
	/* Načítání dat */
	while (last_letter != EOF)
	{
		// Zde probíhá alokace, která bude uvolňena při chybě, nebo na konci funkce.
		CHECK( read_line( &str_buf, infile, &last_letter ) );
		
		if (str_buf.str != NULL && str_buf.length == 0)
		{
			if (last_letter != EOF)
			{ // Nalezena mezera při načítání dat!
// 				ERROR("Nalezena mezera pri nacitani dat!");
				deleteString( &str_buf );
#ifdef SPACE_EN
				KBStringInitEmpty( &kb_str_buf );
				CHECK( KBStringVectorPushBack( &KB_buf.data, &kb_str_buf ) );
#endif
			}
			else
			{
				deleteString( &str_buf );
			}
			
			continue;
		}
		
		CHECK( KBStringInit( &kb_str_buf, &str_buf, '\t' ) );
		CHECK( KBStringVectorPushBack( &KB_buf.data, &kb_str_buf ) );
		
		// Vyprázdní se buffery
		deleteString( &str_buf );
		KBStringInitEmpty( &kb_str_buf );
	}
	
	#undef CHECK
	#undef CHECK_M_FREE
	
	/* Uzavření souboru */
	if ( close_file(FILENAME, infile) == EXIT_FAILURE )
	{
		perror("close_file");
		deleteKBSharedMem(&KB_buf);
		return EXIT_FAILURE;
	}
	
	/* Zkopírování bufferu do sdílené paměti. */
	if ( copy_KB_to_shm(KB_shm, &KB_buf) == EXIT_FAILURE )
	{
		deleteKBSharedMem(&KB_buf);
		free_all();
		return EXIT_FAILURE;
	}
	
	/* Uvolnění bufferu KB. */
	deleteKBSharedMem(&KB_buf);
	if (errno)
	{
		perror("deleteKBSharedMem");
		free_all();
		return EXIT_FAILURE;
	}
	
	return EXIT_SUCCESS;
}

/**
 * Alokuje sdílenou paměť ze souboru.
 * @param KB_shm Ukazatel na sdílenou paměť.
 * @param KB_bin_path Cesta k binárnímu souboru znalostní báze.
 */
int init_shm_from_bin(KBSharedMem **KB_shm, char *KB_bin_path)
{
	int KB_bin_fd = -1;
	struct stat KB_bin_stat;
	KBSharedMem *KB_bin = NULL;
	
	#define CHECK_M_FREE() \
	{ \
		if (KB_bin_fd != -1) \
		{ \
			close(KB_bin_fd); \
		} \
		if (KB_bin != NULL && KB_bin != MAP_FAILED) \
		{ \
			munmap(KB_bin, KB_bin->capacity ); \
		} \
		free_all(); \
	}
	
	#define CHECK(cond) \
	if ( cond ) \
	{ \
		perror( #cond ); \
		CHECK_M_FREE(); \
		return EXIT_FAILURE; \
	}
	
	/* Připojení binárního souboru */
	CHECK( (KB_bin_fd = open(KB_bin_path, O_RDONLY)) == -1 );
	CHECK( fstat(KB_bin_fd, &KB_bin_stat) );
	
	KB_bin = (KBSharedMem *) mmap(NULL, (size_t) KB_bin_stat.st_size, PROT_READ,
								  MAP_SHARED, KB_bin_fd, 0);
	if (KB_bin == MAP_FAILED)
	{
		perror("mmap");
		CHECK_M_FREE();
		if (KB_bin_stat.st_size == 0) {
			unlink(KB_bin_path);
			ERROR("Empty source binary file.\nDeleting...\nPlease, try again.");
		}
		return EXIT_FAILURE;
	}
	
	/* Inicializace sdílené paměti */
	KB_shm_fd = shm_open(KB_shm_name, O_RDWR|O_CREAT, 0644);
	if (KB_shm_fd < 0)
	{
		perror("shm_open");
		CHECK_M_FREE();
		return EXIT_FAILURE;
	}
	CHECK( ftruncate(KB_shm_fd, KB_bin->capacity) );
	CHECK( fzeroing(KB_shm_fd, KB_bin->capacity) == -1 );
	
	/* Připojení sdílené paměti */
	(*KB_shm) = (KBSharedMem *) mmap(NULL, KB_bin->capacity, PROT_READ|PROT_WRITE,
									 MAP_SHARED, KB_shm_fd, 0);
	if (*KB_shm == MAP_FAILED)
	{
		perror("mmap");
		CHECK_M_FREE();
		return EXIT_FAILURE;
	}
	
	/* Kopírování dat */
	memcpy( *KB_shm, KB_bin, KB_bin->capacity );
	
	CHECK( munmap(KB_bin, KB_bin->capacity ) );
	CHECK( close(KB_bin_fd) == -1 );
	
	#undef CHECK
	#undef CHECK_M_FREE
	
	return EXIT_SUCCESS;
}

/**
 * Alokuje sdílenou paměť ze souboru.
 * @param KB_shm Ukazatel na sdílenou paměť.
 * @param KB_path Cesta ke znalostní bázi.
 */
int initKBShm(KBSharedMem **KB_shm, char *KB_path)
{
#ifndef COPY_TO_DISC_EN
	return init_shm(KB_shm, KB_path);
#else
	const char *KB_bin_suffix = ".bin";
	const size_t KB_path_len = strlen(KB_path);
	const size_t KB_bin_suffix_len = strlen(KB_bin_suffix);
	
	int old_errno = 0;
	bool KB_bin_exist = false;
	bool KB_bin_ok = false;
	int KB_bin_fd = -1;
	struct stat KB_stat;
	struct stat KB_bin_stat;
	char *KB_bin_path = NULL;
	KBSharedMem *KB_bin = NULL;
	
	/* Vytvoření cesty k binárnímu souboru. */
	KB_bin_path = malloc( (KB_path_len + KB_bin_suffix_len +1) * sizeof(char) ); // +1 pro znak '\0'
	if (KB_bin_path == NULL)
	{
		perror("malloc");
		return EXIT_FAILURE;
	}
	
	strcpy(KB_bin_path, KB_path);
	strcpy(KB_bin_path + KB_path_len, KB_bin_suffix);
	
	#define CHECK_M_FREE() \
	{ \
		FREE( KB_bin_path ); \
	}
	
	#define CHECK(cond) \
	if ( cond ) \
	{ \
		perror( #cond ); \
		CHECK_M_FREE(); \
		return EXIT_FAILURE; \
	}
	
	/* Ověření zda-li binární soubor existuje */
	old_errno = errno;
	if ( access(KB_bin_path, F_OK) == 0 )
	{
		CHECK( access(KB_bin_path, R_OK|W_OK) );
		
		KB_bin_exist = true;
	}
	errno = old_errno;
	
	/* Ověření zda-li binární soubor má větší mtime než textový soubor */
	if (KB_bin_exist)
	{
		CHECK( stat(KB_bin_path, &KB_bin_stat) );
		CHECK( stat(KB_path, &KB_stat) );
		
		if (KB_bin_stat.st_mtime > KB_stat.st_mtime)
		{
			KB_bin_ok = true;
		}
	}
	
	if (KB_bin_ok)
	{
		/* Binární soubor je stále aktuální */
		CHECK( init_shm_from_bin(KB_shm, KB_bin_path) );
		FREE( KB_bin_path );
		return EXIT_SUCCESS;
	}
	
	/* Otevření/Vytovoření binárního souboru */
	CHECK( (KB_bin_fd = open(KB_bin_path, O_RDWR|O_CREAT, 0640)) == -1 );

	#undef CHECK
	#undef CHECK_M_FREE
	
	#define CHECK_M_FREE() \
	{ \
		free_all(); \
		close(KB_bin_fd); \
		unlink(KB_bin_path); \
		FREE(KB_bin_path); \
	}
	
	#define CHECK(cond) \
	if ( cond ) \
	{ \
		perror( #cond ); \
		CHECK_M_FREE(); \
		return EXIT_FAILURE; \
	}
	
	/* Binární soubor není aktuální */
	CHECK( init_shm(KB_shm, KB_path) );
	
	CHECK( ftruncate(KB_bin_fd, (*KB_shm)->capacity) );
	CHECK( fzeroing(KB_bin_fd, (*KB_shm)->capacity) == -1 );
	
	KB_bin = (KBSharedMem *) mmap(NULL, (*KB_shm)->capacity, PROT_WRITE,
								  MAP_SHARED, KB_bin_fd, 0);
	if (KB_bin == MAP_FAILED)
	{
		perror("mmap");
		CHECK_M_FREE();
		return EXIT_FAILURE;
	}
	
	memcpy( KB_bin, *KB_shm, (*KB_shm)->capacity );
	
	CHECK( munmap(KB_bin, (*KB_shm)->capacity ) );
	CHECK( close(KB_bin_fd) == -1 );
	FREE( KB_bin_path );
	
	#undef CHECK
	#undef CHECK_M_FREE
	
	return EXIT_SUCCESS;
#endif
}

/**
 * Čeká dokud nepříjde nějaký signál.
 * @param mask Množina blokovaných signálů (NULL pro výchozí nastavení).
 */
void wait_to_sig(sigset_t *s_mask)
{
	int old_errno = 0;
	struct sigaction sig_act;
	struct sigaction sig_oact[3];
	sigset_t *mask;
	
	/* Výchozí množina blokovaných signálů */
	sigset_t d_mask;
	sigfillset(&d_mask);
	sigdelset(&d_mask, SIGTERM);
	sigdelset(&d_mask, SIGINT);
	sigdelset(&d_mask, SIGQUIT);
	
	if (s_mask != NULL)
		mask = s_mask;
	else
		mask = &d_mask;
	
	/* Nastavení odchytnutí signálů */
	memset(&sig_act, 0, sizeof(sig_act));
	sig_act.sa_handler = sig_wake;
	sigaction(SIGTERM, &sig_act, &sig_oact[0]);
	sigaction(SIGINT, &sig_act, &sig_oact[1]);
	sigaction(SIGQUIT, &sig_act, &sig_oact[2]);
	
	old_errno = errno;
	/* Vyčkání na příchod signálu. */
	sigsuspend(mask);
	if (errno == EINTR)
	{
		errno = old_errno;
	}
	
	/* Nastavení odchytnutí signálů zpět */
	sigaction(SIGTERM, &sig_oact[0], NULL);
	sigaction(SIGINT, &sig_oact[1], NULL);
	sigaction(SIGQUIT, &sig_oact[2], NULL);
}

//=========================||-MAIN-||=========================
/**
 * Hlavní program
 */
int main(int argc, char **argv)
{
	char *KB_path = "./KB-HEAD.all";
	KBSharedMem *KB_shm = NULL;
	int status = 0;
	int opt;
	struct SArguments arguments = {NULL, NULL};

	// Nastavení chování při SIGTERM, SIGINT a SIGQUIT
	struct sigaction sig_act;
	memset(&sig_act, 0, sizeof(sig_act));
	sig_act.sa_handler = terminate;
	sigaction(SIGTERM, &sig_act, NULL);
	sigaction(SIGINT, &sig_act, NULL);
	sigaction(SIGQUIT, &sig_act, NULL);
	
	// Blokování ostatních signálů
	sigset_t mask;
	sigfillset(&mask);
	sigdelset(&mask, SIGTERM);
	sigdelset(&mask, SIGINT);
	sigdelset(&mask, SIGQUIT);
	sigprocmask(SIG_SETMASK, &mask, NULL);
	
	// Zpracování argumentů
	while ((opt = getopt(argc, argv, "b:s:")) != -1) {
		switch (opt) {
			case 'b':
				arguments.bin_kb_path = optarg;
			break;
			case 's':
				arguments.shm_name = optarg;
				KB_shm_name = arguments.shm_name;
			break;
			default: /* '?' */
				fprintf(stderr, "Usage: %s [-s SHM_NAME] [{-b KB-HEAD.all.bin} | KB-HEAD.all]\n",
						argv[0]);
				exit(EXIT_FAILURE);
			break;
		}
	}

	if (arguments.bin_kb_path)
		status = init_shm_from_bin(&KB_shm, arguments.bin_kb_path);
	else if (optind >= argc)
		status = initKBShm(&KB_shm, KB_path);
	else
		status = initKBShm(&KB_shm, argv[optind]);
	
	if (status) return EXIT_FAILURE;
	
	printf("%s: Waiting for signal...\n", argv[0]);
	fflush(stdout);
#ifndef SPEEDTEST
	wait_to_sig(&mask);
#endif
	
	if (errno != 0)	// Ověření správnosti vykonání funkcí.
	{
		perror("error");
		free_all();
		return EXIT_FAILURE;
	}
	if ( free_all() == EXIT_FAILURE ) {
		return EXIT_FAILURE;
	}
	return EXIT_SUCCESS;
}
/* konec souboru main.c */
