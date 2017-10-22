/* -*- coding: utf-8 -*- */
/*
 * Soubor:  ecodes.h
 * Datum:   2013/08/29
 * Autor:   Jan Doležal, xdolez52@stud.fit.vutbr.cz
 * Projekt: Decipher - Knowledge Base daemon
 * Popis:   Program ze souboru načte matici stringů,
 *          drží ji efektivně v paměti a efektivně v ní hledá
 *          a tuto paměť sdílí read-only pro další programy.
 */
/**
 * @file	ecodes.h
 * @date	2013/08/29
 * @author	Jan Doležal, xdolez52@stud.fit.vutbr.cz
 * @brief	Decipher - Knowledge Base daemon
 */

#ifndef ECODES_H
#define ECODES_H

// práce se vstupem/výstupem
#include <stdio.h>

// obecné funkce jazyka C
#include <stdlib.h>

// proměnná errno
#include <errno.h>
#include <assert.h>

/** Kódy chyb programu */
enum tecodes
{
	E_OK = 0,	// Bez chyby
	E_CLWRONG,	// Chybný příkazový řádek.
	E_NOTDIGIT,	// Načtená hodnota není číslo
	E_ZERONUM,	// Načtená hodnota je nula
	E_UNKNOWN,	// Neznámá chyba
};

/** Chybová hlášení odpovídající chybovým kódům. */
extern const char *ECODEMSG[];

/**
 * Vytiskne hlášení odpovídající chybovému kódu.
 * @param ecode kód chyby programu
 */
void printECode(int ecode);

#endif
/* konec souboru ecodes.h */
