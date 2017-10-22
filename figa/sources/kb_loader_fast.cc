#include <iostream>
#include <fstream>
#include <string>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <cwchar>

using namespace std;

extern "C" char** queryTree(char* filename, int count){
	
	ifstream file(filename);
	if (!file.is_open()){
		cerr << "Couldn't open file!" << endl;
		return NULL;
	}
	
	string line;
	int length;
	char **queryResult = (char**) malloc(count * sizeof(char**));
		
	for (int j=0; j<count; j++){
		getline(file,line);
		length = (int) line.length();
		queryResult[j] = (char *) malloc(length+1);
		if(queryResult[j]){												 
			strcpy(queryResult[j],line.c_str());
		}
	}
	
	file.close();
	return queryResult;
	}

/*int main() {

	char** neco = (char**) malloc (561248 * sizeof(char**)); 
	neco = queryTree(NULL,561248);
	for (int i = 0; i < 561248; i++) {
		if (neco[i] != NULL)
			cout << neco[i] << endl;
		else 
			break;
	}
	return 0;
}*/
