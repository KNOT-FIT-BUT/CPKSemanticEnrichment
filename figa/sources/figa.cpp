#include "figa.h"

marker::marker(bool print_bool, bool over, bool autocom, int m,
	bool returnall, bool spellche, bool in_bytes)
:figa_cedar(print_bool, over, autocom, m, returnall, spellche, in_bytes)
{
}

std::vector<std::string> marker::split_lines(std::string str)
{
	std::stringstream ss(str);
	std::vector<std::string> ret;
	std::string line;

	while (std::getline(ss, line)) {
		ret.push_back(line);
	}

	return ret;
}

bool marker::load_dict(std::string dict_file_name)
{
        if (figa_cedar::checkFileNameForDictType(dict_file_name.c_str(), cedar))
		return false;

	if (cedar)
		return dict_cedar.open(dict_file_name.c_str()) ? false : true;
	else
		return dict_darts.open(dict_file_name.c_str()) ? false : true;
}

std::string marker::_lookup_string(std::string input_string)
{
	std::stringstream buffer;
	std::streambuf *old_sbuf;
	std::istringstream ss(input_string);

	/* Presmerovani vystupu do streamu, abychom
	 * mohli vratit vysledek jako retezec, jelikoz
	 * KBlookup tiskne vysledky na stdout */
	old_sbuf = std::cout.rdbuf(buffer.rdbuf());
	if (cedar)
		KBlookup<dict_type_cedar>(dict_cedar, ss);
	else
		KBlookup<dict_type_darts>(dict_darts, ss);
	std::cout.rdbuf(old_sbuf);

        return buffer.str();
}

std::string marker::lookup_string(std::string input_string)
{
	std::string buffer;
	std::vector<std::string> lines;
	std::string ret;

        buffer = _lookup_string(input_string);

	lines = split_lines(buffer);
	for (int i = 0; i < lines.size(); i++) {
		ret.append(lines[i]);
		ret.append("\tF\n");
	}

	return ret;
}

std::string marker::auto_lookup_string(std::string input_string)
{
	std::string buffer;
	std::vector<std::string> lines;
	std::string ret;

        buffer = _lookup_string(input_string);

	lines = split_lines(buffer);
	for (int i = 0; i < lines.size(); i++) {
		ret.append(lines[i]);
		ret.append("\n");
	}

	return ret;
}

