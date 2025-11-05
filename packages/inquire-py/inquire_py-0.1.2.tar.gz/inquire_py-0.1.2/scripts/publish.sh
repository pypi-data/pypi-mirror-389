#!/usr/bin/env bash
set -euo pipefail

echo "==> Building package..."
uv build

echo ""
echo "==> Built distribution files:"
ls -lh dist/

echo ""
echo "==> To upload to TestPyPI (recommended first):"
echo "    uv publish --publish-url https://test.pypi.org/legacy/ --token \$TEST_PYPI_TOKEN"
echo ""
echo "==> To upload to PyPI (production):"
echo "    uv publish --token \$PYPI_TOKEN"
echo ""
echo "==> After publishing to TestPyPI, test installation with:"
echo "    pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ inquire-py"
echo ""
echo "==> After publishing to PyPI, users can install with:"
echo "    pip install inquire-py"
