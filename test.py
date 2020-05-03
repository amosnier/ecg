import os
import ecg


def main():
    for subdir, dirs, files in os.walk('svd'):
        for file in files:
            if file.endswith('.svd'):
                full_path = os.path.join(subdir, file)
                print(full_path)
                ecg.generate_code(full_path, None, 'mcu_support')


if __name__ == '__main__':
    main()
