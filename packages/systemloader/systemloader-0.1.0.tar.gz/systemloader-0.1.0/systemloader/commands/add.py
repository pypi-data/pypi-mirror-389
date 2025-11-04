import os
import click
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


def get_template_path(template_name):
    """
    Получить путь к шаблону
    """
    current_dir = Path(__file__).parent
    template_path = current_dir.parent / 'core' / 'templates' / template_name
    return template_path

def render_template(template_path, output_path, context):
    """
    Рендеринг шаблона с контекстом
    """
    env = Environment(
        loader=FileSystemLoader(template_path),
        keep_trailing_newline=True,
        autoescape=False
    )

    for root, dirs, files in os.walk(template_path):
        relative_root = Path(root).relative_to(template_path)

        for dir_name in dirs:
            target_dir = output_path / relative_root / dir_name
            target_dir.mkdir(parents=True, exist_ok=True)

        for file_name in files:
            if file_name.endswith('.j2'):
                # Рендерим Jinja2 шаблоны
                template_file = (relative_root / file_name).as_posix()
                template = env.get_template(template_file)
                content = template.render(**context)

                output_file = output_path / relative_root / file_name.replace('.j2', '')
                output_file.write_text(content, encoding='utf-8')
            else:
                # Копируем обычные файлы
                src_file = Path(root) / file_name
                dst_file = output_path / relative_root / file_name
                dst_file.write_bytes(src_file.read_bytes())

def add_project(project_name, template_name='default'):
    """
    Создать новый проект из шаблона
    """
    template_path = get_template_path(template_name)

    if not template_path.exists():
        click.echo(f"❌ Template '{template_name}' not found!")
        return

    output_path = Path.cwd() / project_name

    if output_path.exists():
        click.echo(f"❌ Directory '{project_name}' already exists!")
        return

        # Контекст для шаблонов
    context = {
        'project_name': project_name,
        'module_name': project_name.replace('-', '_').replace(' ', '_'),
    }

    try:
        click.echo(f"🚀 Creating project '{project_name}'...")
        render_template(template_path, output_path, context)

        click.echo(f"✅ Project '{project_name}' created successfully!")
        click.echo(f"📁 Location: {output_path}")

    except Exception as e:
        click.echo(f"❌ Error creating project: {e}")
        # Удаляем частично созданные файлы при ошибке
        if output_path.exists():
            import shutil
            shutil.rmtree(output_path)
