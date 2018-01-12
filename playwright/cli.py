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
@click.option('--output', '-o', default=None, help='output file path')
@click.argument('inspiration_path', type=click.Path(exists=True))
def inspire(output, inspiration_path):
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

    _output_playbook(playbook)


def _output_playbook(playbook):
    playbook_content = playbook.render()
    click.echo(playbook_content)


@cli.command()
def version():
    click.echo(__version__)


if __name__ == '__main__':
    cli()
