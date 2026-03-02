import os, sys, random, shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COVER_DIR, STEGO_DIR, TRAIN_DIR, VAL_DIR, TEST_DIR, SAMPLE_MESSAGES

MAX_IMAGES = 800

def get_files(folder):
    exts = ('.png', '.jpg', '.jpeg', '.bmp', '.pgm')
    return sorted([f for f in os.listdir(folder) if f.lower().endswith(exts)])

def build_splits():
    print("="*50)
    print("Dataset Builder - Using Real Images")
    print("="*50)
    if not os.path.exists(COVER_DIR):
        print(f"ERROR: {COVER_DIR} not found!"); sys.exit(1)

    # Generate stego from real cover images
    from utils.steganography import encode_image
    from PIL import Image
    os.makedirs(STEGO_DIR, exist_ok=True)
    cover_files = get_files(COVER_DIR)
    existing = get_files(STEGO_DIR)
    needed = MAX_IMAGES - len(existing)
    if needed > 0:
        print(f"\nGenerating {needed} stego images...")
        samples = random.sample(cover_files, min(needed, len(cover_files)))
        for i, fname in enumerate(samples):
            try:
                img = Image.open(os.path.join(COVER_DIR, fname)).convert("RGB")
                tmp = os.path.join(COVER_DIR, "tmp.png")
                img.save(tmp)
                out = os.path.join(STEGO_DIR, "stego_"+fname.rsplit(".",1)[0]+".png")
                encode_image(tmp, random.choice(SAMPLE_MESSAGES), out)
                os.remove(tmp)
            except: pass
            if (i+1) % 100 == 0: print(f"   {i+1}/{needed} done...")
        print("Stego generation done!")

    for d in [TRAIN_DIR, VAL_DIR, TEST_DIR]:
        if os.path.exists(d): shutil.rmtree(d)
    for split in [TRAIN_DIR, VAL_DIR, TEST_DIR]:
        for cls in ["cover","stego"]:
            os.makedirs(os.path.join(split, cls), exist_ok=True)

    for cls, src in [("cover", COVER_DIR), ("stego", STEGO_DIR)]:
        files = get_files(src)
        if len(files) > MAX_IMAGES: files = random.sample(files, MAX_IMAGES)
        random.shuffle(files)
        n = len(files)
        n_train = int(n*0.70); n_val = int(n*0.15)
        for dest_base, flist in [(TRAIN_DIR, files[:n_train]), (VAL_DIR, files[n_train:n_train+n_val]), (TEST_DIR, files[n_train+n_val:])]:
            dest = os.path.join(dest_base, cls)
            for f in flist: shutil.copy2(os.path.join(src, f), os.path.join(dest, f))
            print(f"  {os.path.basename(dest_base)}/{cls}: {len(flist)}")

    print("\nDONE! Run: python models/train.py")

if __name__ == "__main__":
    build_splits()
