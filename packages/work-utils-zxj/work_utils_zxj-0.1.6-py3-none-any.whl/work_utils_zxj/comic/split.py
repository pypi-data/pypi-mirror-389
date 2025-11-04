import shutil
from typing import Counter
import os
from PIL import Image


def split_image(image_path: str, save_path: str, is_jpn=True):
    left = "02"
    right = "01"
    if not is_jpn:
        left = "01"
        right = "02"
    base_name = os.path.basename(image_path)
    suffix = os.path.splitext(image_path)[1]
    output_left_path = os.path.join(save_path, f"{base_name}_{left}{suffix}")
    output_right_path = os.path.join(save_path, f"{base_name}_{right}{suffix}")
    # 打开图片
    img = Image.open(image_path)
    width, height = img.size
    # 切割左半部分
    left_img = img.crop((0, 0, width // 2, height))
    left_img.save(output_left_path, quality=95)
    (f"{image_path} Image is cut over  left  save to  {output_left_path}")
    # 切割右半部分
    right_img = img.crop((width // 2, 0, width, height))
    right_img.save(output_right_path, quality=95)
    print(f"{image_path} Image is cut over  right  save to  {output_right_path}")


def move_file(image_path: str, save_path: str, move_modify_name: str | None = None):
    image_name = os.path.basename(image_path)
    dist_src = os.path.join(save_path, image_name)
    if move_modify_name is not None:
        dist_src = os.path.join(
            save_path, f"{move_modify_name}{os.path.splitext(image_path)[1]}"
        )
    shutil.copy(image_path, dist_src)
    print(f"{image_path} Image is move to {dist_src}")


def get_size(files: list[str]):
    size = []
    for file_path in files:
        try:
            with Image.open(file_path) as img:
                size.append(img.size)  # (width, height)
        except Exception as e:
            print(f"无法读取图片 {file_path}, 错误: {e}")
    return Counter(size)


# is_split true 符合的切割 false 不符合的切割
def split(
    src: str,
    split_src: str | None = None,
    width_tolerance: int = 10,
    height_tolerance: int = 10,
    is_split: bool = True,
    is_jp: bool = True,
):
    if not src or not os.path.isdir(src):
        raise ValueError("src is empty")
    if not split_src:
        base_name = os.path.basename(src)
        split_src = os.path.join(os.path.dirname(src), base_name + "_split")
    os.makedirs(split_src, exist_ok=True)
    folders = [
        os.path.join(src, folder)
        for folder in os.listdir(src)
        if os.path.isdir(os.path.join(src, folder))
    ]
    for folder in folders:
        files = [
            os.path.join(folder, file_path)
            for file_path in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, file_path))
        ]
        image_size, _ = get_size(files).most_common()[0]
        common_width, common_height = image_size
        for image_file in files:
            img = Image.open(image_file)
            width, height = img.size
            save_split_path = os.path.join(split_src, os.path.basename(folder))
            os.makedirs(save_split_path, exist_ok=True)
            if (
                abs(width - common_width) < width_tolerance
                and abs(height - common_height) < height_tolerance
                and is_split
            ):
                split_image(image_file, save_split_path, is_jp)
            else:
                move_file(image_file, save_split_path)
