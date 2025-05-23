import os
from tkinter import Tk, filedialog

from mutagen.id3 import ID3
from mutagen.mp3 import MP3

# Constants
COVER_ART_DIR = 'cover_art'
MP3_EXTENSION = '.mp3'
IMAGE_EXTENSIONS = '*.jpg *.jpeg *.png'

# Ensure cover_art directory exists
os.makedirs(COVER_ART_DIR, exist_ok=True)

# Hide Tkinter root window
Tk().withdraw()


def copy_cover_art(file_path, silent=False):
    """Copy and save the first APIC frame (cover art) from an MP3 file."""
    try:
        audio_file = MP3(file_path, ID3=ID3)
        if audio_file.tags is None:
            if not silent:
                print(f'[SKIP] No ID3 tags in {file_path}')
            return False

        apic_frames = audio_file.tags.getall('APIC')
        if not apic_frames:
            if not silent:
                print(f'[SKIP] No cover art in {file_path}')
            return False

        cover_frame = apic_frames[0]
        image_extension = cover_frame.mime.split('/')[-1]
        file_basename = os.path.splitext(os.path.basename(file_path))[0]
        output_path = os.path.join(
            COVER_ART_DIR, f'{file_basename}.{image_extension}'
        )

        with open(output_path, 'wb') as output_file:
            output_file.write(cover_frame.data)

        if not silent:
            print(f'[COPY] Cover art saved to {output_path}')
        return True

    except Exception as error_info:
        print(f'[ERROR] Failed on {file_path}: {error_info}')
        return False


def extract_cover_art(file_path):
    """Copy and remove cover art from the MP3 file."""
    was_copied = copy_cover_art(file_path, silent=True)
    if not was_copied:
        print(f'[SKIP] No cover art in {file_path}')
        return

    try:
        audio_file = MP3(file_path, ID3=ID3)

        if audio_file.tags is None:
            print(f'[SKIP] No ID3 tags to remove from {file_path}')
            return

        audio_file.tags.delall('APIC')
        audio_file.save()
        print(f'[EXTRACT] Cover art removed from {file_path}')
    except Exception as error_info:
        print(
            f'[ERROR] Could not remove cover art from {file_path}: '
            f'{error_info}'
        )


def replace_cover_art(file_path, image_path):
    """Replace any existing cover art of an MP3 file with a new one."""
    from mutagen.id3._frames import APIC

    try:
        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()

        image_extension = os.path.splitext(image_path)[1][1:].lower()
        mime_type = f'image/{image_extension}'

        audio_file = MP3(file_path, ID3=ID3)

        if audio_file.tags is None:
            audio_file.add_tags()
            assert audio_file.tags is not None

        audio_file.tags.delall('APIC')
        audio_file.tags.add(
            APIC(
                encoding=3,
                mime=mime_type,
                type=3,  # front cover
                desc='Cover',
                data=image_data,
            )
        )

        audio_file.save(v2_version=3)

        print(f'[REPLACE] Cover art replaced in {file_path}')

    except Exception as error_info:
        print(f'[ERROR] Failed on {file_path}: {error_info}')


def select_mp3_files():
    return filedialog.askopenfilenames(
        filetypes=[('MP3 Files', MP3_EXTENSION)]
    )


def select_mp3_directory():
    return filedialog.askdirectory()


def select_image_file():
    return filedialog.askopenfilename(
        filetypes=[('Image Files', IMAGE_EXTENSIONS)]
    )


def get_mp3_files_from_directory(directory_path):
    return [
        os.path.join(directory_path, entry)
        for entry in os.listdir(directory_path)
        if entry.lower().endswith('.mp3')
    ]


def close_application():
    from sys import exit

    print('[QUIT] Application closed.')
    exit()


def main():
    operation_options = {
        'COPY': 'c',
        'EXTRACT': 'e',
        'REPLACE': 'r',
        'QUIT': 'q',
    }
    target_options = {'DIRECTORY': 'd', 'FILE': 'f'}

    print()
    print('Choose an operation:')
    print(f'[{operation_options["COPY"]}] COPY cover art')
    print(f'[{operation_options["EXTRACT"]}] EXTRACT cover art')
    print(f'[{operation_options["REPLACE"]}] REPLACE cover art')

    while True:
        selected_operation = (
            input(
                f'Enter one option ({operation_options["QUIT"]} - to quit): '
            )
            .strip()
            .lower()
        )

        if selected_operation == operation_options['QUIT']:
            close_application()
        elif selected_operation in operation_options.values():
            break
        else:
            print('Invalid selection.')

    print()
    print('Choose target type:')
    print(f'[{target_options["DIRECTORY"]}] Directory')
    print(f'[{target_options["FILE"]}] File(s)')

    while True:
        selected_target = (
            input(
                f'Enter one option ({operation_options["QUIT"]} - to quit): '
            )
            .strip()
            .lower()
        )

        if selected_target == operation_options['QUIT']:
            close_application()
        elif selected_target in target_options.values():
            break
        else:
            print('Invalid selection.')

    if selected_target == target_options['DIRECTORY']:
        folder_path = select_mp3_directory()
        selected_files = get_mp3_files_from_directory(folder_path)
    elif selected_target == target_options['FILE']:
        selected_files = select_mp3_files()
    else:
        print('Invalid target type.')
        return

    if not selected_files:
        print('No MP3 files selected.')
        return

    if selected_operation == operation_options['COPY']:
        for file_path in selected_files:
            copy_cover_art(file_path)
    elif selected_operation == operation_options['EXTRACT']:
        for file_path in selected_files:
            extract_cover_art(file_path)
    elif selected_operation == operation_options['REPLACE']:
        image_path = select_image_file()
        if not image_path:
            print('No image selected.')
            return
        for file_path in selected_files:
            replace_cover_art(file_path, image_path)


if __name__ == '__main__':
    main()
