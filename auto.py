import os
import base64
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, APIC
from PIL import Image
from io import BytesIO

GROUPS = [
    ("מהשבוע האחרון", "hits", 1, 25),
    ("מהחודש האחרון", "shabbat", 26, 50),
    ("להיטים מהשנה האחרונה", "nostalgia", 51, 75),
    ("שירים מכל הזמנים", "more", 76, 100),
]

def extract_song_info(mp3_path):
    try:
        audio = MP3(mp3_path, ID3=ID3)
        tags = audio.tags
        title = tags.get('TIT2', TIT2(text=os.path.basename(mp3_path))).text[0]
        artist = tags.get('TPE1', TPE1(text="לא ידוע")).text[0]
        # חיפוש עטיפה בכל תגית שמתחילה ב-APIC
        apic = None
        for key in tags.keys():
            if key.startswith('APIC'):
                apic = tags[key]
                break
        if apic:
            try:
                img = Image.open(BytesIO(apic.data))
                img = img.resize((120, 120))
                buf = BytesIO()
                img.save(buf, format="PNG")
                img_b64 = base64.b64encode(buf.getvalue()).decode()
                cover_url = f"data:image/png;base64,{img_b64}"
            except Exception as e:
                print(f"בעיה בטעינת תמונה עבור {mp3_path}: {e}")
                cover_url = None
        else:
            print(f"לא נמצאה עטיפה (APIC) עבור {mp3_path}")
            cover_url = None
        return title, artist, cover_url
    except Exception as e:
        print(f"שגיאה כללית בקובץ {mp3_path}: {e}")
        return os.path.basename(mp3_path), "לא ידוע", None

def generate_group_html(title, folder, start_idx, end_idx):
    group_html = f'''
        <div class="songs-group-card">
            <div class="group-header">
                <div class="group-title">{title}</div>
                <a href="downloads/{folder}.zip" class="download-all-btn" download target="_blank">הורד הכל</a>
            </div>
            <div class="songs-grid">
    '''
    songs_dir = os.path.join("songs", folder)
    if not os.path.exists(songs_dir):
        return group_html + '</div></div>'


        song_html += f'''
            <a href="javascript:void(0)" 
               onclick="downloadFile('{song_href}', '{os.path.basename(mp3_path)}')" 
               class="download-btn">הורד</a>
        '''    

    files = sorted([f for f in os.listdir(songs_dir) if f.lower().endswith('.mp3')])
    for idx, filename in enumerate(files, start=start_idx):
        mp3_path = os.path.join(songs_dir, filename)
        title, artist, cover_url = extract_song_info(mp3_path)
        song_href = f"songs/{folder}/{filename}"
        style = f'background: linear-gradient(rgba(255,255,255,0.5), rgba(255,255,255,0.5)), url({cover_url}); background-size: cover; background-position: center;' if cover_url else ''
        group_html += f'''
            <div class="song-card" style="{style}">
                <div class="song-info">
                    <span class="song-title">{title}</span>
                    <span class="artist-name">{artist}</span>
                </div>
                <audio src="{song_href}" controls style="width:100%;margin-top:10px;"></audio>
            </div>
        '''
        if idx >= end_idx:
            break
    group_html += '</div></div>'
    return group_html

def main():
    with open(r"E:\sher-hadash\index_template.html", encoding="utf-8") as f:
        template = f.read()

    groups_html = ""
    for group_title, folder, start, end in GROUPS:
        groups_html += generate_group_html(group_title, folder, start, end)

    html = template.replace("<!-- GROUPS_PLACEHOLDER -->", groups_html)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    main()
