import os
import ecg
import sys

def main():
    for subdir, dirs, files in os.walk('svd'):
        for file in files:
            if file.endswith('.svd'):
                full_path = os.path.join(subdir, file)
                try:
                    ecg.generate_code(full_path, None, 'mcu_support')
                except Exception:
                    sys.stderr.write('--- Caught exception while parsing {} ---\n'.format(full_path))
                    raise


if __name__ == '__main__':
    main()
