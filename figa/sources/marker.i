%module marker
%{
#include "figa_cedar.h"
#include "figa.h"
%}

%include "std_string.i"

class marker : public cedar_figa
{
	public:
		marker(bool print_bool = true, bool over = false,
			bool autocom = false, int m = 5,
			bool returnall = false, bool spellche = false,
			bool in_bytes = false);
                bool load_dict(std::string dict_file_name);

//		std::string lookup();
//		std::string lookup_file(std::string input_name);
		std::string lookup_string(std::string input_string);

		// AUTOCOMPLETE:
//		std::string auto_lookup(unsigned int many);
//		std::string auto_lookup_file(std::string input_name, unsigned int many);
		std::string auto_lookup_string(std::string input_string);
};

