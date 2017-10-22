/***
 *** Author: Jan Havran
 *** Email: xhavra13@stud.fit.vutbr.cz
 ***/
#ifndef FIGA_H
#define FIGA_H

#include <vector>

#include "figa_cedar.h"

class marker : public figa_cedar
{
	private:
		dict_type_darts dict_darts;
		dict_type_cedar dict_cedar;
		bool cedar;
		std::vector <std::string> split_lines(std::string str);
		std::string _lookup_string(std::string input_string);
	public:
		marker(bool print_bool = true, bool over = false,
			bool autocom = false, int m = 5,
			bool returnall = false, bool spellche = false,
			bool in_bytes = false);
		bool load_dict(std::string dict_file_name);
		std::string lookup_string(std::string input_string);
		std::string auto_lookup_string(std::string input_string);
};

#endif //FIGA_H

