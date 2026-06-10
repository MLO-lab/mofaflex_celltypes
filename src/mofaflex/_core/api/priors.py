from ..priors import Prior
from . import _generate

_generate.init_api(__name__, Prior, Prior.known_priors())
