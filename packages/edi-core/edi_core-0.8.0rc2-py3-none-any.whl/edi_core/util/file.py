import os.path
import shutil
from io import TextIOWrapper

from edi_core.util.env import get_env


def dir_exists(path: str) -> bool:
    return os.path.isdir(path)


def file_exists(path: str) -> bool:
    return os.path.isfile(path)


def path_exists(path: str) -> bool:
    return os.path.exists(path)


def check_file_exists(path: str):
    if not file_exists(path):
        raise FileNotFoundError(f"The file at {path} does not exist.")


def move(src, dest):
    shutil.move(src, dest)


def delete_file(path: str):
    if file_exists(path):
        os.remove(path)


def get_file_name_without_extension(path: str) -> str:
    base_name = os.path.basename(path)
    name_without_extension, _ = os.path.splitext(base_name)
    return name_without_extension


def get_file_name_with_extension(path: str) -> str:
    return os.path.basename(path)


def get_output_dir():
    return get_env("OUTPUT_DIR")


def get_input_dir():
    return get_env("INPUT_DIR")


def to_output_path(relative_path: str):
    return os.path.join(get_output_dir(), relative_path)


def to_input_path(relative_path: str):
    return os.path.join(get_input_dir(), relative_path)


def ensure_parent_dir_exists(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)


def save_to_output_dir(relative_path: str, content: str) -> str:
    output_path = to_output_path(relative_path)
    ensure_parent_dir_exists(output_path)
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(content)
    return output_path


def open_file_in_output(relative_path: str) -> TextIOWrapper:
    output_path = to_output_path(relative_path)
    ensure_parent_dir_exists(output_path)
    return open(output_path)


def open_file_in_input(relative_path: str) -> TextIOWrapper:
    input_path = to_input_path(relative_path)
    return open(input_path)


def read_file(path: str) -> str:
    check_file_exists(path)
    with open(path, 'r', encoding='utf-8') as file:
        return file.read()
