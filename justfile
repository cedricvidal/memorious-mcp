build:
    uv run python -m build

upload-testpypi:
    uv run --with twine twine upload --repository testpypi dist/*

upload-pypi:
    uv run --with twine twine upload --repository pypi dist/*

run-from-testpypi:
    uvx --default-index https://test.pypi.org/simple/ --index https://pypi.org/simple/ memorious-mcp

run-from-pypi:
    uvx memorious-mcp
