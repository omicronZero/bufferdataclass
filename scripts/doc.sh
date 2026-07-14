# install requirements
pip install sphinx pydata-sphinx-theme --upgrade --quiet

# delete previous versions
rm -rf docs/build
rm -rf docs/source/_autogen

# build ReST from source
# TODO: replace python_ci_base
sphinx-apidoc -o docs/source/_autogen python_ci_base

# build documentation from ReST
sphinx-build -M html docs/source docs/build
