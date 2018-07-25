#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>

#include "libKB_shm.h"

int main()
{
	char *KB_shm_name = "/decipherKB-daemon_shm";
	KBSharedMem *KB_shm_p = NULL;
	int KB_shm_fd = -1;
	int status = 0;
	
	status = connectKBSharedMem( &KB_shm_p, &KB_shm_fd, KB_shm_name );
	if (status != 0)
	{
		puts("ERROR");
		return 1;
	}
	
	printf("%lx: hit enter...", (size_t)KB_shm_p);
	while(getchar() != '\n');
	
	char *str = KBSharedMemDataAt(KB_shm_p, -1, -1);
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
