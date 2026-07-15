# install requirements
pip install sphinx pydata-sphinx-theme --upgrade --quiet

# delete previous versions
rm -rf docs/build
rm -rf docs/source/_autogen

# build ReST from source
sphinx-apidoc -o docs/source/_autogen bufferstruct

# build documentation from ReST
sphinx-build -M html docs/source docs/build
