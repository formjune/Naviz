import re
import os
from PIL import Image
from concurrent.futures import ThreadPoolExecutor


DIRECTORY = r"E:\ref_2"
SIZE = 128, 256, 512, 1024, 2048, 4096, 8192
DEFAULT_SIZE = 256
THREAD_COUNT = 8
SKIP_HIGHER_THAN_ORIGINAL = True


def proceedImage(image_name):
    image = Image.open(image_name)
    current_res = max(image.height, image.width)
    for size in SIZE:
        param = size / current_res
        if SKIP_HIGHER_THAN_ORIGINAL and param >= 1:
            continue
        new_image = image.resize((int(image.width * param), int(image.height * param)), Image.Resampling.LANCZOS)
        new_image.save(image_name.replace(".jpg", f"_{size}.jpg"))


images_list = []
for folder in os.listdir(DIRECTORY):
    dirname = os.path.join(DIRECTORY, folder)
    if not os.path.isdir(dirname) or not re.search(r"(\d{6})-(\d{6})", folder):
        continue

    for file in os.listdir(dirname):
        filename = os.path.join(dirname, file)

        if file.endswith(".mtl"):
            lines = open(filename).readlines()
            for i in range(1, len(lines), 2):
                 lines[i] = lines[i].replace(".jpg", f"_{DEFAULT_SIZE}.jpg")
            if len(lines) == 2:
                lines[0] = "newmtl material\n"
            open(filename, "w").writelines(lines)
        #
        elif file.endswith(".jpg"):
            images_list.append(filename)


with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
    executor.map(proceedImage, images_list)