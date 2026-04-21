def _generate():
    from types import ModuleType

    from ..likelihoods import Likelihood
    from ..terms import Term
    from ..utils import building_docs
    from . import likelihoods, terms  # noqa: F401
    from .utils import DynamicAPIWrapper

    for docsapi, basecls, subclss in (
        ("terms", Term, Term.known_terms()),
        ("likelihoods", Likelihood, Likelihood.known_likelihoods()),
    ):
        mod = ModuleType(docsapi)
        if building_docs():
            apimod = locals()[docsapi]
            for wrapper in dir(apimod):
                setattr(mod, wrapper, getattr(apimod, wrapper))
            setattr(mod, basecls.__name__, None)
        else:
            for clsname, subcls in subclss.items():
                setattr(mod, clsname, DynamicAPIWrapper[subcls])
            setattr(mod, basecls.__name__, DynamicAPIWrapper[basecls])
        globals()[docsapi] = mod


_generate()
