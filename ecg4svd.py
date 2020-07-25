import argparse
import xmltodict
import coding4svd
import tempfile
import os
import pathlib


def generate_code(svd_file, h_file, namespace, compiler):
    print('{}\t\t->\t{}'.format(svd_file, h_file))
    with open(h_file, 'w') as output_stream:
        with open(svd_file) as file:
            doc = xmltodict.parse(file.read())
        coder = coding4svd.Coder4Svd(svd_file, h_file, output_stream, namespace)
        coder.emit_mcu(doc['device'])
    if compiler:
        tmp_dir = tempfile.gettempdir()
        src_file_name = os.path.join(tmp_dir, 'test.cpp')
        h_file_name = os.path.basename(h_file)
        with open(src_file_name, 'w') as src_file:
            src_file.write('#include "{}"\n'.format(h_file_name))
        compile_string = '{} -std=c++17 -o {} -c {} -I {}'
        object_file = os.path.join(tmp_dir, 'test.o')
        command = compile_string.format(compiler, object_file, src_file_name, pathlib.Path(h_file).parent)
        print('Running: {}'.format(command))
        assert not os.system(command)
        print('Compilation successful\n')


def main():
    parser = argparse.ArgumentParser(description='Generate a C++ header file from an ARM Cortex SVD file.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('svd_file', help='SVD file')
    parser.add_argument('-o', '--output', required=True, help='C++ header file name')
    parser.add_argument('-n', '--namespace', help='C++ namespace', default='mcu_support')
    parser.add_argument('-c', '--compiler', help='C++ header file name')
    args = parser.parse_args()
    generate_code(args.svd_file, args.output, args.namespace, args.compiler)


if __name__ == '__main__':
    main()
