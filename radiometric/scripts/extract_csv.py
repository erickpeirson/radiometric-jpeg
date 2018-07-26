import os
import warnings

import click

warnings.filterwarnings("ignore", message="numpy.dtype size changed")
warnings.filterwarnings("ignore", message="numpy.ufunc size changed")

from ..dataset import Dataset


@click.command()
@click.option('--source', prompt="Directory containing radiometric JPEGs")
@click.option('--dest', prompt="Output directory for CSV files")
def extract_csv(source: str, dest: str) -> None:
    """
    Extract temperature values from radiometric JPEG.

    Parameters
    ----------
    source : str
        Absolute path to a directory containing radiometric JPEGs.
    dest : str
        Absolute path to a directory where CSV data should be stored. Will
        attempt to create the directory if it does not already exist.

    """
    if not os.path.exists(source):
        raise click.BadParameter("Source path does not exist!")
    if not os.path.exists(dest):
        try:
            os.makedirs(dest)
        except OSError:
            raise click.BadParameter("Could not create output directory. Do"
                                     " you have write access?")

    dataset = Dataset(source)
    if len(dataset.params) < 2 or dataset.params.shape[1] == 0:
        raise click.BadParameter("Source path does not contain radiometric"
                                 " JPEG images")
    with click.progressbar(dataset.images) as bar:
        for image in bar:
            image.to_csv(dest)


if __name__ == '__main__':
    extract_csv()
