# Makefile for repsim (pybind11 + scikit-build-core)
# Local-only workflow (no cibuildwheel/CI required)

# Usage:
#   make develop       # editable install
#   make install       # regular install
#   make uninstall     # uninstall package
#   make build         # wheel + sdist -> dist/
#   make wheel         # wheel only
#   make sdist         # sdist only
#   make verify        # ensure wheel contains repsim/_repsim.*
#   make install-wheel # pip install latest wheel from dist/
#   make check         # twine metadata check
#   make release       # clean + build + verify + check + upload to PyPI
#   make release-test  # same but to TestPyPI
#   make clean         # remove build artifacts
#   make deepclean     # clean + remove extra caches
#   make rebuild       # clean + develop
#   make info          # print env info
#   make help          # show this help

# --- Config ---
PYTHON ?= python
PIP    ?= $(PYTHON) -m pip
PKG    ?= repsim

# --- Helpers ---
define PRINT_HELP
@echo "Targets:"
@echo "  develop         Editable install (pip install -e .)"
@echo "  install         Regular install (pip install .)"
@echo "  uninstall       Uninstall package ($(PKG))"
@echo "  build           Build wheel + sdist into dist/"
@echo "  wheel           Build wheel only into dist/"
@echo "  sdist           Build sdist only into dist/"
@echo "  verify          Verify wheel bundles compiled extension (repsim/_repsim.*)"
@echo "  install-wheel   Pip install latest wheel from dist/"
@echo "  check           Validate dist/* with twine"
@echo "  release         Clean + build + verify + check + upload to PyPI"
@echo "  release-test    Clean + build + verify + check + upload to TestPyPI"
@echo "  clean           Remove build artifacts and caches"
@echo "  deepclean       Clean + remove extra caches (cmake, mypy, etc.)"
@echo "  rebuild         clean + develop"
@echo "  info            Show Python/build environment info"
@echo "  help            Show this help"
endef

.PHONY: develop install uninstall build wheel sdist verify install-wheel check release release-test clean deepclean rebuild info help

help:
	$(PRINT_HELP)

info:
	@echo "==> Python:"
	@$(PYTHON) -c "import sys,platform; print(sys.version); print(platform.platform())"
	@echo "==> pip:"
	@$(PIP) --version
	@echo "==> build/twine present?"
	@$(PYTHON) -c "import importlib; print('build:', bool(importlib.util.find_spec('build')),'twine:', bool(importlib.util.find_spec('twine')))"

develop:
	$(PIP) install -e .

install:
	$(PIP) install .

uninstall:
	-$(PIP) uninstall -y $(PKG)

wheel:
	$(PYTHON) -m build --wheel --outdir dist

sdist:
	$(PYTHON) -m build --sdist --outdir dist

build:
	$(PYTHON) -m build --wheel --outdir dist
	$(PYTHON) -m build --sdist --outdir dist

# Ensure the built wheel actually contains the compiled extension.
# Fails fast if not found.
verify:
	@set -e; \
	WHEEL=$$(ls -1t dist/*.whl 2>/dev/null | head -n1); \
	[ -n "$$WHEEL" ] || { echo "No wheel in dist/. Run 'make wheel' first."; exit 1; }; \
	echo "==> Verifying wheel: $$WHEEL"; \
	$(PYTHON) -c 'import sys,zipfile,fnmatch; z=zipfile.ZipFile(sys.argv[1]); n=z.namelist(); \
need=["repsim/_utils.py"]; \
miss=[p for p in need if p not in n]; \
ext=[p for p in n if "repsim/_repsim." in p]; \
func=[p for p in n if fnmatch.fnmatch(p,"repsim/_func_*.py")]; \
print("missing:", miss); print("ext:", ext); print("func:", func); \
assert not miss, "Missing support modules in wheel: "+str(miss); \
assert ext, "Missing compiled extension repsim/_repsim.*"; \
assert func, "Missing _func_*.py modules"' "$$WHEEL"


install-wheel:
	@set -e; \
	WHEEL=$$(ls -1t dist/*.whl 2>/dev/null | head -n1); \
	if [ -z "$$WHEEL" ]; then \
	  echo "No wheel in dist/. Run 'make wheel' or 'make build' first."; exit 1; \
	fi; \
	echo "==> Installing $$WHEEL"; \
	$(PIP) install "$$WHEEL" --force-reinstall

check:
	@$(PYTHON) -c "import twine" 2>/dev/null || { \
	  echo 'twine not found. Install with: $(PYTHON) -m pip install -U twine'; exit 1; }
	@test -d dist && ls dist/* >/dev/null 2>&1 || { \
	  echo 'No artifacts in dist/. Run `make build` first.'; exit 1; }
	$(PYTHON) -m twine check dist/*

# Conservative release to PyPI:
# - clean (avoid stale artifacts)
# - build wheel+sdist
# - verify presence of compiled extension in wheel
# - twine check metadata
# - require TWINE_* env vars
release: clean build verify check
	@if [ -z "$$TWINE_USERNAME" ] || [ -z "$$TWINE_PASSWORD" ]; then \
	  echo "Set TWINE_USERNAME=__token__ and TWINE_PASSWORD=pypi-<YOUR_PYPI_TOKEN>"; exit 1; fi
	$(PYTHON) -m twine upload dist/*

# Optional: release to TestPyPI (sandbox)
release-test: clean build verify check
	@if [ -z "$$TWINE_USERNAME" ] || [ -z "$$TWINE_PASSWORD" ]; then \
	  echo "Set TWINE_USERNAME=__token__ and TWINE_PASSWORD=pypi-<YOUR_TESTPYPI_TOKEN>"; exit 1; fi
	$(PYTHON) -m twine upload --repository testpypi dist/*

clean:
	@echo "Cleaning build artifacts..."
	@rm -rf \
		build/ \
		_skbuild/ \
		dist/ \
		*.egg-info \
		.eggs \
		.pytest_cache \
		.mypy_cache \
		.ruff_cache \
		.nox \
		.tox \
		**/__pycache__
	@# Remove compiled extensions if present (adjust if needed)
	@find ./repsim -maxdepth 1 -name "_$(PKG).*so"  -delete 2>/dev/null || true
	@find ./repsim -maxdepth 1 -name "_$(PKG).*pyd" -delete 2>/dev/null || true
	@find ./repsim -maxdepth 1 -name "_$(PKG).*dll" -delete 2>/dev/null || true
	@find ./repsim -maxdepth 1 -name "_$(PKG).*dylib" -delete 2>/dev/null || true

deepclean: clean
	@rm -rf \
		.cache \
		CMakeCache.txt \
		CMakeFiles/ \
		**/.cmake/api \
		**/.cmake/packages \
		**/.cmake/*

rebuild: clean develop