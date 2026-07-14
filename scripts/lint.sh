# install requirements
pip install ruff mypy --upgrade --quiet

# run ruff and mypy

echo Running Ruff/Check...
ruff check --output-format=github --target-version=py314

echo Running Ruff/Format Diff...
ruff format --diff --target-version=py314

echo Running MyPy...
mypy shapeddataclass
