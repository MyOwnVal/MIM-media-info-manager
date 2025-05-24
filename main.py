import os
from tkinter import Tk, filedialog

from mutagen._file import File as MutagenFile
from mutagen.id3 import ID3
from mutagen.mp3 import MP3

# Constants
COVER_ART_DIR = 'cover_art'
AUDIO_FILE_PATTERN = '*.mp3 *.flac *.ogg *.m4a *.mp4 *.wav'
AUDIO_EXTENTIONS = set(AUDIO_FILE_PATTERN.replace('*', '').split())
IMAGE_FILE_PATTERN = '*.jpg *.jpeg *.png'

# Ensure cover_art directory exists
os.makedirs(COVER_ART_DIR, exist_ok=True)


def copy_cover_art(file_path, silent=False):
    """Copy and save the first APIC frame (cover art) from the audio file."""

    try:
        audio_file = MutagenFile(file_path)
        if not audio_file or not audio_file.tags:
            if not silent:
                print(f'[SKIP] No tags in "{file_path}"')
            return False

        apic_frames = (
            audio_file.tags.getall('APIC')
            if hasattr(audio_file.tags, 'getall')
            else []
        )
        if not apic_frames:
            if not silent:
                print(f'[SKIP] No cover art in "{file_path}"')
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
            print(f'[COPY] Cover art saved to "{output_path}"')
        return True

    except Exception as error_info:
        print(f'[ERROR] Failed on "{file_path}": {error_info}')
        return False


def delete_cover_art(file_path):
    """Delete the first APIC frame (cover art) from the audio file."""

    try:
        audio_file = MutagenFile(file_path, easy=False)
        if not audio_file or not audio_file.tags:
            print(f'[SKIP] No tags to remove from "{file_path}"')
            return

        if hasattr(audio_file.tags, 'delall'):
            audio_file.tags.delall('APIC')
            audio_file.save()
            print(f'[DELETE] Cover art removed from "{file_path}"')
        else:
            print(
                f'[SKIP] Tag format does not support cover deletion: '
                f'"{file_path}"'
            )
    except Exception as error_info:
        print(
            f'[ERROR] Could not delete cover art from "{file_path}": '
            f'{error_info}'
        )


def extract_cover_art(file_path):
    """Copy and remove cover art from the audio file."""

    was_copied = copy_cover_art(file_path, silent=True)
    if not was_copied:
        print(f'[SKIP] No cover art in "{file_path}"')
        return
    delete_cover_art(file_path)


def replace_cover_art(file_path, image_path):
    """Replace any existing cover art of the audio file with a new one."""

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
                type=3,
                desc='Cover',
                data=image_data,
            )
        )

        audio_file.save(v2_version=3)

        print(f'[REPLACE] Cover art replaced in "{file_path}"')

    except Exception as error_info:
        print(f'[ERROR] Failed on "{file_path}": {error_info}')


def select_audio_files():
    Tk().withdraw()
    file_paths = filedialog.askopenfilenames(
        filetypes=[('Audio Files', AUDIO_FILE_PATTERN)]
    )
    Tk().destroy()
    return file_paths


def select_audio_directory():
    Tk().withdraw()
    dir_path = filedialog.askdirectory()
    Tk().destroy()
    return dir_path


def select_image_file():
    Tk().withdraw()
    file_path = filedialog.askopenfilename(
        filetypes=[('Image Files', IMAGE_FILE_PATTERN)]
    )
    Tk().destroy()
    return file_path


def get_audio_files_from_directory(directory_path):
    return [
        os.path.join(directory_path, entry)
        for entry in os.listdir(directory_path)
        if entry.lower().endswith(AUDIO_EXTENTIONS)
    ]


def close_application():
    from sys import exit

    print('[QUIT] Application closed.')
    exit()


def main():
    operation_options = {
        'COPY': 'c',
        'DELETE': 'd',
        'EXTRACT': 'e',
        'REPLACE': 'r',
        'QUIT': 'q',
    }
    target_options = {'DIRECTORY': 'd', 'FILE': 'f'}

    print()
    print('Choose an operation:')
    print(f'[{operation_options["COPY"]}] COPY cover art')
    print(f'[{operation_options["DELETE"]}] DELETE cover art')
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
        folder_path = select_audio_directory()
        selected_files = get_audio_files_from_directory(folder_path)
    elif selected_target == target_options['FILE']:
        selected_files = select_audio_files()
    else:
        print('Invalid target type.')
        return

    if not selected_files:
        print('No MP3 files selected.')
        return

    if selected_operation == operation_options['COPY']:
        for file_path in selected_files:
            copy_cover_art(file_path)
    elif selected_operation == operation_options['DELETE']:
        for file_path in selected_files:
            delete_cover_art(file_path)
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
