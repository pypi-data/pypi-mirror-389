from __future__ import annotations

from typing import TYPE_CHECKING

from sphinx.util.typing import ExtensionMetadata
from sphinxcontrib.kasane import new_translator_class_for_builder

if TYPE_CHECKING:
    from sphinx.application import Sphinx

__version__ = "0.0.1"


class DeckMarkdownTranslatorMixin:
    _FIRST_SECTION_PROCESSED = False

    def visit_section(self, node):
        if self._FIRST_SECTION_PROCESSED:
            self.add("---", prefix_eol=2, suffix_eol=2)

        super().visit_section(node)

        if not self._FIRST_SECTION_PROCESSED:
            self._FIRST_SECTION_PROCESSED = True
        else:
            self._push_status(section_level=2)


def setup(app: Sphinx) -> ExtensionMetadata:
    markdown_translator_handler = new_translator_class_for_builder(
        "markdown", DeckMarkdownTranslatorMixin, "DeckMarkdownTranslator"
    )
    app.connect("builder-inited", markdown_translator_handler)

    return ExtensionMetadata(version=__version__, parallel_read_safe=True)
