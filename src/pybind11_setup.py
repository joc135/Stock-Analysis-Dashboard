from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup

ext_modules = [
    Pybind11Extension(
        "option_pricing",          # module name
        ["option_pricing.cpp"] # path to cpp file
    ),
]

setup(
    name="option_pricing",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
)
