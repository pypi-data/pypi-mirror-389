import click
from systemloader.commands.update import init_engine


@click.group()
def main():
    """systemloader"""
    pass


@main.command()
def hello():
    init_engine()
    click.echo('Engine OK!')


@main.command()
def update():
    click.echo('Update')


if __name__ == '__main__':
    main()
