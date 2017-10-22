#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>

#include "libKB_shm.h"

int main()
{
	KBSharedMem *KB_shm_p = NULL;
	int KB_shm_fd = -1;
	int status = 0;
	
	status = connectKBSharedMem( &KB_shm_p, &KB_shm_fd );
	if (status != 0)
	{
		puts("ERROR");
		return 1;
	}
	
	printf("%lx: hit enter...", (size_t)KB_shm_p);
	while(getchar() != '\n');
	
	char *str = KBSharedMemHeadAt(KB_shm_p, 0, 0);
	if (str != NULL)
		puts(str);
	else
		puts("str == NULL");
	
	printf("hit enter...");
	while(getchar() != '\n');
	
	unsigned *kb_row = KBTableRow(&KB_shm_p->table, 0);
	if (kb_row != NULL)
		printf("%u\n", *kb_row);
	else
		puts("kb_row == NULL");
	
	printf("hit enter...");
	while(getchar() != '\n');
	
	unsigned *num = KBSharedMemTableRowLength(KB_shm_p, 1);
	if (num != NULL) {
		unsigned i = 0;
		printf("%u", *num);
		while ( (num = KBSharedMemTableRowColon(KB_shm_p, 1, ++i)) ) {
			printf("\t%u", *num);
		}
		printf("\ti==%u\n", i);
	}
	else {
		puts("num == NULL");
	}
	
	printf("hit enter...");
	while(getchar() != '\n');
	
	status = disconnectKBSharedMem( &KB_shm_p, &KB_shm_fd );
	if (status != 0)
	{
		puts("ERROR");
		return 1;
	}
	
	return 0;
}
