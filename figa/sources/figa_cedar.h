/*** 
 *** Author: Andrej Rajcok
 *** Email: xrajco00@stud.fit.vutbr.cz
 *** Popis: Header pre triedu figa_cedar, ktora sluzi na vyhladavanie entit v texte pomocou KB
 ***/

#ifndef FIGA_CEDAR_H
#define FIGA_CEDAR_H

#include <vector>
#include <fstream>
#include <iostream>
#include <sstream>
#include <unistd.h>
#include <algorithm>
#include "cedar.h"
#include "darts.h"
#include <cstdint>
#include <list>

typedef Darts::DoubleArrayImpl<void,void,int32_t,void> dict_type_darts;
typedef cedar::da<int> dict_type_cedar;

using namespace std;
typedef struct items{
    char* s;  
    int i;
}loaded_items;

#define NO_KEY -2
#define NO_VALUE -1
#define NO_ENTITY -3
#define SPELL_VALUES -4
#define UTF_8_1 0b11000000
#define UTF_8_2 0b11100000
#define UTF_8_3 0b11110000
#define UTF_8_4 0b11111000
#define UTF_8_0 0b10000000

class figa_cedar{
    public:

    typedef struct context{
        int value; // return value
        std::size_t from; // return node
        std::size_t start; // index of start
        std::size_t end; // index of end
        bool capital; // is first word capital
        string word; // word itself
        vector<std::size_t > spell_from; // return nodes after spellcheck    
    }t_context;

    typedef struct res{
        list<t_context> value; // vector of values of traversing words
        std::size_t from; // index of nod in trie
        bool load; // load next word
        bool found; // was found
        vector<std::size_t> spell_from; //current node after spellcheck
        bool spell; // are we spellchecking?
    }t_status;

    typedef struct auto_res{
        string res_str;
        vector<int> res_val;
    }t_search_res;

    bool print = true;
    bool overlapping = false;
    bool autocomp = false;
    bool r_all = false;
    bool bytes = false;
    bool spell = false;
    int many = 5;
    figa_cedar(){};
    figa_cedar(bool print_bool,bool over,bool autocom,int m,bool returnall,bool spellche,bool in_bytes):
    print(print_bool),
    overlapping(over),
    autocomp(autocom),
    spell(spellche),
    many(m),
    r_all(returnall),
    bytes(in_bytes)
    {}


    static int checkFileNameForDictType(const char* file,bool &cedar);
	
    // function for identifying delimiters
    // return true, if given symbol is delimiter
    bool delimiter(char c);

    // values of these childs are values associated with entity
    // function for proccesing numbers at the end of line in namelist
    // it returns filled vector of int
    void get_numbers(string s, vector<int> &values);


    // function to load items from namelist
    // it take input file, read a line,erase white space at the end, procces values at the end,
    // erase rest of white space at the end, store it in vector, and sort it out,
    // so dictioanry can be build rom it    
    // it takes vector of char pointer and vector of integer, after proccesing whole file
    // fills them with entities and their respective values
    bool LoadItems(vector<char*> & data,vector<int> &values, char* file);


    // function to extract all values associated with entity
    // values are storred in child nodes of tree, with offset of 5 symbols of '\1'
    // for every value, the is another child with added offset of '\1'
    // it assumes, that starting offset of 4 '\1' is already traversed
    template <typename dict_T>
    void get_values(dict_T &dict,std::size_t def,vector<int>&res_val,bool first = true);
    
    //
    void print_values(vector<int> &values);

    // autocomplete function,it takes starting node, if node is 0, it takes string,
    // it traverse to the end iof string, and then try and traverse for every possible symbol
    // if it travels succesfuly, it recursively continue, if traverse return valid value, it stores the value and string
    // if it traverse 4 times with symbol '\1' it returns as that is values of another entity 
    template <typename dict_T>
    void autocomplete(string s, dict_T &dict,std::size_t def,vector<t_search_res> &res,int depth = 0);


    // check provided value and finds out if there is any words afterwards
    template <typename dict_T>
    void check_and_save_value(dict_T &dict,size_t from,vector<std::size_t> &res_val_from,vector<std::size_t> &cont_from,int value);

    // generates all posible UTF-8 and find them in dictionary from provide node
    template <typename dict_T>
    void spellcheck_generate(dict_T &dict,size_t from,vector<std::size_t> &res_val_from,vector<std::size_t> &cont_from,int utflevel,const char*rest);
    

    // spellchecking funcnction, it takes string that should be spellcheck, dictionary to check against
    // and vector of string and int to fil for results
    // it first try to change every symbo0l with every possible alternatives, one at the time
    // then try erase symbols, one at the time
    // then it try to insert all posible symbols
    template <typename dict_T>
    void spellcheck(dict_T &dict,string s,vector<std::size_t> &res_val, vector<std::size_t > &cont_from);


    // function for extracting result from t_status structure, that contains
    // vector of string representing all loaded words
    // it then try to find the longest sequence with associated valid value
    // and then it extract the rest of the values for that entity
    template <typename dict_T>
    void get_autocomplete_results(t_status &current,dict_T &dict);


    // function for extracting result from t_status structure, that contains
    // vector of string representing all loaded words
    // it then try to find the longest sequence with associated valid value
    // and then it extract the rest of the values for that entity
    template <typename dict_T>
    void get_results(t_status &current,dict_T &dict);

    template <typename dict_T>
    void get_spellcheck_results(t_status &current,dict_T &dict);
    //
    template <typename dict_T>
    void get_entity(t_status &current,dict_T &dict);

    // function for spellchecking look up
    template <typename dict_T>
    void spell_KBlookup(dict_T &dict, istream &ifs);
    // main function for extracting entiteis, it takes dictionary nad input file as parameters
    // it load words, try to find possible matches, if it si possible match, it is stored in t_status structure
    // it keeps loading words while it is possible match, when the fisrt word that isnt possible match is found
    // it call get_results(), to extract longest possible entity from laoded words in t_status structure
    template <typename dict_T>
    void KBlookup(dict_T &dict, istream &ifs);
};

#include "figa_cedar.tpp"

#endif //FIGA_CEDAR_H

