import click
from systemloader.commands.add import add_project

@click.group()
def main():
    """MyLib - Custom project generator"""
    pass

# Добавляем команду add
@main.command()
@click.argument('command')
@click.argument('project_name')
@click.option('--template', default='default', help='Template to use')
def add(command, project_name, template):
    """Add new project or component"""
    if command == 'project':
        add_project(project_name, template)
    else:
        click.echo(f"Unknown command: {command}")

if __name__ == '__main__':
    main()
