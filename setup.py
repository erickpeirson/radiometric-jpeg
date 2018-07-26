from setuptools import setup, find_packages

setup(
    name='radiometric',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click",
        "numpy",
        "pandas",
        "attrdict",
        "pillow"
    ],
    entry_points='''
        [console_scripts]
        extract_csv=radiometric.scripts.extract_csv:extract_csv
    ''',
)
