import os
import zipfile
import base64
import re
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TPE1
from PIL import Image
from io import BytesIO
from datetime import datetime

ALBUMS_DIR = "albums"

def extract_album_info(zip_path):
    album_name = os.path.splitext(os.path.basename(zip_path))[0]
    artist = "לא ידוע"
    cover_data_url = None

    print(f"בודק אלבום: {zip_path}")
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            # מצא קובץ תמונה
            img_name = next((f for f in z.namelist() if f.lower().endswith(('.jpg', '.jpeg', '.png'))), None)
            if img_name:
                print(f"  נמצא קובץ תמונה: {img_name}")
                with z.open(img_name) as img_file:
                    img = Image.open(img_file)
                    img = img.convert("RGB")
                    img = img.resize((200, 200))
                    buf = BytesIO()
                    img.save(buf, format="PNG")
                    img_b64 = base64.b64encode(buf.getvalue()).decode()
                    cover_data_url = f"data:image/png;base64,{img_b64}"
            else:
                print("  לא נמצאה עטיפת אלבום (תמונה)")

            # מצא קובץ MP3
            mp3_name = next((f for f in z.namelist() if f.lower().endswith('.mp3')), None)
            if mp3_name:
                print(f"  נמצא קובץ MP3: {mp3_name}")
                with z.open(mp3_name) as mp3_file:
                    mp3_bytes = mp3_file.read()
                    try:
                        audio = MP3(BytesIO(mp3_bytes), ID3=ID3)
                        tags = audio.tags
                        if tags and 'TPE1' in tags:
                            artist = tags['TPE1'].text[0]
                            print(f"    שם אמן מהתגית: {artist}")
                        else:
                            print("    לא נמצאה תגית TPE1 (אמן)")
                    except Exception as e:
                        print(f"    שגיאה בקריאת תגיות MP3: {e}")
            else:
                print("  לא נמצא קובץ MP3 באלבום")
    except Exception as e:
        print(f"שגיאה בפתיחת קובץ ZIP: {e}")

    # תאריך יצירת קובץ (ולא שינוי אחרון)
    if hasattr(os, "stat"):
        stat = os.stat(zip_path)
        if hasattr(stat, "st_ctime"):
            created = datetime.fromtimestamp(stat.st_ctime).strftime("%d.%m.%Y")
        else:
            created = datetime.fromtimestamp(os.path.getmtime(zip_path)).strftime("%d.%m.%Y")
    else:
        created = datetime.fromtimestamp(os.path.getmtime(zip_path)).strftime("%d.%m.%Y")

    return {
        "album_name": album_name,
        "artist": artist,
        "cover_data_url": cover_data_url,
        "zip_file": os.path.basename(zip_path),
        "updated": created
    }

def generate_albums_html():
    html = ""
    if not os.path.exists(ALBUMS_DIR):
        print(f"תיקיית האלבומים albums לא קיימת בנתיב: {os.path.abspath(ALBUMS_DIR)}")
        return html, []
    # מיון לפי תאריך יצירת קובץ (החדש ביותר למעלה)
    files = sorted(
        [f for f in os.listdir(ALBUMS_DIR) if f.lower().endswith('.zip')],
        reverse=True,
        key=lambda f: os.stat(os.path.join(ALBUMS_DIR, f)).st_ctime
    )
    print(f"נמצאו {len(files)} קבצי ZIP בתיקיית albums")
    album_cards = []
    for fname in files:
        album_path = os.path.join(ALBUMS_DIR, fname)
        info = extract_album_info(album_path)
        card_html = f'''
        <div class="album-card" data-zip="{info["zip_file"]}" style="--album-cover: url('{info["cover_data_url"] or ""}')">
            <img src="{info["cover_data_url"] or ""}" alt="{info["album_name"]}" class="album-cover">
            <div class="album-updated">עודכן לאחרונה: {info["updated"]}</div>
            <a href="{ALBUMS_DIR}/{info["zip_file"]}" class="download-btn" download>הורד אלבום</a>
            <div class="album-content">
                <div class="album-info">
                    <div class="album-title">{info["album_name"]}</div>
                    <div class="artist-name">{info["artist"]}</div>
                </div>
            </div>
        </div>
        '''
        album_cards.append(card_html)
    return album_cards

def main():
    print("מתחיל עדכון דף אלבומים...")

    # קרא את התבנית
    with open("albums_template.html", encoding="utf-8") as f:
        template = f.read()

    # צור כרטיסים לכל האלבומים
    album_cards = generate_albums_html()
    if not album_cards:
        print("אין אלבומים. לא מתבצע עדכון.")
        return

    all_albums_html = "\n".join(album_cards)
    html = template.replace("<!-- ALBUMS_PLACEHOLDER -->", all_albums_html)
    with open("albums.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("סיום! נוצר/עודכן קובץ albums.html")

if __name__ == "__main__":
    main()
