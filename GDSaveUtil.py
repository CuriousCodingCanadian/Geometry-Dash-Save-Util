import base64
import os
import struct
import sys
import traceback
import zlib
import shutil
from xml.dom import minidom

__version__ = '1.2.0'

match sys.platform:
    case 'win32':
        BASE_PATH = os.getenv('LocalAppData')
    case 'darwin':
        BASE_PATH = os.path.expanduser('~/Library/Application Support')
    case 'linux':
        BASE_PATH = os.path.expanduser('~/.local/share/steam/steamapps/compatdata/322170/pfx/drive_c/Users/steamuser/AppData/Local/GeometryDash')
    

POSSIBLE_FILE_NAMES = ['CCGameManager.dat', 'CCLocalLevels.dat', 'CCGameManager', 'CCLocalLevels', 'CCGameManager.dat.xml', 'CCLocalLevels.dat.xml', 'CCGameManager.xml', 'CCLocalLevels.xml', 'GDSaveUtil.py', 'README.md']

SAVE_FILE_NAME = ['CCGameManager.dat', 'CCLocalLevels.dat']
SAVE_FILE_PATH = os.path.join(os.getenv('LocalAppData'), 'GeometryDash')

prettify_xml = True

MENU_OPTIONS = ['E', 'D', 'O', 'T']

def print_menu() -> None:
    print(f'Geometry Dash Savefile Util v{__version__} by WEGFan (modified by ees4.dev)\n'
          '\n'
          'Original decryption code obtained from https://pastebin.com/JakxXUVG by Absolute Gamer\n'
          '\n'
          'This utility is for encrypting and decrypting Geometry Dash save files.\n'
          'Run this script in an empty directory or one used with this script previously.\n'
          'After editing the decrypted save files, use this script to encrypt them back.\n'
          '\n'
          '1. [E]ncrypt\n'
          '2. [D]ecrypt\n'
          '3. [O]pen save file folder\n'
          f'4. [T]oggle prettify XML after decrypt [Current: {"ON" if prettify_xml else "OFF"}]'
          '5. [S]ave changes to save file folder\n'
          '6. [Q]uit\n')
    
def toggle_pretty_xml() -> None:
    global prettify_xml
    prettify_xml = not prettify_xml
    print(f'Prettify XML after decrypt {"enabled" if prettify_xml else "disabled"}.')


def xor_bytes(data: bytes, value: int) -> bytes:
    return bytes(map(lambda x: x ^ value, data))

def encrypt_xml_save(xml_data: bytes) -> bytes:
    compressed_data = zlib.compress(xml_data)
    data_crc32 = zlib.crc32(xml_data)
    data_size = len(xml_data)

    compressed_data = (b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x00\x0b' +  # gzip header
                        compressed_data[2:-4] +
                        struct.pack('I I', data_crc32, data_size))
    
    encoded_data = base64.b64encode(compressed_data, altchars=b'-_')
    encrypted_data = xor_bytes(encoded_data, 11)

    return encrypted_data

def decrypt_gzip_save(encrypted_data: bytes) -> bytes:
    decrypted_data = xor_bytes(encrypted_data, 11)
    decoded_data = base64.b64decode(decrypted_data, altchars=b'-_')
    decompressed_data = zlib.decompress(decoded_data[10:], -zlib.MAX_WBITS)
    
    return decompressed_data

def yes_no():
    print('Do you want to continue? [y/n]')
    if input('>>> ').lower() != 'y':
        sys.exit(0)

def encrypt_directory(directory: str) -> None:
    for save_file in SAVE_FILE_NAME:
        SAVE_FILE_NAME_STRIPPED = save_file.removesuffix('.dat')
        try:
            print(f'Encrypting {SAVE_FILE_NAME_STRIPPED}.xml...')

            if os.path.exists(os.path.join(directory, f'{save_file}')):
                print('This will overwrite the existing encrypted save file.')
                yes_no()

            with open(f'{SAVE_FILE_NAME_STRIPPED}.xml', 'rb') as f:
                decrypted_data = f.read()

            encrypted_data = encrypt_xml_save(decrypted_data)

            with open(os.path.join(directory, save_file), 'wb') as f:
                f.write(encrypted_data)

            print('Done!')
        except FileNotFoundError as err:
            print(f"Can't find {SAVE_FILE_NAME_STRIPPED}.xml in current folder!")
        except Exception as err:
            print(f'Failed to encrypt {SAVE_FILE_NAME_STRIPPED}.xml!')
            traceback.print_exc()

def decrypt_directory(directory: str) -> None:
    for save_file in SAVE_FILE_NAME:
        SAVE_FILE_NAME_STRIPPED = save_file.removesuffix('.dat')
        try:
            print(f'Decrypting {save_file}...')
            if os.path.exists(os.path.join(directory, f'{SAVE_FILE_NAME_STRIPPED}.xml')):
                print('This will overwrite the existing decrypted save file.')
                yes_no()

            with open(save_file, 'rb') as f:
                encrypted_data = f.read()

            decrypted_data = decrypt_gzip_save(encrypted_data)

            if prettify_xml:
                try:
                    xml_dom = minidom.parseString(decrypted_data)
                    decrypted_data = xml_dom.toprettyxml(indent='\t', encoding='utf-8')
                except Exception as err:
                    print(f'Failed to prettify {SAVE_FILE_NAME_STRIPPED}.xml! File will remain unprettified.')

            with open(f'{SAVE_FILE_NAME_STRIPPED}.xml', 'wb') as f:
                f.write(decrypted_data)

            print('Done!')
        except FileNotFoundError as err:
            print(f"Can't find {save_file}.xml in save file folder!")
        except Exception as err:
            print(f'Failed to decrypt {save_file}!')
            traceback.print_exc()
def main():
    print_menu()

    WORKING_DIR = os.getcwd()

    FILES_GOOD = False

    for file_name in os.listdir(WORKING_DIR):
        if file_name not in POSSIBLE_FILE_NAMES:
            break
    else:
        FILES_GOOD = True

    if not FILES_GOOD:
        print('This directory has extra files. It is recommended to run this script in an empty directory or one previously used for this script.')
        yes_no()

    if not os.listdir(WORKING_DIR) == []:
        print('The current working directory is not empty. It is recommended to run this script in an empty directory.')
        yes_no()

    while True:
        print()
        s = input('>>> ')
        print()

        match s:
            case num if num in ['1', '2', '3', '4']:
                index = int(num)
            case char if char.upper() in MENU_OPTIONS:
                index = MENU_OPTIONS.index(char.upper()) + 1
            case _:
                print('Invalid input!')
                continue
        
        match index:
            case 1:  # encrypt
                encrypt_directory(WORKING_DIR)
            case 2:  # decrypt
                decrypt_directory(WORKING_DIR)
            case 3:  # open save file folder
                os.startfile(SAVE_FILE_PATH)
            case 4:  # toggle pretty xml
                toggle_pretty_xml()
            case 5:
                for save_file in SAVE_FILE_NAME:
                    shutil.copy(os.path.join(WORKING_DIR, save_file), os.path.join(SAVE_FILE_PATH, save_file))
                print('Changes saved to save file folder!')
            case 6:
                sys.exit(0)
            case _:
                print('Invalid option selected (this should never show)!')
                continue


if __name__ == '__main__':
    try:
        main()
    except (EOFError, KeyboardInterrupt) as err:
        sys.exit()
