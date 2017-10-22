/* -*- coding: utf-8 -*- */
/*
 * Soubor:  global.h
 * Datum:   2013/08/29
 * Autor:   Jan Doležal, xdolez52@stud.fit.vutbr.cz
 * Projekt: Decipher - Knowledge Base daemon
 * Popis:   Program ze souboru načte matici stringů,
 *          drží ji efektivně v paměti a efektivně v ní hledá
 *          a tuto paměť sdílí read-only pro další programy.
 */
/**
 * @file	global.h
 * @date	2013/08/29
 * @author	Jan Doležal, xdolez52@stud.fit.vutbr.cz
 * @brief	Decipher - Knowledge Base daemon
 */

#ifndef GLOBAL_H
#define GLOBAL_H

// práce se vstupem/výstupem
#include <stdio.h>

// obecné funkce jazyka C
#include <stdlib.h>
#include <stdbool.h>

// kvůli funkci strtoul a dalších
#include <string.h>

// ošetření přetečení
#include <limits.h>

// proměnná errno
#include <errno.h>
#include <assert.h>

// často potřebný hlavičkový soubor
#include <unistd.h>

#define FREE(pointer) { free(pointer); pointer = NULL; }

#define ERROR(message) \
  fprintf(stderr,"%s (%s:%s:%d)\n",(message),__FILE__,__func__,__LINE__)

/**
 * Řetězec
 */
typedef struct {
	char *str;
	unsigned length;
	unsigned capacity;
} String;

/**
 * Inicializuje prázdný String \a string.
 */
void StringInitEmpty(String *string);

/**
 * "Destruktor" Stringu.
 */
void deleteString(String *string);

/**
 * Zjistí počet celé obsazené paměti bez sizeof(String).
 */
size_t StringSizeOf(String *string);

/**
 * Funkce open_file_to_write
 * - Otevře soubor pro zápis, pokud není zadán výstup na stdout pomocí "-".
 * @param[in] name Ukazatel na řetezec, obsahující jméno souboru.
 * @return Vrací ukazatel na otevřený soubor. (v případě chyby na NULL)
 */
FILE *open_file_to_write(const char *name);

/**
 * Funkce open_file_to_read
 * - Otevře soubor pro čtení, pokud není zadán vstup ze stdin pomocí "-".
 * @param[in] name Ukazatel na řetezec, obsahující jméno souboru.
 * @return Vrací ukazatel na otevřený soubor. (v případě chyby na NULL)
 */
FILE *open_file_to_read(const char *name);

/**
 * Funkce close_file
 * - Zavře soubor, pokud není zadán stdout nebo stdin pomocí "-".
 * @param[in]	name	Ukazatel na řetezec, obsahující jméno souboru.
 * @param[in]	fp	Ukazatel na otevřený soubor.
 * @return Vrací chybový kód.
 */
int close_file(const char *name, FILE *fp);

/**
 * Funkce read_line
 * - Přečte řádek o předem neznámé délce
 * @param *string	Ukazatel na řeťezec (pole znaků), kde se uloží onen řádek (ukazatel).
 * @param *p_soubor	Ukazatel na otevřený soubor.
 * @param *last_letter	Adresa do které se uloží poslední načtené písmeno.
 * @return Vrací chybový kód.
 */
int read_line(String *string, FILE *p_soubor, int *last_letter);

/**
 * Nádstavba pro strtoul. Převede řetězec na unsigned int a vratí chybový kód.
 * @param[in]	source	Řetězec, jenž se bude převádět na číslo.
 * @param[out]	dest	Ukazatel na místo kde se převod uloží.
 * @return Vrací chybový kód podle tecodes
 */
int get_num_arg(const char *source, unsigned int *dest);

/**
 * Ukončí program se zadanou zprávou a stavem.
 * @param[in]	msg		Zadaná zpráva.
 * @param[in]	exit_status	Ukončujíci stav.
 */
void die(const char *msg, int exit_status);

/**
 * Zapíše do streamu daný počet znaků '\0'.
 * @param[in]	fd		File descritor.
 * @param[in]	count	Počet nul k zapsání.
 */
ssize_t fzeroing(int fd, size_t count);

#endif
/* konec souboru global.h */
