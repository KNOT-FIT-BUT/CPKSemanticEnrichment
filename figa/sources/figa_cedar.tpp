/*** 
 *** Author: Andrej Rajcok
 *** Email: xrajco00@stud.fit.vutbr.cz
 *** Popis: Implementacia triedy figa_cedar pre vyhladavanie entit v texte
 ***/


/* Name:        get_values
 * Class:       figa_cedar
 * Purpose:     extract all associated values stored in subtree 
 * Parameters:  dict    - dictionary
 *              def     - root node of subtree
 *              res_val - return vector for associated values
 *              first   - indicator if this is first call
 * Returns:     Nothing
 * Remarks:     values are storred in child nodes of tree, with offset of 2 symbols of '\1'     
 *              for every value, there is another child with added offset of '\1'
 */
template <typename dict_T>
void figa_cedar::get_values(dict_T &dict,std::size_t def,vector<int>&res_val,bool first){
    int value = 0;
    std::size_t pos = 0;
    std::size_t from = def;
    string tmp;

    // first iteration
    if(first){
        string tmp_string = "\1";
        value = dict.traverse(tmp_string.data(),from,pos = 0);
        if(value == NO_KEY)
            return;  
    }

    char c[2] ;
    c[1] = 0;
    c[0] = 1;
    from = def;
    pos = 0;
    value = dict.traverse(c,from,pos);
    // get value
    if(value > NO_VALUE){
        res_val.push_back(value);
    } 
    // get the rest of the values
    if(value >= NO_VALUE){
        get_values<dict_T>(dict,from,res_val,false);
    }
}


/* Name:        autocomplete
 * Class:       figa_cedar
 * Purpose:     extract posible entities from subtree 
 * Parameters:  s       - string to find the subtree
 *              dict    - dictionary 
 *              def     - root node of subtree, if 0, s is used
 *              res     - return vector for entites with their values
 *              dept    - flag to stop it from going into subtree of associated values
 * Returns:     Nothing
 * Remarks:     it apllies all possible char symbols to the node, if traverse is succesfull     
 *              it recursively call itself, with updated def and symbol appended to s
 *              it keep looking until it reaches limit of entites or until it tries 
 *              all posible symbols 
 */
template <typename dict_T>
void figa_cedar::autocomplete(string s, dict_T &dict,std::size_t def,vector<t_search_res> &res,int depth){
    int value = 0;
    std::size_t pos = 0;
    std::size_t from = def;
    string tmp;
    char c[2] ;
    c[1] = 0;
    int j = 0;
    t_search_res tmp_res;
    vector<int> tmp_values;
    std::size_t tmp_from = 0,tmp_pos = 0;
    // def node is 0, use given string
    if(def == 0){
        value = dict.traverse(s.data(),def,pos);
        if(value < -1)
            return;
    }
    // check if we arent too deep in the way for stored bonus values
    if(depth == 2)
        return;
        
    // try to add every possible symbol, j is set to 30, but can be lowered
    for(j=30;j<256;j++){
        if(res.size() >= this->many && !this->r_all){
            return;
        }
        from = def;
        c[0] = j;
        pos = 0;
        value = dict.traverse(c,from,pos);
        if(value > NO_VALUE){ // adding succesfull, child exist and has associated value
            tmp = s;
            tmp.push_back(j);
            tmp_values.clear();
            tmp_from = from;
            get_values<dict_T>(dict,tmp_from,tmp_values);
            tmp_values.push_back(value);
            tmp_res.res_str = tmp;
            tmp_res.res_val = tmp_values;
            res.push_back(tmp_res);
        }
        if(value == NO_VALUE){ // adding succesfull, but child has no associated value
            tmp = s;
            tmp.push_back(j);
        }
        if(value >= NO_VALUE){ // recursively try to find childs of succesfull adding
            if(j == 1)
                autocomplete<dict_T>(tmp,dict,from,res,depth+1);
            else
                autocomplete<dict_T>(tmp,dict,from,res);
        }
    }
}


/* Name:        check_and_save_value
 * Class:       figa_cedar
 * Purpose:     check th eend of the word in dictionary if it has associated values
 *              and if it is followed by another word
 * Parameters:  dict        - dictionary 
 *              from        - current node
 *              res_val_from- return vector of nodes with possible entities
 *              cont_from   - return vector of nodes with associated values
 *              value       - value to check
 * Returns:     Nothing
 * Remarks:      
 */
template <typename dict_T>
void figa_cedar::check_and_save_value(dict_T &dict,size_t from,vector<std::size_t> &res_val_from,vector<std::size_t> &cont_from,int value){
    size_t pos;
    if(value >=0 || value == NO_VALUE){
        if(value >= 0)
            cont_from.push_back(from);
        value= dict.traverse(" ",from,pos = 0);
        if(value >=0 || value == NO_VALUE){
            res_val_from.push_back(from);
        }
    }  
}


/* Name:        spellcheck_generate
 * Class:       figa_cedar 
 * Purpose:     generates UTF-8 symbol by trying all posible symbols for given byte of UTF-8 symbol  
 * Parameters:  dict        - dictionary 
 *              from        - current node in tree
 *              res_val_from- return vector for nodes with possible entities
 *              cont_from   - return vector for nodes with associated values
 *              utflevel    - defines hte position of current byte in generated UTF-8 symbol
 *              rest        - rest of the word to append after symbol
 * Returns:     Nothing
 * Remarks:     positve utf-level indicates first call and defines number of bytes in symbol
 *              negatie bytes indicates generating non first bytes and byte position in UTF8 symbol
 */
template <typename dict_T>
void figa_cedar::spellcheck_generate(dict_T &dict,size_t from,vector<std::size_t> &res_val_from,vector<std::size_t> &cont_from,int utflevel,const char* rest){
    // default range for non first symbol
    int min_i = UTF_8_0;
    int max_i = UTF_8_1; 

    // setting the range for first symbol
    if(utflevel == 1){
        min_i = UTF_8_1;
        max_i = UTF_8_2;
        utflevel = -1;
    }
    if(utflevel == 2){
        min_i = UTF_8_2;
        max_i = UTF_8_3;
        utflevel = -2;
    }
    if(utflevel == 3){
        min_i = UTF_8_3;
        max_i = UTF_8_4;
        utflevel = -3;
    }

    int value;
    size_t pos;
    char ap[2];
    ap[1] = 0;
    size_t backup = from;
    
    // iterate through all possible symbols
    for(int j=min_i; j< max_i; j++){
        from = backup;
        ap[0] = j;
        value = dict.traverse(ap,from,pos = 0);

        if(value >=0 || value == NO_VALUE){
            if(utflevel){
                spellcheck_generate(dict,from,res_val_from,cont_from,utflevel+1,rest);
            }else{
                // end of symbol, check if the whole word exist
                value = dict.traverse(rest,from,pos = 0);
                check_and_save_value(dict,from,res_val_from,cont_from,value);
            }
        }
    }
}


/* Name:        spellcheck
 * Class:       figa_cedar
 * Purpose:     spellcheck given word, from all given nodes, then it updates this nodes
 *              with all new reached nodes 
 * Parameters:  dict        - dictionary 
 *              s           - word to spellcheck
 *              res_val_from- vector all all curent position in tree
 *              cont_from   - return vector for nodes with associated values
 * Returns:     Nothing
 * Remarks:     It extract all the current nodes from res_val_from, and then it fills up wiht new
 *              it tries 3 elemetary operation, insert, delete, replace wiht all posible UTF-8 symbols
 *              and then tries swapping neighboors, if whole word can be aplied for 
 *              node, it adds it for possible divided word 
 */
template <typename dict_T>
void figa_cedar::spellcheck(dict_T &dict,string s,vector<std::size_t> &res_val_from,vector<std::size_t> &cont_from){
    int i = 0,j=0,k[3]={0},ii = 0;
    string tmp = s;
    string tmp_i[3];
    std::size_t pos = 0;
    int value = 0;
    int i_max = 0;
    std::size_t from = 0;
    vector<std::size_t>::iterator it_from;
    vector<std::size_t> from_vec;
    from_vec = res_val_from;
    res_val_from.clear();
    string backup = s;
    int orig_s_size = s.size();

    // for all nodes tries all symbols
    for(it_from = from_vec.begin(); it_from < from_vec.end();it_from++){
        s = backup; // correct word to default form
        from = *it_from;

        // get the position of error, if there is none, add end of the word to posible nodes
        dict.traverse(s.data(),from,pos=0);
        i_max =  s.size();
        if(pos >= s.size()){
            res_val_from.push_back(from);
            // add word if no error was found
            int g = dict.traverse(" ",from,pos=0);
            if(g >= NO_VALUE)
                res_val_from.push_back(from);
        }
        from = *it_from;

        tmp_i[2] = s;
        // try to replace every symbol
        for(i =0;i < i_max;i = i+1+ii){
            tmp = tmp_i[2];
            ii = 0;
            
            // erase whole utf8 symbol, so the whole symbol can be replaced by symbols or various length
            if(!(tmp.at(i) < UTF_8_0)){
                if(tmp.at(i) < UTF_8_1)
                    tmp.erase(i,1);
                else{
                    if(tmp.at(i) < UTF_8_2)
                        tmp.erase(i,2);
                    else{    
                        tmp.erase(i,3);
                        ii++;
                    }
                    ii++;
                }
                ii++;
            }
            const char* rest = &(tmp[i+1]);
            // ASCII
            for(j=30;j<128;j++){
                from = *it_from;
                tmp[i] = j;
                value = dict.traverse(tmp.data(),from,pos = 0);
                check_and_save_value(dict,from,res_val_from,cont_from,value);
            }
            for(int j=1;j <=3;j++){
                from = *it_from;
                tmp[i] = 0;
                value = dict.traverse(tmp.data(),from,pos = 0);
                spellcheck_generate(dict,from,res_val_from,cont_from,j,rest);
            }
        }
        
        if(orig_s_size == 1){
            i = 1; // no point in deleting the only character
        }else{
            i=0;
        }
        // try to delete character
        for(;i<i_max;i++){
            tmp = s;
            from = *it_from;
            
            // deleting whole UTF8 symbols, 1 - 4 bytes
            if(tmp.at(i) < UTF_8_0)
                tmp.erase(i,1);
            else{
                if(tmp.at(i) < UTF_8_1)
                    tmp.erase(i,2);
                else{
                    if(tmp.at(i) < UTF_8_2)
                        tmp.erase(i,3);
                    else{    
                        tmp.erase(i,4);
                        i++;
                    }
                    i++;
                }
                i++;
            }
            value = dict.traverse(tmp.data(),from,pos = 0);
            check_and_save_value(dict,from,res_val_from,cont_from,value);
        }
        ii=0;
        // try to insert characters
        for(i=0;i<i_max+1;i=i+1+ii){
            tmp = s;
            j = 30;
            tmp.insert(i,((const char*)&j),1);
            const char *rest = &(tmp[i+1]);
            for(j=30;j<128;j++){
                from = *it_from;
                tmp[i] = j;
                value = dict.traverse(tmp.data(),from,pos = 0);
                check_and_save_value(dict,from,res_val_from,cont_from,value);
            }
            
            for(int j=1;j <=3;j++){
                from = *it_from;
                tmp[i] = 0;
                value = dict.traverse(tmp.data(),from,pos = 0);
                spellcheck_generate(dict,from,res_val_from,cont_from,j,rest);
            }
            ii = 0;
            // skipping whole UTF8 symbols, no point inserting symbol in the middle of UTF8 symbol
            if(s[i] >= UTF_8_1)
                ii++;
            if(s[i] >= UTF_8_2)
                ii++;
            if(s[i] >= UTF_8_3)
                ii++;
        }
    }    
}

/* Name:        get_autocomplete_results
 * Class:       figa_cedar
 * Purpose:     extract result of loaded words, tries to find the longest 
 *              sequence with associated value 
 * Parameters:  current     - structure with queue of processed words   
 *              dict        - dictionary 
 * Returns:     Nothing
 * Remarks:     It goes from back, rewrinting stored values with stop value,
 *              until it finds value biiger then NO_VALUE, then it write out
 *              all associated values with that node and then it writes out 
 *              start and end and goes fromt the start of the queue, printing
 *              out words until it reaches stop value, while printing
 *              it rewrites value to stop value, then it deletes  words 
 *              from start until it reaches only non stop value 
 */
template <typename dict_T>
void figa_cedar::get_autocomplete_results(t_status &current,dict_T &dict){
    int value = NO_ENTITY;
    std::size_t pos = 0;
    std::size_t from = 0;

    t_context ent_val;

    vector<t_search_res> entities;
    vector<t_search_res>::iterator it_sea;
    vector<std::size_t >::iterator ent_it;
    vector<string>::iterator it_str;

    string s;
    s.clear();

    // procces words in reverse order, label word NO_ENTITY until word with positive value or value NO_VALUE is found, then break
    for(list<t_context>::reverse_iterator it_con = current.value.rbegin(); it_con != current.value.rend();++it_con){
        if(it_con->value >= 0 || it_con->value == NO_VALUE){
            break;
        }
        else{
           it_con->value = NO_ENTITY;
        }
    }
    // create string for autocomplete, use number of values in context, stop at first value NO_ENTITY or end of vector, save the context
    // of the last word, label all words with NO_ENTITY, label first word with NO_ENTITY value NO_KEY as indent
    for(list<t_context>::iterator it = current.value.begin(); it != current.value.end();it++){
        if(it->value == NO_ENTITY){
            it->value = NO_KEY;
            break;
        }
        // get context, only contex of the last processed word will be saved
        value = it->value;
        from = it->from;
        
        it->value = NO_ENTITY;
        s.append(it->word);
        s.append(" ");
    }

    // erase last s.append(" ");
    if(!s.empty()){ 
        s.pop_back();
    }

    // need to autocomplete?, evidently we need
    if(value >= 0){
        vector<int> tmp_values;
        get_values<dict_T>(dict,from,tmp_values);
        tmp_values.push_back(value);
        t_search_res tmp_res;        
        tmp_res.res_str = s;
        tmp_res.res_val = tmp_values;
        entities.push_back(tmp_res);
    }
    
    if(value != NO_ENTITY){
            autocomplete<dict_T>(s,dict,from,entities);            
    }


    // print out loaded entities
    for(it_sea = entities.begin();it_sea < entities.end();it_sea++){                   
        if(this->print){
            cout << it_sea->res_str << "\t";
        }
        print_values(it_sea->res_val);
        if(this->print){
            cout << endl;
        }
    }

    // if overlaping erase only first word, else, the whole entity

    if(!current.value.empty()){
        current.value.erase(current.value.begin());
    }
    if(!this->overlapping){
        while(!current.value.empty() && current.value.front().value == NO_ENTITY && value != NO_ENTITY){
            current.value.erase(current.value.begin());
        }
        if(!current.value.empty()){
            current.value.front().value = NO_ENTITY;
        }
    }        
}

/* Name:        get_spellcheck_ressults
 * Class:       figa_cedar
 * Purpose:     extract result of loaded words, tries to find the longest 
 *              sequence with associated value 
 * Parameters:  current     - structure with queue of processed words   
 *              dict        - dictionary 
 * Returns:     Nothing
 * Remarks:     It goes from back, rewrinting stored values with stop value,
 *              until it finds value biiger then NO_VALUE, then it write out
 *              all associated number with that node or nodes 
 *              star and end and goes fromt the start of the queue, printing
 *              out words until it reaches stop value, while printing
 *              it rewrites value to stop value, then it deletes  words 
 *              from start until it reaches only non stop value 
 */
template <typename dict_T>
void figa_cedar::get_spellcheck_results(t_status &current,dict_T &dict){
    int value = NO_ENTITY;
    t_context ent_val ;
    std::size_t pos = 0;
    std::size_t end = 0;
    std::size_t count = 0;
    
    for(list<t_context>::reverse_iterator it_con = current.value.rbegin(); it_con != current.value.rend();++it_con){
        end = it_con->end;
        if(it_con->value >= 0){
            ent_val = *it_con;
            vector<int> ent_values;
            get_values<dict_T>(dict,ent_val.from,ent_values);
            ent_values.push_back(it_con->value);
            print_values(ent_values);
            if(this->print){
                cout << "\t" << current.value.front().start << "\t" << end  << "\t" ;
            }
            break;
        }else{
            if(it_con->value == SPELL_VALUES){
                vector<std::size_t>::iterator it_from;
                vector<int> spell_values;
                for(it_from = it_con->spell_from.begin();it_from < it_con->spell_from.end();it_from++){
                    get_values<dict_T>(dict,*it_from,spell_values);
                    spell_values.push_back(dict.traverse("",*it_from,pos = 0));
                }                
                print_values(spell_values);
                if(this->print){
                    cout << "\t" << current.value.front().start << "\t" << end  << "\t" ;
                }
                break;   
            }else{
                it_con->value = NO_ENTITY;
            }
        }
    }

    for(list<t_context>::iterator it = current.value.begin(); it != current.value.end();it++){
        if(it->value == NO_ENTITY){
            it->value = NO_KEY; // 
            break;
        }else{
            it->value = NO_ENTITY;
        }
        if(this->print){
            cout << it->word << " ";
            count++;
        }
    }
    if(this->print && count > 0){
        cout << endl;
    }
    if(!current.value.empty()){
        value = current.value.front().value;
        current.value.erase(current.value.begin());
    }
    if(!this->overlapping){
        while(!current.value.empty() && current.value.front().value == NO_ENTITY && value == NO_ENTITY){
            current.value.erase(current.value.begin());
        }
        if(!current.value.empty()){
            current.value.front().value = NO_ENTITY;
        }
    }
}

/* Name:        get_results
 * Class:       figa_cedar
 * Purpose:     extract result of loaded words, tries to find the longest 
 *              sequence with associated value 
 * Parameters:  current     - structure with queue of processed words   
 *              dict        - dictionary 
 * Returns:     Nothing
 * Remarks:     It goes from back, rewrinting stored values with stop value,
 *              until it finds value biiger then NO_VALUE, then it write out
 *              all associated values with that node and then it write out 
 *              star and end and goes fromt the start of the queue, printing
 *              out words until it reaches stop value, while printing
 *              it rewrites value to stop value, then it deletes  words 
 *              from start until it reaches only non stop value 
 */
template <typename dict_T>
void figa_cedar::get_results(t_status &current,dict_T &dict){
    int value = NO_ENTITY;
    t_context ent_val ;
    std::size_t pos = 0;
    std::size_t end = 0;
    std::size_t count = 0;

    // find longest sequence with assocaited value, rewrites non assocaited values to stop value
    for(list<t_context>::reverse_iterator it_con = current.value.rbegin(); it_con != current.value.rend();++it_con){
        end = it_con->end;
        if(it_con->value >= 0){
            ent_val = *it_con;
            vector<int> ent_values;
            get_values<dict_T>(dict,ent_val.from,ent_values);
            ent_values.push_back(it_con->value);
            print_values(ent_values);
            if(this->print){
                cout << "\t" << current.value.front().start << "\t" << end  << "\t" ;
            }
            break;
        }
        else{
           it_con->value = NO_ENTITY;
        }
    }

    // print out the word of entity
    for(list<t_context>::iterator it = current.value.begin(); it != current.value.end();it++){
        if(it->value == NO_ENTITY){
            it->value = NO_KEY;
            break;
        }else{
            it->value = NO_ENTITY;
        }
        if(this->print){
            if (count > 0)
                cout << " ";
            cout << it->word;
            count++;
        }
    }
    // end of print out
    if(this->print && count > 0){
        cout << endl;
    }

    // clearing the start of hte queue
    if(!current.value.empty()){
        value = current.value.front().value;
        current.value.erase(current.value.begin());
    }
    // clerst queue fromt he rest of the entity
    if(!this->overlapping){
        while(!current.value.empty() && current.value.front().value == NO_ENTITY && value == NO_ENTITY){
            current.value.erase(current.value.begin());
        }
        if(!current.value.empty()){
            current.value.front().value = NO_ENTITY;
        }
    }
}



/* Name:        get_entity
 * Class:       figa_cedar
 * Purpose:     call one of the results retrieved based on class parameteres 
 * Parameters:  current     - structure with queue of processed words   
 *              dict        - dictionary 
 * Returns:     Nothing
 * Remarks:     It restart the queue at the end, by defaulting flags in current
 */
template <typename dict_T>
void figa_cedar::get_entity(t_status &current,dict_T &dict){
    if(!current.value.empty()){
        if(this->spell){
            get_spellcheck_results<dict_T>(current,dict);
        }else{
            if(this->autocomp){ // autocomplete
                //cout << current.words.back() << "||" << current.words.front() << endl;
                get_autocomplete_results<dict_T>(current,dict);
            }else{ // geting entiy and associated values form dictionary
                get_results<dict_T>(current,dict);
            }
        }
    }
    current.from = 0;
    current.load = false;
    current.found = false;
    current.spell = false;
}


/* Name:        spell_KBlookup
 * Class:       figa_cedar
 * Purpose:     process input text and identifies possible entities in them
 *              and check for spellcheck mistakes 
 * Parameters:  dict        - dictionary 
 *              ifs         - input stream
 * Returns:     Nothing
 * Remarks:     it parses input stream into words, then ti tries to aply them
 *              from current node, if it fails it tries to spellcheck the word,
 *              if it fails too it tries to find entity in the loaded words,
 *              after retrieving it, it process again the rest of loaded words
 *              to find entity 
 */
template <typename dict_T>
void figa_cedar::spell_KBlookup(dict_T &dict, istream &ifs){

    
    list<t_context>::iterator it;
    vector<std::size_t>::iterator it_from;

    // status of processing
    t_status current;

    // variables for work with dictionary
    string word;
    int value = 0;
    std::size_t pos = 0;
    vector<std::size_t> spell_from;
    
    // flags
    bool start = true;    
    bool cant_load_more = true;
    bool word_is_uri = false;
    
    // initializing structure that holds temporary context and laoded words
    current.from = 0;
    current.load = true;
    current.found = false;
    current.value.clear();
    current.spell = 0;

    // initialinzg structure tah hold context of the word
    t_context cont;
    cont.start = 0;
    cont.end = 0;
    cont.from = 0;
    cont.value = 0;
    cont.word.clear(); 
    
    // counting bytes
    std::size_t  count = 1;
                   
    while(true){ // while there is somthing to read
        //cout <<current.load << "  " << current.from << "  ";
        
        if(current.value.empty()){ // everything processed, load more
            current.load = true;
            if(!ifs.good())
                break;
        }
        word.clear();
        char c;
        if(current.load && ifs.good()){ // need to load more
            cont.start = count;
            word_is_uri = false;
            while(true){ // loading new word
                c = ifs.get();
                // always increase if counting in bytes, increase if ASCII symbol
                if(this->bytes || (unsigned char) c < UTF_8_0 || (unsigned char) c >= UTF_8_1){
                    count++;                            // increase if c is 11xxxxxx or higher -> utf-8 symbol begin
                }
                //cout << c << "  ";
                if ((word.size() == 4 && word == "http" || word.size() == 5 && word == "https") && c == ':') {
                    word_is_uri = true;
                }
                
                if (!ifs.good()) {
                    break;
                } else if (word_is_uri) {
                    if (delimiter(c) && ! ispunct(c)) { // end at delimiter if is not a punctiation
                        break;
                    }
                } else if (delimiter(c)) { // end at delimiter
                    if (word.size() == 1 && c == '.') { // append dot to an initial
                        word.push_back(c);
                    }
                    break;
                }
                word.push_back(c);
            }
            //cout << word << current.spell << "||";
            if(word.size() > 0){ // proccesing new word
                // save context
                cont.end = count-2;
                cont.word = word;
                current.found = false;
                if(!current.spell){
                    // updates the vector of nodes to spellcheck from            
                    spell_from.clear();
                    spell_from.push_back(current.from);

                    // try to aply loaded word in dictionary
                    value = cont.value = dict.traverse(word.data(),current.from,pos = 0);

                    //save context
                    cont.from = current.from;

                    if(cont.value >=0){ //for spellcheck, we assume there is no error, so when entity is found, no spellchecking
                        current.found = true;
                    }
                    
                    //sve the context of current word
                    current.value.push_back(cont);
                                        
                    // try to go on next word
                    if(value >=0 || value == NO_VALUE)
                        value = dict.traverse(" ",current.from,pos = 0);
                }else{
                    // updates the vector of nodes to spellcheck from
                    spell_from.clear();
                    spell_from = current.spell_from;
                    
                    // clear reached spellcheck nodes
                    current.spell_from.clear();
                    cont.spell_from.clear();
                    
                    // flags for indicating if value was found
                    int flag_for_value_found = NO_KEY;
                    int flag_for_next_word = NO_KEY;

                    for(it_from = spell_from.begin(); it_from < spell_from.end(); it_from++){
                        std::size_t tmp_from = *it_from;
                        // try to aply loaded word in dictionary
                        value = cont.value = dict.traverse(word.data(),tmp_from,pos = 0);
                        if(cont.value >= 0){
                            current.found = true;
                            flag_for_value_found = SPELL_VALUES;
                            cont.spell_from.push_back(tmp_from);
                        }
                        
                        // try to go on next word
                        if(value >=0 || value == NO_VALUE)
                            value = dict.traverse(" ",tmp_from,pos = 0);
                        //cout << ":" << value;
                        if(value == NO_VALUE || value >= 0){// add candidates for longer entity
                            flag_for_next_word = NO_VALUE;
                            current.spell_from.push_back(tmp_from);
                        }
                    }
                    cont.value = flag_for_value_found;
                    value = flag_for_next_word;
                    current.value.push_back(cont);
                }

                current.spell_from = spell_from;
                current.value.back().spell_from.clear();
                spellcheck<dict_T>(dict,cont.word,current.spell_from,current.value.back().spell_from);
                if(!current.spell_from.empty()){
                    current.spell = true;
                    continue;
                }else{
                    get_entity<dict_T>(current,dict);
                }
            }
        }else{ // processing already loaded word in context current
            // defaulting context
            current.from = 0;
            current.load = true;
            current.found = false;
            current.spell = false;
            cant_load_more = true;
            while(!current.value.empty() && cant_load_more){ // end of file, but words are loaded, we need to process them
                cant_load_more = !ifs.good();
                for(it=current.value.begin();it!=current.value.end();it++){ // iterating through loaded words
                    //cout << it->word  << " ==="<<endl;
                    current.found = false;
                    if(!current.spell){ 
                        spell_from.clear();
                        spell_from.push_back(current.from);           
                        // try to loaded word in dictionary
                        it->value = dict.traverse(it->word.data(),current.from,pos = 0);
                        value = it->value;
                        //save context
                        it->from = current.from;
                        if(it->value >=0){ //for spellcheck, we assume there is no error, so when entity is found, no spellchecking
                            current.found = true;
                        }
                        // try to go on next word
                        if(value == NO_VALUE || value >= 0)
                            value = dict.traverse(" ",current.from,pos = 0);
                    }else{
                        spell_from.clear();
                        spell_from = current.spell_from; 
                        current.spell_from.clear();
                        it->spell_from.clear();
                        int flag_for_value_found = NO_KEY;
                        int flag_for_next_word = NO_KEY;
                        for(it_from = spell_from.begin(); it_from < spell_from.end(); it_from++){
                            std::size_t tmp_from = *it_from;
                            // try to loaded word in dictionary
                            value = dict.traverse(word.data(),tmp_from,pos = 0);
                            if(value >= 0){
                                current.found = true;
                            }
                            if(value >= 0){
                                flag_for_value_found = SPELL_VALUES;
                                it->spell_from.push_back(tmp_from);
                            }
                            // try to go on next word
                            if(value == NO_VALUE || value >=0)
                                value = dict.traverse(" ",tmp_from,pos = 0);
                            if(value == NO_VALUE || value >= 0){// add candidates for longer entity
                                flag_for_next_word = NO_VALUE;
                                current.spell_from.push_back(tmp_from);
                            }
                        }
                        it->value = flag_for_value_found;
                        value = flag_for_next_word;
                    }
                    it->spell_from.clear();
                    current.spell_from = spell_from;
                    spellcheck<dict_T>(dict,it->word,current.spell_from,it->spell_from);
                    if(!it->spell_from.empty())
                        it->value = SPELL_VALUES;
                    if(!current.spell_from.empty()){
                        current.spell = true;
                        if(cant_load_more && value == NO_VALUE){// if there is no more words to load
                            get_entity<dict_T>(current,dict);
                            break;
                        }else{
                            continue;
                        }
                    }else{
                        get_entity<dict_T>(current,dict);
                        break;
                    }
                }
            } 
        }
    }
}
// main function for extracting entiteis, it takes dictionary nad input file as parameters
// it load words, try to find possible matches, if it si possible match, it is stored in t_status structure
// it keeps loading words while it is possible match, when the fisrt word that isnt possible match is found
// it call get_results(), to extract longest possible entity from loaded words in t_status structure

/* Name:        KBlookup
 * Class:       figa_cedar
 * Purpose:     process input text and identifies possible entities in them 
 * Parameters:  dict        - dictionary 
 *              ifs         - input stream
 * Returns:     Nothing
 * Remarks:     it parses input stream into words, then it tries to aply them
 *              from current nod, if it fails it tries to find entity in the 
 *              loaded words, after retrieving it, it process again the rest 
 *              of loaded wordsto find entity 
 */
template <typename dict_T>
void figa_cedar::KBlookup(dict_T &dict, istream &ifs){
    list<t_context>::iterator it;
    t_status current;
    // variables for work with dictionary
    string word;
    string punctiation, word_delimiter;
    const string space = " ";
    int value = 0;
    std::size_t pos = 0;
    
    // flags
    bool start = true;    
    bool cant_load_more = true;
    bool word_is_uri = false;
    
    // initializing structure that holds temporary context and laoded words
    current.from = 0;
    current.load = true;
    current.found = false;
    current.value.clear();

    // initialinzg structure tah hold context of the word
    t_context cont;
    cont.start = 0;
    cont.end = 0;
    cont.from = 0;
    cont.value = 0;
    cont.word.clear(); 
    
    // counting bytes
    std::size_t  count = 1;
                   
    while(true){ // while there is somthing to read
        //cout <<current.load << "  " << current.from << "  ";
        
        if(current.value.empty()){ // everything processed, load more
            current.load = true;
            if(!ifs.good())
                break;
        }
        
        word.clear();
        char c;
        if(current.load && ifs.good()){ // need to load more
            cont.start = count;
            word_is_uri = false;
            while(true){ // loading new word
                c = ifs.get();
                // always increase if counting in bytes, increase if ASCII symbol
                if(this->bytes || (unsigned char) c < UTF_8_0 || (unsigned char) c >= UTF_8_1){
                    count++;                            // increase if c is 11xxxxxx or higher -> utf-8 symbol begin
                }
                //cout << c << "  ";
                if ((word.size() == 4 && word == "http" || word.size() == 5 && word == "https") && c == ':') {
                    word_is_uri = true;
                }
                
                if (!ifs.good()) {
                    break;
                } else if (word_is_uri) {
                    if (delimiter(c) && ! ispunct(c)) { // end at delimiter if is not a punctiation
                        break;
                    }
                } else if (delimiter(c)) { // end at delimiter
                    break;
                }
                word.push_back(c);
            }
            //cout << word << " " << endl;
            if(word.size() > 0){ // proccesing new word
                // save context
                cont.end = count-2;
                cont.word = word;
            
                // try to loaded word in dictionary
                cont.value = dict.traverse(word.data(),current.from,pos = 0);
                value = cont.value;
                //save context
                cont.from = current.from;
                current.value.push_back(cont);
                // try to go on next word
                if(value == NO_VALUE || value >= 0){
                    if(ispunct(c)) {
                        punctiation = c;
                        word_delimiter = punctiation + space;
                        value = dict.traverse(word_delimiter.c_str(),current.from,pos = 0);
                        if(value != NO_VALUE && value < 0) {
                            word_delimiter = punctiation;
                            current.from = cont.from;
                            value = dict.traverse(word_delimiter.c_str(),current.from,pos = 0);
                        }
                    } else {
                        value = dict.traverse(" ",current.from,pos = 0);
                    }
                }
                if(value == NO_VALUE || value >= 0){ // word was found in dict, with or without associated value
                    continue;
                }else{ // word wasnt found in dictionary
                    get_entity<dict_T>(current,dict);
                }
            }

        }else{ // processing already loaded word in context current
            // defaulting context
            current.from = 0;
            current.load = true;
            cant_load_more = true;
            while(!current.value.empty() && cant_load_more){ // end of file, but words are loaded, we need to process them
                cant_load_more = !ifs.good();
                for(it=current.value.begin();it!=current.value.end();it++){ // iterating through loaded words
                    //cout << it->word  << " ==="<<endl;
                    // is it in dictionary
                    value = dict.traverse(it->word.data(),current.from,pos = 0);
            
                    // save context
                    it->value = value;
                    it->from = current.from;

                    // is there another word in dictionary?
                    if(value >=0 || value == NO_VALUE)
                        value = dict.traverse(" ",current.from,pos = 0);   
                    //cout << value << " \\\\" <<endl;     
                    if(value == NO_VALUE || value >= 0){ // there is another word in dictionary
                        if(cant_load_more && value == NO_VALUE){// if there is no more words to load
                            get_entity<dict_T>(current,dict);
                            break;   
                        }else
                            continue;
                    }else{
                        get_entity<dict_T>(current,dict);
                        break;
                    }
                }
            } 
        }
        
      //  cout << current.load << " | " << current.words.back() << " | " << value << ":"<<len << ":" << pos<< endl;
    }
}
