from setuptools import setup

setup(
    name="asdf_validate",
    version="0.1",
    py_modules=["asdf_validate"],
    install_requires=["h5py"],
    entry_points="""
        [console_scripts]
        asdf-validate=asdf_validate.validator:main
    """
)
