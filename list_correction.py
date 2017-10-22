import argparse

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', help='Prints all entities without disambiguation.')

    arguments = parser.parse_args()

    content = open(arguments.input).read()
    content = content.split('\n')
    duplicities = []

    with open(arguments.input, 'w') as f:
        for line in content:
            if line:
                splitted = line.split('\t')
                if not splitted[0] in duplicities:
                    f.write(line + '\n')
                    duplicities.append(splitted[0])
