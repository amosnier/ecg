import argparse


def vectors_from_stream(stream):
    vectors_found = False
    vectors = []
    max_handler_name_len = 0
    for line in stream:

        # Search for '__Vectors       DCD     __initial_sp                      ; Top of Stack'

        parts = line.split(sep=';')
        if not parts:
            continue
        words = parts[0].split()
        if not words:
            continue
        if not vectors_found:
            if not words[0] == '__Vectors':
                continue
            assert words[1] == 'DCD' and words[2] == '__initial_sp'
            vectors_found = True
            continue

        # At this point, we know we are in the vector area, and there are words,
        # which means we are on an exception/interrupt, or at the end.

        if words[0] == '__Vectors_End':
            break
        assert words[0] == 'DCD' and len(words) == 2
        vectors.append((words[1], parts[1].strip()))
        max_handler_name_len = max(max_handler_name_len, len(words[1]))

    return vectors, max_handler_name_len


def main():
    parser = argparse.ArgumentParser(description='Generate C++ source code files from an ARM assembly startup file.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('startup_file', help='startup (assembly) file')
    parser.add_argument('destination', help='destination directory')
    args = parser.parse_args()
    startup_file = args.startup_file
    print('source file: {}'.format(startup_file))
    with open(startup_file) as file:
        vectors = vectors_from_stream(file)
    print(vectors)


if __name__ == '__main__':
    main()
