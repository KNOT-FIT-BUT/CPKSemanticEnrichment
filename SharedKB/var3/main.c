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
const char *KB_shm_name = "/decipherKB-daemon_shm";
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
 | Funkce            |
 +------------------*/
/**
 * Uvolní všechny prostředky.
 */
int free_all()
{
	#define CHECK(cond) if ( cond ) { perror( #cond ); }
	
	if (KB_shm_fd >= 0) {
		CHECK( close(KB_shm_fd) == -1 );
		CHECK( shm_unlink(KB_shm_name) == -1 );
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

/*       _\|/_
         (o o)
 +----oOO-{_}-OOo----+
 | namelist.ASCII    |
 +------------------*/
/**
 * Alokuje paměť a naplní ji hodnotami na řádku (oddělenými ';').
 */
unsigned * namelist_getRow(FILE *filtered_namelist, int *last_letter)
{
	/* Inicializace dat */
	unsigned *array = NULL;
	unsigned *rebuf = NULL;
	unsigned length = 1;
	unsigned capacity = 32;	// Skutečná velikost pole jenž začíná 2⁵.
	String str_buf;
	char *endptr = NULL;
	
	/* Inicializace */
	StringInitEmpty( &str_buf );
	
	/* Alokace prostoru */
	array = malloc( (capacity) * sizeof(unsigned) );	// počáteční velikost pole
	if (array == NULL) {
		perror("malloc");
		return NULL;
	}
	
	/* Nulování */
	memset(array, 0, (capacity) * sizeof(unsigned));
	
	/* Načtení dat */
	#define CHECK_M_FREE() \
	{ \
		deleteString( &str_buf ); \
		FREE(array); \
	}
	
	#define CHECK(cond, prefix) \
	if ( cond ) \
	{ \
		if ((prefix)[0] == 0) { \
			perror( #cond ); \
		} \
		else { \
			fprintf(stderr, "%s: ", prefix); \
			perror( #cond ); \
		} \
		CHECK_M_FREE(); \
		return NULL; \
	}
	do {
		// Zde probíhá alokace, která bude uvolňena při chybě nebo na konci cyklu.
		CHECK( read_until(&str_buf, filtered_namelist, last_letter, ";\n"), "" );
		
		if (str_buf.str != NULL && str_buf.length == 0) {
			deleteString( &str_buf );
			break;
		}
		else if (str_buf.str[0] == 'N') {
			deleteString( &str_buf );
			CHECK( read_line(&str_buf, filtered_namelist, last_letter), "" );
			deleteString( &str_buf );
			break;
		}
		
		if (length == capacity)
		{				// Když jsme za hranicí pole je třeba...
			capacity <<= 1;		// ... zvětšení velikosti bufferu na dvojnásobek.
			rebuf = realloc(array, capacity*sizeof(unsigned));
			CHECK( rebuf == NULL, "realloc" );	// Pokud není další místo, konec.
			array = rebuf;		// Předání nové adresy bufferu.
		}
		
		// Uložení hodnoty
		array[length++] = strtoui(str_buf.str, &endptr, 10);
		CHECK( (*endptr != 0 || endptr == str_buf.str || errno), "strtoui" );
		
		// Vyprázdní se buffer
		deleteString( &str_buf );
	} while (*last_letter != EOF && *last_letter != '\n');
	
	#undef CHECK
	#undef CHECK_M_FREE
	
	/* Zápis délky na nultý prvek */
	array[0] = length;
	
	return array;
}

/**
 * Naplní tabulku v KBSharedMem hodnotami z namelistu.
 * @return Vrací chybový kód.
 */
int get_namelist(KBSharedMem *KB_buf, char *namelist_path)
{
	char *cmd = NULL;
	FILE *cmd_stdout = NULL;
	int last_letter = 0;
	
	#define CHECK(cond, prefix) \
	if ( cond ) \
	{ \
		if ((prefix)[0] == 0) { \
			perror( #cond ); \
		} \
		else { \
			fprintf(stderr, "%s: ", prefix); \
			perror( #cond ); \
		} \
		return EXIT_FAILURE; \
	}
	
	/* Vytvoření příkazu. */
	cmd = strcat_m("cut -d '|' -f 2 < ", namelist_path);
	CHECK( cmd == NULL, "strcat_m" );
	
	/* Zfiltrování namelistu */
	cmd_stdout = popen(cmd, "r");
	if (cmd_stdout == NULL) {
		FREE(cmd);
		return EXIT_FAILURE;
	}
	FREE(cmd);
	
	/* Načítání jednotlivých řádků */
	while (last_letter != EOF) {
		unsigned *row = namelist_getRow(cmd_stdout, &last_letter);
		CHECK( row == NULL, "namelist_getRow" );
		if (row[0] <= 1) {
			FREE(row);
			continue; // Přeskočení nesmyslů
		}
		KBTablePushBack( &(KB_buf->table), row );
	}
	
	/* Uzavření roury */
	CHECK( pclose(cmd_stdout), "" );
	
	#undef CHECK
	
	return EXIT_SUCCESS;
}

/*       _\|/_
         (o o)
 +----oOO-{_}-OOo----+
 | Hlavní funkce     |
 +------------------*/
/**
 * Alokuje sdílenou paměť a naplní ji hodnotami.
 * @param KB_shm Ukazatel na sdílenou paměť.
 * @param KB_path Cesta ke znalostní bázi.
 */
int init_shm(KBSharedMem **KB_shm, char *KB_path, char *namelist_path)
{
	char *FILENAME = KB_path;
	int last_letter = 0;  // Poslední načtené písmeno z fce read_line() pro zjištění konce souboru.
	KBSharedMem KB_buf;   // Buffer pro KB.
	FILE *infile = NULL;
	String str_buf;
	KBString kb_str_buf;
	
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
	
	/* Načítání hlavičky */
	while (last_letter != EOF)
	{
		// Zde probíhá alokace, která bude uvolňena při chybě, nebo na konci funkce.
		CHECK( read_line( &str_buf, infile, &last_letter ) );
		
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
	
	/* Načtení namelistu */
	if ( get_namelist(&KB_buf, namelist_path) == EXIT_FAILURE )
	{
		perror("get_namelist");
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
		if (KB_bin != NULL) \
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
int initKBShm(KBSharedMem **KB_shm, char *KB_path, char *namelist_path)
{
#ifndef COPY_TO_DISC_EN
	return init_shm(KB_shm, KB_path, namelist_path);
#else
	int old_errno = 0;
	bool KB_bin_exist = false;
	bool KB_bin_ok = false;
	int KB_bin_fd = -1;
	struct stat KB_stat;
	struct stat KB_bin_stat;
	struct stat namelist_stat;
	char *KB_bin_path = NULL;
	KBSharedMem *KB_bin = NULL;
	
	/* Vytvoření cesty k binárnímu souboru. */
	KB_bin_path = strcat_m(KB_path, ".bin");
	if (KB_bin_path == NULL)
	{
		perror("strcat_m");
		return EXIT_FAILURE;
	}
	
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
		CHECK( stat(namelist_path, &namelist_stat) );
		
		if ((KB_bin_stat.st_mtime > KB_stat.st_mtime) && (KB_bin_stat.st_mtime > namelist_stat.st_mtime))
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
	
	/* Vytovoření binárního souboru */
	CHECK( (KB_bin_fd = open(KB_bin_path, O_RDWR|O_CREAT, 0640)) == -1 );
	FREE( KB_bin_path );
	
	#undef CHECK
	#undef CHECK_M_FREE
	
	#define CHECK_M_FREE() \
	{ \
		free_all(); \
		close(KB_bin_fd); \
	}
	
	#define CHECK(cond) \
	if ( cond ) \
	{ \
		perror( #cond ); \
		CHECK_M_FREE(); \
		return EXIT_FAILURE; \
	}
	
	/* Binární soubor není aktuální */
	CHECK( init_shm(KB_shm, KB_path, namelist_path) );
	
	CHECK( ftruncate(KB_bin_fd, (*KB_shm)->capacity) );
	
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
	char *namelist_path = "./namelist.ASCII";
	KBSharedMem *KB_shm = NULL;
	int status = 0;
	
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
	
	if (argc == 3) {
		if ( strcmp(argv[1], "-b") == 0 )
			status = init_shm_from_bin(&KB_shm, argv[2]);
		else
			status = initKBShm(&KB_shm, argv[1], argv[2]);
	}
	else {
		status = initKBShm(&KB_shm, KB_path, namelist_path);
	}
	
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
