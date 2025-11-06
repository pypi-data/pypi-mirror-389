# process
 - [pyproject.toml](../pyproject.toml) modify version info
 - cd D:\git_geeker\geeker_dev\python_dev\itgeeker_package
 - python -m build
 - pip install D:\git_geeker\geeker_dev\python_dev\itgeeker_package\dist\itgeeker-0.2.5-py3-none-any.whl
 - twine publish to pypi.org:   twine upload dist/itgeeker-0.2.4* --verbose
 - pypi-AgEIcHlwaS5vcmcCJDU5N2Q1MDdlLWFmZDgtNGNjNC05M2Q5LWE5NGZhYjI1MmFmZgACKlszLCJmYzg2ODlkYy1lMmQxLTQxNzktYmU1Yi03MzAxNjQ0NTRhMDgiXQAABiDNCsuWZ6jpQzvszdqu6D-SNbwEZECFqDW6i_A6za4dEA


# build method
pip install build
python -m build
or
uv build
or
hatch build /path/to/project


[//]: # (pip install itgeeker -i https://pypi.tuna.tsinghua.edu.cn/simple)
pip install itgeeker -i https://pypi.org/simple


pip install -e .
or
uv run src\itgeeker\main.py

# layout
flat layout
src layout

# setuptools
```ini
[build-system]
requires = ["setuptools>=40.8.0"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
```

# hatchling
https://pypi.org/project/hatchling/
https://hatch.pypa.io/latest/
pip install hatchling
add __init__.py
```ini
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```


# build with Hatch
hatch build /path/to/project

# twine
https://pypi.org/project/twine/
pip install twine
cd /d D:\git_geeker\geeker_dev\python_dev\itgeeker_package
twine upload dist/itgeeker-0.2.4*
twine upload dist/itgeeker-0.2.4* --verbose

2025-09-11
Token for "itgeeker"
Permissions: Upload packages
Scope: Entire account (all projects)
pypi-AgEIcHlwaS5vcmcCJDU5N2Q1MDdlLWFmZDgtNGNjNC05M2Q5LWE5NGZhYjI1MmFmZgACKlszLCJmYzg2ODlkYy1lMmQxLTQxNzktYmU1Yi03MzAxNjQ0NTRhMDgiXQAABiDNCsuWZ6jpQzvszdqu6D-SNbwEZECFqDW6i_A6za4dEA

Using this token
To use this API token:
◦ Set your username to __token__
◦ Set your password to the token value, including the pypi- prefix
For example, if you are using Twine to upload your projects to PyPI, set up your $HOME/.pypirc file like this:
```ini
[pypi]
  username = __token__
  password = pypi-AgEIcHlwaS5vcmcCJDU5N2Q1MDdlLWFmZDgtNGNjNC05M2Q5LWE5NGZhYjI1MmFmZgACKlszLCJmYzg2ODlkYy1lMmQxLTQxNzktYmU1Yi03MzAxNjQ0NTRhMDgiXQAABiDNCsuWZ6jpQzvszdqu6D-SNbwEZECFqDW6i_A6za4dEA
```
For further instructions on how to use this token, visit the PyPI help page.

https://pypi.org/project/itgeeker/0.1.0/
https://pypi.org/project/itgeeker/0.2.0/