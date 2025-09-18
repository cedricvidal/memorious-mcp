build:
    rm -rf ./dist/*
    uv run python -m build

upload-testpypi:
    uv run --with twine twine upload --repository testpypi dist/*

upload-pypi:
    uv run --with twine twine upload --repository pypi dist/*

run-from-testpypi:
    uvx --default-index https://test.pypi.org/simple/ --index https://pypi.org/simple/ memorious-mcp

run-from-pypi:
    uvx memorious-mcp

install-mcp-publisher:
    curl -L "https://github.com/modelcontextprotocol/registry/releases/download/v1.0.0/mcp-publisher_1.0.0_$(uname -s | tr '[:upper:]' '[:lower:]')_$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/').tar.gz" | tar xz mcp-publisher

mcp-login:
    ./mcp-publisher login github-oidc

mcp-upload:
    ./mcp-publisher publish
