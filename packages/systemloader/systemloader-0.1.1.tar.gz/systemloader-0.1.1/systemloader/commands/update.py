import os
import shutil
from pathlib import Path


def get_engine_path():
    """
    Получить путь к движку
    """
    current_dir = Path(__file__).parent
    template_path = current_dir.parent / 'core'
    return template_path


def copy_directory_contents(src, dst):
    # Проверяем, существует ли исходный каталог
    if not os.path.exists(src):
        raise ValueError(f"Источник {src} не существует!")

    # Создаем целевой каталог, если его нет
    os.makedirs(dst, exist_ok=True)

    # Рекурсивно копируем файлы и папки
    for item in os.listdir(src):
        src_path = os.path.join(src, item)
        dst_path = os.path.join(dst, item)

        if os.path.isdir(src_path):
            shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
        else:
            shutil.copy2(src_path, dst_path)

def init_engine():
    copy_directory_contents(get_engine_path(), './')


def update_engine():
    pass

# def render_template(template_path, output_path, context):
#     """
#     Рендеринг шаблона с контекстом
#     """
#     env = Environment(
#         loader=FileSystemLoader(template_path),
#         keep_trailing_newline=True,
#         autoescape=False
#     )
#
#     for root, dirs, files in os.walk(template_path):
#         relative_root = Path(root).relative_to(template_path)
#
#         for dir_name in dirs:
#             target_dir = output_path / relative_root / dir_name
#             target_dir.mkdir(parents=True, exist_ok=True)
#
#         for file_name in files:
#             if file_name.endswith('.j2'):
#                 # Рендерим Jinja2 шаблоны
#                 template_file = (relative_root / file_name).as_posix()
#                 template = env.get_template(template_file)
#                 content = template.render(**context)
#
#                 output_file = output_path / relative_root / file_name.replace('.j2', '')
#                 output_file.write_text(content, encoding='utf-8')
#             else:
#                 # Копируем обычные файлы
#                 src_file = Path(root) / file_name
#                 dst_file = output_path / relative_root / file_name
#                 dst_file.write_bytes(src_file.read_bytes())

