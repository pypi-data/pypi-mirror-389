from setuptools import setup, find_packages

setup(
    name="vanrickshaw",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["Pillow"],
    entry_points={
        'console_scripts': [
            'van=van.banik:run',
        ],
    },
    author="Souparno",
    description="Rickshaw ASCII art animation in terminal",
)
