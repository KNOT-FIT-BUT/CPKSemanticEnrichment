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
	
	
	status = disconnectKBSharedMem( &KB_shm_p, &KB_shm_fd );
	if (status != 0)
	{
		puts("ERROR");
		return 1;
	}
	
	return 0;
}
