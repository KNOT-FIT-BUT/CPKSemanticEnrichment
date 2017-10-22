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
	return read_until(string, p_soubor, last_letter, "\n");
}



int read_until(String *string, FILE *p_soubor, int *last_letter, const char *delims)
{
	unsigned count = 0;		// Počet přečtených znaků.
	unsigned bufsize = 32;	// Skutečná velikost bufferu jenž začíná 2⁵.
	char *buf = NULL;	// Buffer.
	char *rebuf = NULL;	// Ukazatel na novou adresu bufferu.
	const size_t delims_len = strlen(delims);
	bool stop = false;
	
	// Alokace bufferu
	buf = malloc(bufsize*sizeof(char));	// počáteční velikost bufferu
	if (buf == NULL) return EXIT_FAILURE;
	
	// Načítání znaků do bufferu
	while ((*last_letter = getc(p_soubor)) != EOF)
	{
		for (size_t i = 0; i < delims_len; i++) {
			if (*last_letter == delims[i]) {
				stop = true;
				break;
			}
		}
		if (stop) {
			break;
		}
		
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



unsigned long my_strtoul(const char *nptr, char **endptr, int base, unsigned long maxvalue)
{
	unsigned long result;
	unsigned long l_number;
	
	if (nptr[0] != '-')
	{
		l_number = strtoul(nptr, endptr, base);
		if (l_number > maxvalue) {
			errno = ERANGE;
			result = maxvalue;
		}
		else {
			result = l_number;
		}
	}
	else {
		errno = ERANGE;
		result = maxvalue;
	}
	
	return result;
}



uint32_t strtoui32(const char *nptr, char **endptr, int base)
{
	return my_strtoul(nptr, endptr, base, UINT32_MAX);
}



unsigned strtoui(const char *nptr, char **endptr, int base)
{
	return my_strtoul(nptr, endptr, base, UINT_MAX);
}



char * strcat_m(const char *prefix, const char *suffix)
{
	const size_t prefix_len = strlen(prefix);
	const size_t suffix_len = strlen(suffix);
	char *result = NULL;
	
	/* Vytvoření příkazu. */
	result = malloc( (prefix_len + suffix_len +1) * sizeof(char) ); // +1 pro znak '\0'
	if (result == NULL)
	{
		perror("malloc");
		return NULL;
	}
	
	strcpy(result, prefix);
	strcpy(result + prefix_len, suffix);
	
	return result;
}



void die(const char *msg, int exit_status)
{
	perror(msg);
	exit(exit_status);
}

/* konec souboru global.c */
