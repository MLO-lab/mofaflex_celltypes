def _generate():
    from types import ModuleType

    from ..likelihoods import Likelihood
    from ..terms import Term
    from .utils import DynamicAPIWrapper

    for docsapi, basecls, subclss in (
        ("terms", Term, Term.known_terms()),
        ("likelihoods", Likelihood, Likelihood.known_likelihoods()),
    ):
        mod = ModuleType(docsapi)
        for clsname, subcls in subclss.items():
            setattr(mod, clsname, DynamicAPIWrapper[subcls])
        setattr(mod, basecls.__name__, DynamicAPIWrapper[basecls])
        globals()[docsapi] = mod


_generate()
