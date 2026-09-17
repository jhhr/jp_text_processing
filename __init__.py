"""Japanese furigana, reading and word-highlighting processing.

`kana_highlight` and `word_highlight` are re-exported lazily: importing them eagerly here
would pull most of the package (and the mecab controller) into `sys.modules` before any
submodule is reached, so running one as a script -- `python -m jp_text_processing.kana.
kana_highlight_tests` from this directory's parent -- would execute it a second time under
the name `__main__`, duplicating its module-level state.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .kana.kana_highlight import kana_highlight
    from .word.word_highlight import word_highlight

__all__ = ["kana_highlight", "word_highlight"]

_LAZY_MODULES = {
    "kana_highlight": ".kana.kana_highlight",
    "word_highlight": ".word.word_highlight",
}


def __getattr__(name: str) -> Any:
    module_name = _LAZY_MODULES.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from importlib import import_module

    return getattr(import_module(module_name, __name__), name)
