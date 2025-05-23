import os

from mutagen.id3 import ID3
from mutagen.mp3 import MP3

# Directories
AUDIO_DIR = 'audio'
COVER_ART_DIR = 'cover_art'

# Create the output directory if it doesn't exist
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(COVER_ART_DIR, exist_ok=True)

# Iterate over all MP3 files in the audio directory
for filename in os.listdir(AUDIO_DIR):
    if filename.lower().endswith('.mp3'):
        mp3_path = os.path.join(AUDIO_DIR, filename)

        try:
            audio = MP3(mp3_path, ID3=ID3)
        except Exception as e:
            print(f"Failed to load '{filename}': {e}")
            continue

        if audio.tags is not None:
            apic_frames = audio.tags.getall('APIC')

            if apic_frames:
                apic = apic_frames[0]
                image_data = apic.data
                image_extension = apic.mime.split('/')[
                    -1
                ]  # e.g., 'jpeg', 'png'

                # Strip extension and build new file name
                base_name = os.path.splitext(filename)[0]
                output_path = os.path.join(
                    COVER_ART_DIR, f'{base_name}.{image_extension}'
                )

                try:
                    with open(output_path, 'wb') as img_out:
                        img_out.write(image_data)
                    print(
                        f"Extracted cover art from '{filename}' -> '{output_path}'"
                    )
                except Exception as e:
                    print(f"Error saving cover art for '{filename}': {e}")
            else:
                print(f"No cover art in '{filename}'")
        else:
            print(f"No ID3 tags in '{filename}'")
