/*** 
 *** Author: Andrej Rajcok
 *** Email: xrajco00@stud.fit.vutbr.cz
 *** Popis: Implementacia triedy figa_cedar pre vyhladavanie entit v texte
 *** TODO: 
 ***/

#include <fstream>
#include <iostream>
#include <sstream>
#include <unistd.h>
#include <algorithm>
#include <cwchar>
#include "figa_cedar.h"

#include <cstdint>
#include <random>
#include <vector>
#include <time.h>

using namespace std;

// function to build dictionary
// it takes vector of char pointers, representing entities,vector of int values
// and it fills given instance of dictionary
template <typename dict_T>
int BuildDict(vector<char*> indata,vector<int> values,dict_T &dict){
	char** data = indata.data();
	unsigned int size = indata.size();	
	int error = dict.build(size,(const char**)data,NULL,values.data());
	return error;
}

//====================================//
// Nazev: print_help                  //
// Popis: vytiskne napovedu na stdin  //
//====================================//
void print_help () {
	std::cout << std::endl;
	std::cout << "rebuilded and updated: FItGAzetter Cedar, Jan 4th, 2016, Andrej ";
	std::cout << "Rajcok, xrajco00@stud.fit.vutbr.cz" << std::endl;
	std::cout << "updated: FItGAzetter v0.8, July 9th, 2014, Peter ";
	std::cout << "Hostacny, xhosta03@stud.fit.vutbr.cz" << std::endl;
	std::cout << "updated: FItGAzetter v0.7c, November 16th, 2013, Karel ";
	std::cout << "Brezina, xbrezi13@stud.fit.vutbr.cz" << std::endl;
	std::cout << "FItGAzetteer v0.35c, September 14th, 2010, Marek ";
	std::cout << "Visnovsky, xvisno00@stud.fit.vutbr.cz" << std::endl;
	std::cout << "based on: fsa Ver. 0.49, March 18th, 2009, (c) Jan Daciuk";
	std::cout << ",jandac@eti.pg.gda.pl" << std::endl << std::endl;
	std::cout << "Usage: ./figav08 [options]..." << std::endl << std::endl;
	std::cout << "Options:" << std::endl;
	std::cout << "  -a        -> autocomplete function" << std::endl;
	std::cout << "  -b        -> return offset in bytes instead of characters [ONLY FIGA]" << std::endl;
	std::cout << "  -d FILE   -> define tree file or namelist" << std::endl;
    std::cout << "  -n        -> file given in -d, is namelist" << std::endl;
	std::cout << "  -w FILE   -> write given tree from -d into file" << std::endl;
	std::cout << "  -f FILE   -> define input file" << std::endl;
	std::cout << "  -h        -> print this help" << std::endl;
	std::cout << "  -m NUMBER -> define number of returned entities [ONLY AUTOCOMPLETE]" << std::endl;
	std::cout << "               (default value is 5)" << std::endl;
	std::cout << "  -o        -> enable entity overlapping [ONLY FIGA]" << std::endl;
	std::cout << "  -p        -> for print out string" << std::endl;
	std::cout << "  -s        -> enable spellchecking and define spell_automaton [ONLY FIGA]" << std::endl;
	std::cout << "  -x        -> return all possible entities [ONLY AUTOCOMPLETE]" << std::endl;
	return;
} // konec print_help

//

/* Name:        main
 * Class:       none
 * Purpose:     Main function. Load parameters, determines course of action, load dictionary and call lookup function.
 * Parameters:  
 * Returns:     Succes.
 * Remarks:     
 */
int main(int argc,char* const* argv){
	int error=0;

    // vectors and iterators for loaded data to create dicitonary
	vector<char*> data;
    vector<int> values;
	vector<char*>::iterator it;
    ifstream input;
	
	bool cedar = true;

    // dictionaries
	dict_type_cedar dict_cedar;
	dict_type_darts dict_darts;
	
    // variables to process parameters
    char c;
    bool dict_file = false;
    char* dict_file_name = NULL;
    char* file_name = NULL;
    char* write_dict_file = NULL;
    bool file = false,write_dict = false,namelist = false,return_all = false;
    bool overlapping = false,spellcheck = false,autocomplete = false,print_bool = false,in_bytes = false;
    int many = 5;

	// zpracovani argumentu
	while ((c = getopt(argc, argv, "aboqxnw:d:f:phm:s")) != -1)
		switch (c) {
			case 'a':
				autocomplete = true;
				break;
			case 'b':
				in_bytes = true;
				break;
			case 'd':
                dict_file = true;
                dict_file_name = optarg;
				error--;
				break;
			case 'n': // dictionary subor je namelist
                dict_file = false;
                namelist = true;
                break;
            case 'w': // zapisat dictionary do suboru
                write_dict = true;
                write_dict_file = optarg;
			case 'f':
				file = true;
				file_name = optarg;
				break;
			case 'h':
				error = 2;
				break;
			case 'o':
				overlapping = true;
				break;
			case 'p':
				print_bool = true;
				break;
			case 'q':
//				quotes_boundary = true;
				break;
			case 'x':
				return_all = true;
				break;
			case 's':
                spellcheck = true;
				break;
			case 'm':
				many = atoi(optarg);
				break;
			default:
				std::cerr << "FIGA ERROR: Unrecognized option. " << std::endl;
				return 2;
			}

    //
    if(dict_file && namelist == false){
        if(figa_cedar::checkFileNameForDictType(dict_file_name,cedar)){
            cerr << "Dictionary file need to have '.dct' or '.ct' ending. '.ct' for CedarTree and '.dct' for DartsCloneTree" << endl;
            return 1;
        }
    }
    
    bool cedar_check = cedar;
    if(write_dict){
        if(figa_cedar::checkFileNameForDictType(write_dict_file,cedar_check)){
            cerr << "Dictionary file need to have '.dct' or '.ct' ending. '.ct' for CedarTree and '.dct' for DartsCloneTree" << endl;
            return 1;
        }
    }

    if (namelist && write_dict)
        cedar = cedar_check;

    // initializing class for entity finding
    figa_cedar gazeteer(print_bool,overlapping,autocomplete,many,return_all,spellcheck,in_bytes);
	
	// check for errors within parameters
	if (error > 0) {
		if (error != 2)
			std::cerr << "FIGA ERROR: One dictionary file must be specified!" << std::endl;
		else
			print_help(); // tisk help
		return 1;
	}
    if(cedar_check != cedar){
        cerr << "Input and output dictionary must be the same type! " << endl;
        return 1;
    }	

    // loading dictionary
    if(namelist){ // from namelist file
	    gazeteer.LoadItems(data,values,dict_file_name);
		if(cedar){
			if( dict_cedar.build(data.size(),(const char**)data.data(),NULL,values.data())){
				cerr << "FAIL BUILD DICTIONARY" << endl;
				return 1;
			}
		}else{
			try {
				dict_darts.build(data.size(),(const char**)data.data(),NULL,values.data());
			} catch (Darts::Details::Exception e) {
				std::cerr << e.what() << std::endl;	
				return 1;

			}
		}
	}else{ // from saved dictionary file
		if(cedar)
			dict_cedar.open(dict_file_name);
        else
			dict_darts.open(dict_file_name);
    }

    // saving dictionary to file
    if(write_dict_file){
		if(cedar)
			dict_cedar.save(write_dict_file);
		else
			dict_darts.save(write_dict_file);
	}
    // call function is dependent on dictionary type(cedar,darts), input type(stdin,file) and type of processing(spellcheck on/off)
	if(file){ // input from file
		input.open (file_name, std::ifstream::in);
		if(spellcheck){ // processing with spellcheck
			if(cedar) // cedar dicitonary
				gazeteer.spell_KBlookup<dict_type_cedar>(dict_cedar,input);
			else // darts dicitonary
				gazeteer.spell_KBlookup<dict_type_darts>(dict_darts,input);
		}else{ // processing without spellcheck
			if(cedar) // cedar dicitionary
				gazeteer.KBlookup<dict_type_cedar>(dict_cedar,input);
			else // darts dictionary
				gazeteer.KBlookup<dict_type_darts>(dict_darts,input);
		}
	}else{ // input from 
		if(spellcheck){ // spellcheck on
			if(cedar) // cedar dicitonary
				gazeteer.spell_KBlookup<dict_type_cedar>(dict_cedar,cin);
			else // darts dictioanry
				gazeteer.spell_KBlookup<dict_type_darts>(dict_darts,cin);
		}else{ // spellcheck off
			if(cedar) // cedar dictionary
				gazeteer.KBlookup<dict_type_cedar>(dict_cedar,cin);
			else // darts dicitonary
				gazeteer.KBlookup<dict_type_darts>(dict_darts,cin);
		}
	}
	
    // freeing memory
	for(unsigned int i = 0; i < data.size();i++){
		delete(data.data()[i]);
	}
	return 0;
}

