import click

from playwright import __version__
from playwright.config import PlaywrightConfig
from playwright.error import PlaywrightUnsupportedError
from playwright.inspired import InspiredPlaybook
from playwright.playhouse.nifcloud import NifcloudPlayhouse


@click.group()
def cli():
    pass


@cli.command()
@click.option('--output-file', '-f', default=False, is_flag=True, help='output to file')
@click.argument('inspiration_path', type=click.Path(exists=True))
def inspire(output_file, inspiration_path):
    config = PlaywrightConfig()
    config.load_file(inspiration_path)

    playbook = InspiredPlaybook(config)

    for inspiration in config.inspirations:
        if inspiration['playhouse'] == 'nifcloud':
            playhouse = NifcloudPlayhouse()
            playhouse.init(config, inspiration)
            inspired = playhouse.inspire()
            playbook.append_inspired(inspired)
        else:
            raise PlaywrightUnsupportedError('unsuppouted playhouse: {}'.format(inspiration['playhouse']))

    _output_playbook(playbook, output_file)


def _output_playbook(playbook, output_to_file=False):
    playbook_content = playbook.render()

    if not output_to_file:
        click.echo(playbook_content)
        return

    output_path = playbook.generate_output_path()
    with open(output_path, "w") as file:
        file.write(playbook_content)
        click.echo(output_path)


@cli.command()
def version():
    click.echo(__version__)


if __name__ == '__main__':
    cli()
