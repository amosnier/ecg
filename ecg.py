import argparse
import xmltodict
import sys
import coding


def generate_code(svd_file, h_file, namespace):
    print('{}\t\t->\t{}'.format(svd_file, h_file))
    with open(h_file, 'w') as output_stream:
        with open(svd_file) as file:
            doc = xmltodict.parse(file.read())
        coder = coding.Coder(svd_file, h_file, output_stream, namespace)
        coder.emit_mcu(doc['device'])


def main():
    # noinspection PyTypeChecker
    parser = argparse.ArgumentParser(description='Generate C++ header file from ARM Cortex SVD file.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('svd_file', help='SVD file')
    parser.add_argument('-o', '--output', required=True, help='C++ header file name')
    parser.add_argument('-n', '--namespace', help='C++ namespace', default='mcu_support')
    args = parser.parse_args()
    svd_file = args.svd_file
    h_file = args.output
    namespace = args.namespace
    generate_code(svd_file, h_file, namespace)


if __name__ == '__main__':
    main()
