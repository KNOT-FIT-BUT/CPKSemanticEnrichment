/* -*- coding: utf-8 -*- */
/*
 * Soubor:  global.c
 * Datum:   2013/08/29
 * Autor:   Jan Doležal, xdolez52@stud.fit.vutbr.cz
 * Projekt: Decipher - Knowledge Base daemon
 * Popis:   Program ze souboru načte matici stringů,
 *          drží ji efektivně v paměti a efektivně v ní hledá
 *          a tuto paměť sdílí read-only pro další programy.
 */
/**
 * @file	global.c
 * @date	2013/08/29
 * @author	Jan Doležal, xdolez52@stud.fit.vutbr.cz
 * @brief	Decipher - Knowledge Base daemon
 */

// Často potřebné hlavičky
#include "global.h"
#include "ecodes.h"

void StringInitEmpty(String *string)
{
	string->str=NULL;
	string->length=0;
	string->capacity=0;
}



size_t StringSizeOf(String *string)
{
	size_t sizeOf = 0;
	
	if (string->str != NULL)
	{
		sizeOf += (string->length + 1) * sizeof(char); // řetězec (+1 pro znak '\0')
	}
	
	return sizeOf;
}



void deleteString(String *string)
{
	FREE( string->str );
	string->length=0;
	string->capacity=0;
}



FILE *open_file_to_write(const char *name)
{
	if (strcmp(name, "-") == 0)
		return stdout;		// Výstup nastaven na stdout
	
	FILE *p_soubor;		///< Bude do něj uložena adresa otevřeného souboru.
	p_soubor = fopen(name,"w+");
	return p_soubor;		// Pokud se soubor nepovede vytvořit, vrati ukazatel na NULL.
}



FILE *open_file_to_read(const char *name)
{
	if (strcmp(name, "-") == 0)
		return stdin;		// Vstup nastaven na stdin
	
	FILE *p_soubor;		///< Bude do něj uložena adresa otevřeného souboru.
	p_soubor = fopen(name,"r");
	return p_soubor;		// Pokud se soubor nepovede otevřít, vrati ukazatel na NULL.
}



int close_file(const char *name, FILE *fp)
{
	if (strcmp(name, "-") == 0)
		return EXIT_SUCCESS;	// Výstup nastaven na stdout nebo stdin -> OK
	
	// Uzavření souboru
	if (fclose(fp) == EOF)
		return EXIT_FAILURE;
	return EXIT_SUCCESS;
}



int read_line(String *string, FILE *p_soubor, int *last_letter)
{
	unsigned count = 0;		// Počet přečtených znaků.
	unsigned bufsize = 32;	// Skutečná velikost bufferu jenž začíná 2⁵.
	char *buf = NULL;	// Buffer.
	char *rebuf = NULL;	// Ukazatel na novou adresu bufferu.
	
	// Alokace bufferu
	buf = malloc(bufsize*sizeof(char));	// počáteční velikost bufferu
	if (buf == NULL) return EXIT_FAILURE;
	
	// Načítání znaků do bufferu
	while ((*last_letter = getc(p_soubor)) != EOF && *last_letter != '\n')
	{
		if (count+1 == bufsize)	// count + 1 je na ukočovací znak '\0'.
		{				// Když jsme za hranicí pole je třeba...
			bufsize <<= 1;		// ... zvětšení velikosti bufferu na dvojnásobek.
			rebuf = realloc(buf, bufsize*sizeof(char));
			if (rebuf == NULL) {	// Pokud není další místo, konec.
				free(buf);
				buf = NULL;
				return EXIT_FAILURE;
			}
			buf = rebuf;		// Předání nové adresy bufferu.
		}
		
		buf[count++] = *last_letter;// Přidání znaku do řetězce.
	}
	buf[count] = '\0';		// Přidání znaku znak konce řetězce.
	
	// Předání adresy a délky řetězce a délky alokovaného místa.
	string->str = buf;
	string->length = count;
	string->capacity = bufsize;
	
	return EXIT_SUCCESS;
}



int get_num_arg(const char *source, unsigned int *dest)
{
	char *chyba;				///< ukazatel na písmeno kde přestala číst funkce strtoul()
	unsigned long l_number;
	
	if (source[0] != '-')
	{
		l_number = strtoul(source, &chyba, 10);
		if (l_number > UINT_MAX)
			errno = ERANGE;
		else
			*dest = l_number;
	}
	else
		return E_NOTDIGIT;
	
	if (*chyba != 0 || chyba == source || errno)
		return E_NOTDIGIT;
	
	return E_OK;
}



void die(const char *msg, int exit_status)
{
	perror(msg);
	exit(exit_status);
}



ssize_t fzeroing(int fd, size_t count)
{
	#define BUF_LEN 4096

	char buf[BUF_LEN];
	size_t pos;
	size_t to_write;
	ssize_t written;

	memset(buf, 0, BUF_LEN);

	if (lseek(fd, 0, SEEK_SET) == (off_t)(-1)) {
		return -1;
	}

	for (pos = 0; pos < count; pos += written) {
		to_write = count - pos;
		to_write = (to_write < BUF_LEN) ? (to_write) : (BUF_LEN);

		written = write(fd, buf, to_write);
		if (written == -1) {
			return -1;
		}
	}

	if (fsync(fd) == -1) {
		return -1;
	}

	return pos;

	#undef BUF_LEN
}

/* konec souboru global.c */
