import os
from tkinter import StringVar, Tk, filedialog, messagebox, ttk

from mutagen._file import File as MutagenFile
from mutagen.id3 import ID3
from mutagen.id3._frames import APIC
from mutagen.mp3 import MP3

# Constants
COVER_ART_DIR = 'cover_art'
AUDIO_FILE_PATTERN = '*.mp3 *.flac *.ogg *.m4a *.mp4 *.wav'
AUDIO_EXTENSIONS = tuple(AUDIO_FILE_PATTERN.replace('*', '').split())
IMAGE_FILE_PATTERN = '*.jpg *.jpeg *.png'

# Ensure cover_art directory exists
os.makedirs(COVER_ART_DIR, exist_ok=True)


def copy_cover_art(file_path, silent=False):
    """Copy and save the first APIC frame (cover art) from the audio file."""

    try:
        audio_file = MutagenFile(file_path)
        if not audio_file or not audio_file.tags:
            return f'[SKIP] No tags in "{file_path}"'

        apic_frames = (
            audio_file.tags.getall('APIC')
            if hasattr(audio_file.tags, 'getall')
            else []
        )
        if not apic_frames:
            return f'[SKIP] No cover art in "{file_path}"'

        cover_frame = apic_frames[0]
        image_extension = cover_frame.mime.split('/')[-1]
        file_basename = os.path.splitext(os.path.basename(file_path))[0]
        output_path = os.path.join(
            COVER_ART_DIR, f'{file_basename}.{image_extension}'
        )

        with open(output_path, 'wb') as output_file:
            output_file.write(cover_frame.data)

        return f'[COPY] Cover art saved to "{output_path}"'
    except Exception as error_info:
        return f'[ERROR] Failed on "{file_path}": {error_info}'


def delete_cover_art(file_path):
    """Delete the first APIC frame (cover art) from the audio file."""

    try:
        audio_file = MutagenFile(file_path, easy=False)
        if not audio_file or not audio_file.tags:
            return f'[SKIP] No tags to remove from "{file_path}"'

        if hasattr(audio_file.tags, 'delall'):
            audio_file.tags.delall('APIC')
            audio_file.save()
            return f'[DELETE] Cover art removed from "{file_path}"'
        else:
            return (
                f'[SKIP] Tag format does not support cover deletion: '
                f'"{file_path}"'
            )
    except Exception as error_info:
        return (
            f'[ERROR] Could not delete cover art from "{file_path}": '
            f'{error_info}'
        )


def extract_cover_art(file_path):
    """Copy and remove cover art from the audio file."""

    copy_result = copy_cover_art(file_path, silent=True)
    if '[COPY]' in copy_result:
        delete_result = delete_cover_art(file_path)
        return f'{copy_result}\n{delete_result}'
    return copy_result


def replace_cover_art(file_path, image_path):
    """Replace any existing cover art of the audio file with a new one."""

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

        return f'[REPLACE] Cover art replaced in "{file_path}"'
    except Exception as error_info:
        return f'[ERROR] Failed on "{file_path}": {error_info}'


def get_audio_files_from_directory(directory_path):
    return [
        os.path.join(directory_path, entry)
        for entry in os.listdir(directory_path)
        if entry.lower().endswith(AUDIO_EXTENSIONS)
    ]


def run_operation(operation, audio_selection, image_path):
    if not audio_selection:
        messagebox.showwarning('Warning', 'Please select a file or folder.')
        return

    if isinstance(audio_selection, str) and os.path.isdir(audio_selection):
        files = get_audio_files_from_directory(audio_selection)
    elif isinstance(audio_selection, list):
        files = audio_selection
    else:
        messagebox.showerror('Error', 'Invalid selection.')
        return

    if not files:
        messagebox.showwarning('Warning', 'No valid audio files found.')
        return

    results = []
    for file_path in files:
        if operation == 'COPY':
            results.append(copy_cover_art(file_path))
        elif operation == 'DELETE':
            results.append(delete_cover_art(file_path))
        elif operation == 'EXTRACT':
            results.append(extract_cover_art(file_path))
        elif operation == 'REPLACE':
            if not image_path or not os.path.isfile(image_path):
                results.append('[ERROR] Invalid image file selected.')
                break
            results.append(replace_cover_art(file_path, image_path))

    messagebox.showinfo('Operation Summary', '\n'.join(results))


def main():
    root = Tk()
    root.title('Cover Art Manager')

    operation_var = StringVar()
    path_display_var = StringVar()
    image_var = StringVar()
    audio_selection = []

    def browse_files():
        nonlocal audio_selection
        files = list(
            filedialog.askopenfilenames(
                filetypes=[('Audio Files', AUDIO_FILE_PATTERN)]
            )
        )
        audio_selection = files
        path_display_var.set('; '.join(files))

    def browse_folder():
        nonlocal audio_selection
        folder = filedialog.askdirectory()
        audio_selection = folder
        path_display_var.set(folder)

    def browse_image():
        image_var.set(
            filedialog.askopenfilename(
                filetypes=[('Image Files', IMAGE_FILE_PATTERN)]
            )
        )

    ttk.Label(root, text='Operation:').grid(row=0, column=0, sticky='w')
    ttk.Combobox(
        root,
        textvariable=operation_var,
        values=['COPY', 'DELETE', 'EXTRACT', 'REPLACE'],
    ).grid(row=0, column=1)

    ttk.Label(root, text='Selected Audio:').grid(row=1, column=0, sticky='w')
    ttk.Entry(root, textvariable=path_display_var, width=60).grid(
        row=1, column=1, columnspan=2
    )
    ttk.Button(root, text='Browse Folder', command=browse_folder).grid(
        row=1, column=3
    )
    ttk.Button(root, text='Browse Files', command=browse_files).grid(
        row=1, column=4
    )

    ttk.Label(root, text='Image (for REPLACE):').grid(
        row=2, column=0, sticky='w'
    )
    ttk.Entry(root, textvariable=image_var, width=60).grid(
        row=2, column=1, columnspan=2
    )
    ttk.Button(root, text='Browse Image', command=browse_image).grid(
        row=2, column=3
    )

    ttk.Button(
        root,
        text='Run',
        command=lambda: run_operation(
            operation_var.get(), audio_selection, image_var.get()
        ),
    ).grid(row=3, column=1)
    ttk.Button(root, text='Exit', command=root.destroy).grid(row=3, column=2)

    root.mainloop()


if __name__ == '__main__':
    main()
