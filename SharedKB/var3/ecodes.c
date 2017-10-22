/* -*- coding: utf-8 -*- */
/*
 * Soubor:  ecodes.c
 * Datum:   2013/08/29
 * Autor:   Jan Doležal, xdolez52@stud.fit.vutbr.cz
 * Projekt: Decipher - Knowledge Base daemon
 * Popis:   Program ze souboru načte matici stringů,
 *          drží ji efektivně v paměti a efektivně v ní hledá
 *          a tuto paměť sdílí read-only pro další programy.
 */
/**
 * @file	ecodes.c
 * @date	2013/08/29
 * @author	Jan Doležal, xdolez52@stud.fit.vutbr.cz
 * @brief	Decipher - Knowledge Base daemon
 */

// Vlastní chybové kódy.
#include "ecodes.h"



const char *ECODEMSG[] =
{
	/* E_OK */
	"Vše v pořádku.\n",
	/* E_CLWRONG */
	"Chybné parametry příkazového řádku.\n",
	/* E_NOTDIGIT */
	"Načtená hodnota není (kladné) číslo.\n",
	/* E_ZERONUM */
	"Požadováno číslo větší než nula.\n",
	/* E_UNKNOWN */
	"Neznámá chyba.\n",
};



void printECode(int ecode)
{
	if (ecode < E_OK || ecode > E_UNKNOWN)
	{ ecode = E_UNKNOWN; }
	
	fprintf(stderr, "%s", ECODEMSG[ecode]);
}

/* konec souboru ecodes.c */
