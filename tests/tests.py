from unittest import TestCase
import os
import tempfile

import csv
import numpy as np

from radiometric.metadata import ImageMetadata
from radiometric.image import RadiometricImage
from radiometric.dataset import Dataset


class TestImageMetadata(TestCase):
    def setUp(self):
        self.path = os.path.abspath(
            os.path.join("tests", "data", "20180704_110606_882.JPG")
        )

    def test_metadata(self):
        """Loads image metadata from EXIF record."""
        meta = ImageMetadata(self.path)
        self.assertEqual(meta.T_min, 4.52,
                         "The coolest temperature is 4.52 °C")
        self.assertEqual(meta.T_max, 31.07,
                         "The hottest temperature is 31.07 °C")


class TestImage(TestCase):
    def setUp(self):
        self.path = os.path.abspath(
            os.path.join("tests", "data", "20180704_110606_882.JPG")
        )

    def test_image(self):
        """Loads image content from radiometric JPEG."""
        image = RadiometricImage(self.path)
        self.assertIsInstance(image.meta, ImageMetadata,
                              "Loads image metadata")
        self.assertEqual(image.meta.T_min, 4.52,
                         "The coolest temperature is 4.52 °C")
        self.assertEqual(image.meta.T_max, 31.07,
                         "The hottest temperature is 31.07 °C")

        self.assertTrue(os.path.exists(image.raw), "Extracts raw IR data")
        self.assertEqual(os.stat(image.raw).st_size, 38_622,
                         "Raw IR TIFF has the expected size")

    def test_export_csv(self):
        tempdir = tempfile.mkdtemp()
        image = RadiometricImage(self.path)
        csv_path = image.to_csv(tempdir)
        self.assertTrue(os.path.exists(csv_path), "Creates a CSV file")
        with open(csv_path) as f:
            data = np.array([[float(v) for v in row] for row in csv.reader(f)])
        self.assertEqual(data.shape, (160, 120),
                         "CSV output has the expected dimensions")
        self.assertEqual((data.min(), data.max()), (11.0, 34.37),
                         "Data has expected minimum and maximum values")

    def test_export_tiff(self):
        tempdir = tempfile.mkdtemp()
        image = RadiometricImage(self.path)
        tiff_path = image.to_tiff(tempdir)
        self.assertTrue(os.path.exists(tiff_path), "Creates a TIFF file")
        self.assertEqual(os.stat(tiff_path).st_size,
                         os.stat(image.raw).st_size,
                         "IR TIFF is the same size as the raw IR TIFF.")


class TestDataset(TestCase):
    def setUp(self):
        self.path = os.path.abspath(os.path.join("tests", "data"))

    def test_dataset(self):
        dataset = Dataset(self.path)
        self.assertEqual(dataset.params.shape, (7, 2),
                         "Dataset parameter array has the expected shape")
        self.assertEqual((round(dataset.S_min, 9), round(dataset.S_max, 9)),
                         (278.792279081, 303.527227566),
                         "Loaded expected min and max scaling values.")

        for img in dataset.images:
            self.assertIsInstance(img, RadiometricImage)
