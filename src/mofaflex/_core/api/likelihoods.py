from ..likelihoods import Likelihood
from . import _generate

_generate.init_api(__name__, Likelihood, Likelihood.known_likelihoods())
