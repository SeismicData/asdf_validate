from setuptools import setup

setup(
    name="asdf_validate",
    version="0.1",
    py_modules=["validator"],
    install_requires=["h5py"],
    entry_points="""
        [console_scripts]
        asdf-validate=validator:main
    """
)
