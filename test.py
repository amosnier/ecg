import os
import ecg
import sys


def main():
    for subdir, dirs, files in os.walk('svd'):
        for in_file in files:
            if in_file.endswith('.svd'):
                out_dir = os.path.join('generated', os.path.relpath(subdir, 'svd'), os.path.splitext(in_file)[0])
                os.makedirs(out_dir, exist_ok=True)
                full_in_path = os.path.join(subdir, in_file)
                try:
                    ecg.generate_code(full_in_path, os.path.join(out_dir, 'mcu.h'), 'mcu_support')
                except Exception:
                    sys.stderr.write('--- Caught exception while parsing {} ---\n'.format(full_in_path))
                    raise


if __name__ == '__main__':
    main()
