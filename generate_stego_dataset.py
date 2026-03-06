import os, sys, random, shutil
from PIL import Image

COVER_SOURCE = os.path.join(os.path.expanduser("~"), "Desktop", "images", "DIV2K_train_HR", "DIV2K_train_HR")
BASE_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "StegoAI")
COVER_DIR = os.path.join(BASE_DIR, "dataset", "cover")
STEGO_DIR = os.path.join(BASE_DIR, "dataset", "stego")
TRAIN_DIR = os.path.join(BASE_DIR, "dataset", "train")
VAL_DIR = os.path.join(BASE_DIR, "dataset", "val")
TEST_DIR = os.path.join(BASE_DIR, "dataset", "test")
IMG_SIZE = (128, 128)
MAX_STEGO = 5000
DELIMITER = "###END###"
MESSAGES = ["Secret message hidden here.", "Confidential data embedded.", "Operation complete.", "Mission briefing classified.", "Secure channel active."]

def text_to_bits(text):
    bits = []
    for char in text:
        b = format(ord(char), "08b")
        bits.extend([int(x) for x in b])
    return bits

def encode_image(cover_path, message, output_path):
    try:
        img = Image.open(cover_path).convert("RGB").resize(IMG_SIZE, Image.LANCZOS)
        pixels = list(img.getdata())
        bits = text_to_bits(message + DELIMITER)
        if len(bits) > len(pixels) * 3:
            bits = text_to_bits("Secret" + DELIMITER)
        new_pixels = []
        bit_idx = 0
        for pixel in pixels:
            r, g, b = pixel
            if bit_idx < len(bits): r = (r & 0b11111110) | bits[bit_idx]; bit_idx += 1
            if bit_idx < len(bits): g = (g & 0b11111110) | bits[bit_idx]; bit_idx += 1
            if bit_idx < len(bits): b = (b & 0b11111110) | bits[bit_idx]; bit_idx += 1
            new_pixels.append((r, g, b))
        out = Image.new("RGB", IMG_SIZE)
        out.putdata(new_pixels)
        out.save(output_path, format="PNG")
        return True
    except:
        return False

def get_files(folder):
    exts = ('.png', '.jpg', '.jpeg', '.bmp')
    return [f for f in os.listdir(folder) if f.lower().endswith(exts)]

def main():
    print("STEGO DATASET GENERATOR")
    os.makedirs(COVER_DIR, exist_ok=True)
    os.makedirs(STEGO_DIR, exist_ok=True)
    print("Copying cover images...")
    cover_files = get_files(COVER_SOURCE)
    print("Found", len(cover_files), "images")
    done = 0
    for f in cover_files:
        src = os.path.join(COVER_SOURCE, f)
        dst = os.path.join(COVER_DIR, f.replace(".jpg",".png").replace(".jpeg",".png"))
        if not os.path.exists(dst):
            try:
                Image.open(src).convert("RGB").resize(IMG_SIZE, Image.LANCZOS).save(dst, "PNG")
            except: pass
        done += 1
        if done % 100 == 0: print(" ", done, "covers done")
    print("Generating 5000 stego images...")
    cover_list = get_files(COVER_DIR)
    done = 0
    batch = 0
    while done < MAX_STEGO:
        random.shuffle(cover_list)
        for f in cover_list:
            if done >= MAX_STEGO: break
            sname = "stego_" + str(batch).zfill(4) + "_" + str(done).zfill(4) + ".png"
            spath = os.path.join(STEGO_DIR, sname)
            if encode_image(os.path.join(COVER_DIR, f), random.choice(MESSAGES), spath):
                done += 1
            if done % 200 == 0 and done > 0: print(" ", done, "/ 5000 done")
        batch += 1
    print("Building splits...")
    for d in [TRAIN_DIR, VAL_DIR, TEST_DIR]:
        if os.path.exists(d): shutil.rmtree(d)
    for sp in [TRAIN_DIR, VAL_DIR, TEST_DIR]:
        for cls in ["cover","stego"]: os.makedirs(os.path.join(sp,cls), exist_ok=True)
    for cls, src in [("cover",COVER_DIR),("stego",STEGO_DIR)]:
        files = get_files(src)
        random.shuffle(files)
        n = len(files)
        nt = int(n*0.70); nv = int(n*0.15)
        for dest, flist in [(TRAIN_DIR,files[:nt]),(VAL_DIR,files[nt:nt+nv]),(TEST_DIR,files[nt+nv:])]:
            for f in flist: shutil.copy2(os.path.join(src,f), os.path.join(dest,cls,f))
            print(" ", os.path.basename(dest)+"/"+cls+":", len(flist))
    print("DONE! Now run: python models/train.py")

main()
