import os
import sys
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


def copy_cover_art(file_path):
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
        assert audio_file.tags is not None
        if hasattr(audio_file.tags, 'delall'):
            audio_file.tags.delall('APIC')
            audio_file.save()
            return f'[DELETE] Cover art removed from "{file_path}"'
        return (
            f'[SKIP] Tag format does not support cover deletion: "{file_path}"'
        )
    except Exception as error_info:
        return (
            f'[ERROR] Could not delete cover art from "{file_path}": '
            f'{error_info}'
        )


def extract_cover_art(file_path):
    """Copy and remove cover art from the audio file."""

    copy_result = copy_cover_art(file_path)
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


def edit_metadata(file_path, updates):
    try:
        audio_file = MutagenFile(file_path, easy=True)
        if not audio_file:
            return f'[ERROR] Could not open "{file_path}"'
        for key, value in updates.items():
            if value:
                audio_file[key] = value
        audio_file.save()
        return f'[UPDATE] Metadata saved in "{file_path}"'
    except Exception as error_info:
        return f'[ERROR] Metadata edit failed on "{file_path}": {error_info}'


def populate_metadata_fields(
    file_path, title_var, artist_var, album_var, genre_var, date_var
):
    try:
        audio_file = MutagenFile(file_path, easy=True)
        if audio_file:
            title_var.set(audio_file.get('title', [''])[0])
            artist_var.set(audio_file.get('artist', [''])[0])
            album_var.set(audio_file.get('album', [''])[0])
            genre_var.set(audio_file.get('genre', [''])[0])
            date_var.set(audio_file.get('date', [''])[0])
    except Exception as error_info:
        messagebox.showerror('Error', f'Failed to read metadata: {error_info}')


def main():
    root = Tk()
    root.title('Audio Cover Art Manager & Metadata Editor')

    audio_selection = []
    image_path_var = StringVar()
    path_display_var = StringVar()

    title_var = StringVar()
    artist_var = StringVar()
    album_var = StringVar()
    genre_var = StringVar()
    date_var = StringVar()

    def browse_files():
        nonlocal audio_selection
        files = list(
            filedialog.askopenfilenames(
                filetypes=[('Audio Files', AUDIO_FILE_PATTERN)]
            )
        )
        audio_selection = files
        path_display_var.set('; '.join(files))
        if len(files) == 1:
            populate_metadata_fields(
                files[0], title_var, artist_var, album_var, genre_var, date_var
            )

    def browse_folder():
        nonlocal audio_selection
        folder = filedialog.askdirectory()
        audio_selection = get_audio_files_from_directory(folder)
        path_display_var.set(folder)

    def browse_image():
        image_path_var.set(
            filedialog.askopenfilename(
                filetypes=[('Image Files', IMAGE_FILE_PATTERN)]
            )
        )

    def run_cover_op(operation):
        if not audio_selection:
            messagebox.showerror('Error', 'No audio files selected.')
            return
        results = []
        for file_path in audio_selection:
            if operation == 'COPY':
                results.append(copy_cover_art(file_path))
            elif operation == 'DELETE':
                results.append(delete_cover_art(file_path))
            elif operation == 'EXTRACT':
                results.append(extract_cover_art(file_path))
            elif operation == 'REPLACE':
                if not image_path_var.get():
                    messagebox.showerror('Error', 'Select an image file.')
                    return
                results.append(
                    replace_cover_art(file_path, image_path_var.get())
                )
        messagebox.showinfo('Result', '\n'.join(results))

    def run_metadata_edit(batch=False):
        if not audio_selection:
            messagebox.showerror('Error', 'No audio files selected.')
            return
        updates = {
            'title': title_var.get(),
            'artist': artist_var.get(),
            'album': album_var.get(),
            'genre': genre_var.get(),
            'date': date_var.get(),
        }
        targets = audio_selection if batch else [audio_selection[0]]
        results = [edit_metadata(f, updates) for f in targets]
        messagebox.showinfo('Metadata Result', '\n'.join(results))

    notebook = ttk.Notebook(root)

    # Cover tab
    cover_tab = ttk.Frame(notebook)
    metadata_tab = ttk.Frame(notebook)

    notebook.add(cover_tab, text='Cover Art')
    notebook.add(metadata_tab, text='Metadata')
    notebook.pack(expand=True, fill='both')

    # Cover tab layout
    ttk.Label(cover_tab, text='Selected Audio:').grid(
        row=0, column=0, sticky='w'
    )
    ttk.Entry(cover_tab, textvariable=path_display_var, width=60).grid(
        row=0, column=1, columnspan=2
    )
    ttk.Button(cover_tab, text='Browse Folder', command=browse_folder).grid(
        row=0, column=3
    )
    ttk.Button(cover_tab, text='Browse Files', command=browse_files).grid(
        row=0, column=4
    )

    ttk.Label(cover_tab, text='Image (for REPLACE):').grid(
        row=1, column=0, sticky='w'
    )
    ttk.Entry(cover_tab, textvariable=image_path_var, width=60).grid(
        row=1, column=1, columnspan=2
    )
    ttk.Button(cover_tab, text='Browse Image', command=browse_image).grid(
        row=1, column=3
    )

    ttk.Button(
        cover_tab, text='COPY', command=lambda: run_cover_op('COPY')
    ).grid(row=2, column=1)
    ttk.Button(
        cover_tab, text='DELETE', command=lambda: run_cover_op('DELETE')
    ).grid(row=2, column=2)
    ttk.Button(
        cover_tab, text='EXTRACT', command=lambda: run_cover_op('EXTRACT')
    ).grid(row=2, column=3)
    ttk.Button(
        cover_tab, text='REPLACE', command=lambda: run_cover_op('REPLACE')
    ).grid(row=2, column=4)

    # Metadata tab layout
    ttk.Label(metadata_tab, text='Title:').grid(row=0, column=0, sticky='w')
    ttk.Entry(metadata_tab, textvariable=title_var, width=50).grid(
        row=0, column=1, columnspan=2
    )

    ttk.Label(metadata_tab, text='Artist:').grid(row=1, column=0, sticky='w')
    ttk.Entry(metadata_tab, textvariable=artist_var, width=50).grid(
        row=1, column=1, columnspan=2
    )

    ttk.Label(metadata_tab, text='Album:').grid(row=2, column=0, sticky='w')
    ttk.Entry(metadata_tab, textvariable=album_var, width=50).grid(
        row=2, column=1, columnspan=2
    )

    ttk.Label(metadata_tab, text='Genre:').grid(row=3, column=0, sticky='w')
    ttk.Entry(metadata_tab, textvariable=genre_var, width=50).grid(
        row=3, column=1, columnspan=2
    )

    ttk.Label(metadata_tab, text='Date:').grid(row=4, column=0, sticky='w')
    ttk.Entry(metadata_tab, textvariable=date_var, width=50).grid(
        row=4, column=1, columnspan=2
    )

    ttk.Button(
        metadata_tab,
        text='Apply to First File',
        command=lambda: run_metadata_edit(batch=False),
    ).grid(row=5, column=1)
    ttk.Button(
        metadata_tab,
        text='Apply to All Files',
        command=lambda: run_metadata_edit(batch=True),
    ).grid(row=5, column=2)

    ttk.Button(root, text='Exit', command=sys.exit).pack(pady=10)

    root.protocol('WM_DELETE_WINDOW', sys.exit)
    root.mainloop()


if __name__ == '__main__':
    main()
