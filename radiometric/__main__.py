import os
import click

from .dataset import Dataset


@click.command()
@click.option('--source', prompt="Directory containing radiometric JPEGs")
@click.option('--dest', prompt="Output directory for CSV files")
def extract_csv(source: str, dest: str) -> None:
    if not os.path.exists(source):
        raise click.BadParameter("Source path does not exist!", param=source)
    if not os.path.exists(dest):
        try:
            os.makedirs(dest)
        except OSError:
            raise click.BadParameter("Could not create output directory. Do"
                                     " you have write access?", param=dest)

    dataset = Dataset(source)
    if not dataset.params.shape[1] > 0:
        raise click.BadParameter("Source path does not contain radiometric"
                                 " JPEG images", param=source)
    with click.progressbar(dataset.images) as bar:
        for image in bar:
            image.to_csv(dest, image.convert_fnx(dataset.S_min, dataset.S_max))


if __name__ == '__main__':
    extract_csv()
