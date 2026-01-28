from ..priors import Prior
from ..utils import docstring_get_indentation as _indent
from . import _generate


def _doc_callback(doc: str | None, priorcls: type[Prior]):
    if (f := priorcls.factors_allowed()) != priorcls.weights_allowed():
        msg = (".. important::\n", f"   This prior can only be used for {'factors' if f else 'weights'}.\n")
        if doc is None:
            return "".join(msg)
        else:
            indent = _indent(doc)
            lines = doc.splitlines(keepends=True)
            return "".join((lines[0], "\n", *(" " * indent + cmsg for cmsg in msg), *lines[1:]))
    else:
        return doc


_generate.init_api(__name__, Prior, Prior.known_priors(), _doc_callback)
