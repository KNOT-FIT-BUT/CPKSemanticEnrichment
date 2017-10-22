#include <iostream>
#include <cstdio>

using namespace std;

int many_bytes(short);

int main() {
	
	short znak = getchar();
	int count = 0;
	int pocet = 0;
	
	while (znak != EOF && znak != '\0') {
		if ((znak >= 0) && (znak < 128)) {
			printf("%c",znak);
			znak = getchar();
		}
		else {
			cout << "&#x";

			pocet = many_bytes(znak);

			for (int i = 0; i < pocet; i++) {
				printf("%X",znak);
				znak = getchar();
			}
			cout << ";";
		}
	}

	return 0;
}


int many_bytes(short znak) {
	
	for (int i = 6; i > 0; i--) {
		if (!((znak >> i) & 1)) {
			return 7 - i;
		}
	}
	return 2;
}
