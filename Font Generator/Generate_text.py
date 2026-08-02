import json
import itertools
import os
from PIL import Image, ImageDraw, ImageFont
import numpy
import cv2


FONT_FILE = "ttf/Oswald.ttf"
FONT_NAME = "Oswald"
RESOLUTION = 2048
FONT_SIZE = 180

CELL_HEIGHT_TOP = 120
CELL_HEIGHT_BOTTOM = 120
CELL_WIDTH = 8
SPACE_WIDTH = 40

BACKGROUND_COLOR = 0, 0, 0, 0
FONT_COLOR = 255, 255, 255, 255


# do not change
STRING = "абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ0123456789 .,/№()»-"
COLUMNS = 13
ROWS = 7
step_x = RESOLUTION // COLUMNS
step_y = RESOLUTION // ROWS
PAIRS = {
    "УЛ": .97,
    "ул": .97,
    "Ул": .97,
    "уЛ": .97,
    "ца": .5,
    "ВА": .2
}

font = ImageFont.truetype(FONT_FILE, FONT_SIZE)
canvas = Image.new("RGBA", (RESOLUTION, RESOLUTION), BACKGROUND_COLOR)
canvas_edit = ImageDraw.Draw(canvas)
frame = Image.new("RGB", (RESOLUTION, RESOLUTION), "black")
frame_edit = ImageDraw.Draw(frame)
uv = {}


for j, letter in enumerate(STRING):
    pos_y = (j // COLUMNS + 0.5) * step_y
    pos_x = (j % COLUMNS + 0.5) * step_x

    empty = Image.new("L", (RESOLUTION, RESOLUTION), 0)
    empty_edit = ImageDraw.Draw(empty)
    empty_edit.text((pos_x, pos_y), letter, anchor="mm", font=font, fill="white")
    canvas_edit.text((pos_x, pos_y), letter, anchor="mm", font=font, fill=FONT_COLOR)
    frame_edit.text((pos_x, pos_y), letter, anchor="mm", font=font, fill="white")

    if letter == " ":
        x_min = pos_x - SPACE_WIDTH / 2
        x_max = pos_x + SPACE_WIDTH / 2

    else:
        empty = numpy.array(empty)
        thresh = cv2.threshold(empty, 127, 255, cv2.THRESH_BINARY)[1]
        contours = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
        contours = numpy.concatenate(contours)
        x_min, y_min, w, h = cv2.boundingRect(contours)
        x_max = x_min + w + 1
        x_min -= CELL_WIDTH

    y_min = pos_y - CELL_HEIGHT_TOP
    y_max = pos_y + CELL_HEIGHT_BOTTOM
    uv[letter] = x_min / RESOLUTION, x_max / RESOLUTION, 1 - y_max / RESOLUTION, 1 - y_min / RESOLUTION
    frame_edit.rectangle((x_min, y_min, x_max, y_max), outline="blue", width=2)


data = CELL_WIDTH / RESOLUTION, PAIRS, uv


if 0:
    #frame_edit.text((1024, 1024), "улица колотушкина", anchor="mm", font=font, fill="blue")

    import cv2
    import numpy
    image = cv2.resize(numpy.array(frame), (1024, 1024))
    cv2.imshow("Image", image)
    cv2.waitKey(0)
else:
    out_folder = r"C:\Users\Andrey\AppData\Roaming\Blender Foundation\Blender\5.1\scripts\addons\PolyToFont_addon"
    os.makedirs(out_folder, exist_ok=True)
    json.dump(data, open(f"{out_folder}/{FONT_NAME}.json", "w", encoding="utf-8"))
    #canvas.save(f"{out_folder}/{FONT_NAME}.png")
    #frame.save(f"{out_folder}/{FONT_NAME}_checker.png")

