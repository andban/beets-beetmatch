import math

import pytest

from beetsplug.beetmatch.common.helpers import import_optional


class TestOptionalImport:

    def test_existing_import_module(self):
        imported = import_optional("math")

        assert imported == math

    def test_existing_import_symbol(self):
        imported = import_optional("math", symbol="pi")

        assert imported == math.pi

    def test_raise_on_missing_import(self):
        with pytest.raises(ImportError):
            import_optional("grindcore4python")

    def test_warn_on_missing_import(self):
        with pytest.warns(UserWarning):
            import_optional("python4grindcore", error="warn")
