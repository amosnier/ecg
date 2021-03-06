import os
import ecg
import sys
import argparse
import pathlib


def main():
    parser = argparse.ArgumentParser(description='Test ecg.')
    parser.add_argument('-c', '--compiler', help='C++ header file name')
    args = parser.parse_args()
    compiler = args.compiler
    os.chdir(pathlib.Path(__file__).parent.absolute())
    os.makedirs('build', exist_ok=True)
    num_files = 0
    for subdir, dirs, files in os.walk('svd'):
        for in_file in files:
            if in_file.endswith('.svd'):
                out_dir = os.path.join('generated', os.path.relpath(subdir, 'svd'), os.path.splitext(in_file)[0])
                os.makedirs(out_dir, exist_ok=True)
                full_in_path = os.path.join(subdir, in_file)
                try:
                    full_out_path = os.path.join(out_dir, 'mcu.h')
                    ecg.generate_code(full_in_path, full_out_path, 'mcu_support', compiler)
                    num_files += 1
                except Exception:
                    sys.stderr.write('--- Caught exception while parsing {} ---\n'.format(full_in_path))
                    raise
    print('generated {} files'.format(num_files))


if __name__ == '__main__':
    main()
