#include "figa_cedar.h"

/* Name:        sortFunc
 * Class:       none
 * Purpose:     compare two structures, compares their string parts in 
 *              unsigned char comparision, because of darts-clone
 * Parameters:  a       -first object
 *		        b      - second object
 * Returns:     True if first object is smaller then second.
 * Remarks:     
 */
bool sortfunc(loaded_items* a,loaded_items* b){
	int i = 0;
	while(true){
		if(a->s[i]!=b->s[i])
			return ((unsigned char) (a->s[i]) < (unsigned char) (b->s[i]));
		if((a->s[i] == '\0') || (b->s[i] =='\0'))
			return true;
		i++;
	}
};

/* Name:        checkFileNameForDictType
 * Class:       none
 * Purpose:     check file name for extension to determine type of dictionary
 * Parameters:  file       - file name
 *		        cedar      - return parameter to indicate type of dicitionary
 * Returns:     Nothing (constructor).
 * Remarks:     Only to launch fsa contructor.
 */

int figa_cedar::checkFileNameForDictType(const char* file,bool &cedar){
    int length = strlen(file);
    
    // .ct == .CedarTree
    if( file[length-3] == '.' &&
        file[length-2] == 'c' &&
        file[length-1] == 't'){
        cedar = true;
        return 0;
    }
    
    // .dct == .DartsCloneTree
    if( file[length-4] == '.' &&
        file[length-3] == 'd' &&
        file[length-2] == 'c' &&
        file[length-1] == 't'){
        cedar = false;
        return 0;
    }
    
    return 1;
}

/* Name:        delimiter
 * Class:       figa_cedar
 * Purpose:     function for identifying delimiters
 * Parameters:  c   - char to check
 * Returns:     true if given symbol is delimiter
 * Remarks:     
 */
bool figa_cedar::delimiter(char c){
    // checks if symbol is white space, punctiation or control character
    if(isspace(c) || ispunct(c) || iscntrl(c))
        return true;
    return false;
}


/* Name:        get_numbers
 * Class:       figa_cedar
 * Purpose:     parse string for associated values
 * Parameters:  s       - string to process
 *		        values  - vector to fill with associated values
 * Returns:     Nothing. Fills vector values with associated values for entity
 * Remarks:     Only to launch fsa contructor.
 */
void figa_cedar::get_numbers(string s, vector<int> &values){
    char c = '0';
    int number = 0;
    // numbers are saved backwards
    // except numbers may also occur 'N' character in string 's'
    // numbers are pop back from string, and added together until symbol ';'
    // then the final number is saved in vector and it resets and continue until
    // there is somethin to read
    while(!(s.empty())){ 
        while(!(s.empty()) && c != ';'){
            if (isdigit(c))
                number =number * 10 + c - '0';

            c = s.back();
            s.pop_back();
        }
        if(s.empty() && c != ';'){
            if (isdigit(c))
                number =number * 10 + c -'0';
        }
        else{
            c = s.back();
            s.pop_back();
        }
        values.push_back(number);
        number = 0;
    }
}

/* Name:        LoadItems
 * Class:       figa_cedar
 * Purpose:     load entities and their associated values from file, and fills given vectors with it
 * Parameters:  data       - vector for entities
 *		        values     - vector for associated value
 *              file       - input file
 * Returns:     True if succesfull.
 * Remarks:     It loads input by chunks of 10000 symbols and parse it by line. It take one lane,
 *              and from the end goes until it hits delimiter, it takes that suffix and process it
 *              for associated values, then it takes the prefix, and depending on the number of
 *              associated values, it copies the prefix and add suffix of '\1', wher with each 
 *              string is associated one value and then it both save to vector, sort it and save to 
 *              coresponding return vectors
 */
bool figa_cedar::LoadItems(vector<char*> & data,vector<int> &values, char* file){
    ifstream in;
    bool end = false;   
    char c;
    string line;
    string numbers_str;
    vector<int> numbers;
    stringstream s;
    int index = 0;
    int count_val,i = 0;
    char tmp[10000];

    // vector to hold entites and values before sorting
    loaded_items *ptr;    
    vector<loaded_items*> tmp_data;

    // open input file
    in.open(file,std::ifstream::in);
    if(in){
        in.read(tmp,10000);
        s << tmp;
    }
    else{
        return false;
    }

    // counting bytes/words
    int long count = 0,count_w = 0;

    
    for(int i = 0; (!end);i++){// while the EOF wasnt read
        bool el =false;
        line.clear();
        while(!el){// while EOF or '\n' wasnt read
            if(index >= in.gcount()){// everything loaded was processed
                if(in.good()){   
                    in.read(tmp,10000);
                    index = 0;
                }else{
                    end =true;
                    tmp[0] = EOF;
                    index = 0;
                }
            }
            c = tmp[index];
            index++;
            count++;
            if((c == '\n') || (c == EOF) || end){ //end of line
                el = true;
                if(line.size() > 0){
                    c = line.back();
                    while(isspace(c) && line.size() > 0){ // skipp all whitespace at the end
                        line.pop_back();
                        c = line.back();                    
                    }
                    numbers_str.clear();
                    while((isdigit(c) || c == ';' || c == 'N') && line.size() > 0){ // cut out the value numbers
                        line.pop_back();    
                        numbers_str.push_back(c);
                        c = line.back();                    
                    }
                    while(isspace(c) && line.size() > 0){ // skipp the rest of the white space at the end
                        line.pop_back();
                        c = line.back();                    
                    }
                    if(line.size()>0){
                        count_w++;
                        // processing values
                        numbers.clear();
                        get_numbers(numbers_str,numbers);

                        for(count_val = 0;count_val < numbers.size();count_val++){
                            if(count_val == 0){ // for the first value create normal entity entry
                                ptr = (loaded_items*) new loaded_items; // create new instance for sorting
                                ptr->s =(char*) new char[line.size()+1]; // allocate memory for entities name
                                ptr->i = numbers.at(count_val); // get value
                                memcpy(ptr->s,line.data(),line.size()); // copy entity to allocated memory
                                (ptr->s)[line.size()] = '\0'; // add end of string
                                tmp_data.push_back(ptr); // save at to the vector
                            }else{ // for every other than first create special entry
                                ptr = (loaded_items*) new loaded_items;
                                ptr->s =(char*) new char[line.size()+1+2+count_val];//(sizeof(char)*(line.size()+1));
                                memcpy(ptr->s,line.data(),line.size());
                                // bonus values are separated by 2 symbols of '\1'
                                for(i = 0; i< 1+2+count_val;i++){
                                    (ptr->s)[line.size()+i] = 1;
                                }
                                ptr->i = numbers.at(count_val);
                                (ptr->s)[line.size()+2+count_val] = '\0';
                                tmp_data.push_back(ptr);
                            }
                            
                        }
                    }
                }
                line.clear();
                
            }
            line.push_back(c); // add symbol to the line string    
        }
    }
    // closing input
    in.close();
    
    // sort vector of string and values
    std::sort(tmp_data.begin(),tmp_data.end(),sortfunc);

    char * last_s = (char*)"";
    int last_i;
    // split vector into two vector of char* and int
    vector<loaded_items*>::iterator it_li;
    for(it_li = tmp_data.begin(); it_li < tmp_data.end();it_li++){
        if(strcmp(last_s,(*it_li)->s) == 0) // erase duplicates, cedar cant handle it
            if(last_i == (*it_li)->i)
                continue;  
        data.push_back((*it_li)->s);
        values.push_back((*it_li)->i);
        last_s = (*it_li)->s;
        last_i = (*it_li)->i;
    }
    tmp_data.clear();
    return true;
}

// 
/* Name:        print_values
 * Class:       figa_cedar
 * Purpose:     print values stored in vector with ';' as delimiter
 * Parameters:  values     - vector of associated values to print
 * Returns:     Nothing.
 * Remarks:     
 */
void figa_cedar::print_values(vector<int> &values){
    if(!this->print)
        return;
    int tmp = -1;

    std::vector<int>::iterator ent_it;
    
    // sort it so no duplicates will be print
    sort(values.begin(),values.end());
    bool first_start = true;

    for(ent_it = values.begin();ent_it < values.end();ent_it++) {
        if(tmp == *ent_it)
            continue; // dont print duplicates
        else
            tmp = *ent_it;
        if(!first_start)
            cout << ";";
        else
            first_start = false;
        cout << *ent_it;
    } 
}
