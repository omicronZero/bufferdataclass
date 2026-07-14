# install build script
python -m pip install build twine --upgrade --quiet

# build package to dist-directory
python -m build

# test built distribution for errors
twine check dist dist/* --strict
