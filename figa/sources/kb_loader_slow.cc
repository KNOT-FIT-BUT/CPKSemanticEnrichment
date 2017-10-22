#include <iostream>
#include <fstream>
#include <string>
#include <cstdio>
#include <cstring>
#include <cstdlib>

using namespace std;

extern "C" char*** queryTree(char* filename, int count, int maxitem){
	
	ifstream file(filename);
	if (!file.is_open()){
		cerr << "Couldn't open file!" << endl;
		return NULL;
	}

	string line;
	string subline;
	size_t length = 0;
	size_t length_next = 0;
	int length_text = 0;
	int iter = 0;
	char ***queryResult = (char***) malloc(count * sizeof(char***));
	
	for (int j=0; j<count; j++){

		getline(file,line);
		
		switch(line[0]) {
			case 'p': 
				iter = 33;
				break;
			case 'w':
				iter = 31;
				break;
			case 'l':
				iter = 22;
				break;
			default: 
				iter = maxitem;
		}

		queryResult[j] = (char**) malloc(iter * sizeof(char**));
		length = 0;
		length_next = (int) line.find_first_of("\t",0);

		for (int i = 0; i<iter; i++) {
			subline.assign(line,length,(length_next-length));
			length_text = subline.length();
			queryResult[j][i] = (char *) malloc(length_text+1);
			if(queryResult[j][i]){												 
				strcpy(queryResult[j][i],subline.c_str());
			}
		
			length = length_next+1;
			length_next = (int) line.find_first_of("\t",length);

			if (length_next == string::npos) {
				i++;
				subline.assign(line,length,string::npos);
				length_text = subline.length();
				queryResult[j][i] = (char *) malloc(length_text+1);
				if(queryResult[j][i]){												 
					strcpy(queryResult[j][i],subline.c_str());
				}
				break;
			}
		}
	}

	file.close();
	return queryResult;
}

/*int main() {

	char*** neco = (char***) malloc (561248 * sizeof(char***)); 
	neco = queryTree(NULL,561248);
	for (int i = 0; i < 561248; i++) {
		cout << i << endl;
		for (int j = 0; j < 22; j++) 
			if (neco[i][j] != NULL)
				cout << neco[i][j] << endl;
			else 
				break;
	}
	return 0;
}*/
