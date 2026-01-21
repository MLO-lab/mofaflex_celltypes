import numpy as np
import pytest

from mofaflex._core.priors import APIType, Normal, Prior
from mofaflex._core.terms import MofaFlex, mofaflex
from mofaflex._core.utils import MeanStd


class DummyPrior(Prior):
    _factors = True
    _weights = False
    _state_attrs = ("_prop", "_meanstdprop")

    n_factors = 15
    subset_prop = slice(5, 10)
    n_subset_factors = 5

    def __init__(self, names, rng):
        super().__init__(names.keys())
        self._prop = 6.6743e-11
        self._meanstdprop = MeanStd({"test": 2.7182818284}, {"test": 1.6180339887})
        self._customsave = 1.602176634e-19
        self._rng = rng
        self.nsamples = names

        self._prop_factors = {
            name: self._rng.random((nsamples, self.n_factors)) for name, nsamples in self.nsamples.items()
        }
        self._prop_factors_subset = {
            name: self._rng.random((nsamples, self.n_subset_factors)) for name, nsamples in self.nsamples.items()
        }
        self._method_factors = {
            name: self._rng.random((nsamples, self.n_factors)) for name, nsamples in self.nsamples.items()
        }
        self._method_factors_subset = {
            name: self._rng.random((nsamples, self.n_subset_factors)) for name, nsamples in self.nsamples.items()
        }

    @Prior._api
    @property
    def prop_nofactors(self):
        return 42

    @Prior._api(has_factors=True)
    @property
    def prop_a̲x̲i̲s̲(self):
        return self._prop_factors

    @Prior._api(has_factors=True, factors_subset="subset_prop")
    @property
    def prop_factors_subset(self):
        return self._prop_factors_subset

    @Prior._api(has_factors=False)
    def method_nofactors(self):
        return 3.1415926535

    @Prior._api
    def method_factors(self):
        return self._method_factors

    @Prior._api(factors_subset="subset_prop")
    def method_a̲x̲i̲s̲_subset(self):
        return self._method_factors_subset

    def posterior(self):
        pass

    def _save(self):
        return {"customsave": self._customsave}

    def _load(self, state, map_location):
        self._customsave = state["customsave"]


mofaflex._apinames = mofaflex._init_api()


@pytest.fixture
def dummyprior(rng):
    return DummyPrior({"name_1": 4, "name_2": 5}, rng)


def compare_dict_of_dfs(a, b, b_order=slice(None)):
    assert a.keys() == b.keys()
    for k, df in a.items():
        assert np.all(df == b[k][:, b_order])


def test_api():
    for api in DummyPrior.api():
        if api.name == "prop_nofactors":
            assert api.type == APIType.property
            assert api.has_factors is False
            assert api.factors_subset is None
        elif api.name == "prop_factors":
            assert api.type == APIType.property
            assert api.has_factors is True
            assert api.factors_subset is None
        elif api.name == "prop_factors_subset":
            assert api.type == APIType.property
            assert api.has_factors is True
            assert api.factors_subset == "subset_prop"
        elif api.name == "method_nofactors":
            assert api.type == APIType.method
            assert api.has_factors is False
            assert api.factors_subset is None
        elif api.name == "method_factors":
            assert api.type == APIType.method
            assert api.has_factors is True
            assert api.factors_subset is None
        elif api.name == "method_factors_subset":
            assert api.type == APIType.method
            assert api.has_factors is True
            assert api.factors_subset == "subset_prop"

    for meth in DummyPrior.api_methods():
        assert meth.type == APIType.method

    for prop in DummyPrior.api_properties():
        assert prop.type == APIType.property


def test_dynamic_api(rng, dummyprior):
    term = MofaFlex(n_factors=dummyprior.n_factors, factor_prior=(dummyprior,), weight_prior=(Normal,))
    term._init_api()
    term._device = "cpu"
    term._sample_names = {
        name: np.asarray([f"{name}_{i}" for i in range(nsamples)]) for name, nsamples in dummyprior.nsamples.items()
    }
    term._factor_names = np.asarray(term.factor_names)
    term.factor_order = rng.choice(dummyprior.n_factors, size=dummyprior.n_factors, replace=False)

    factor_order_subset = term.factor_order[dummyprior.subset_prop]
    factor_order_subset[np.argsort(factor_order_subset)] = np.arange(len(factor_order_subset))

    assert term.prop_nofactors == dummyprior.prop_nofactors

    factors = term.get_prop_factor()
    compare_dict_of_dfs(factors, dummyprior.prop_a̲x̲i̲s̲)
    assert all(np.all(fcs.columns == term.factor_names) for fcs in factors.values())

    factors = term.get_prop_factor(ordered=True)
    compare_dict_of_dfs(factors, dummyprior.prop_a̲x̲i̲s̲, term.factor_order)
    assert all(np.all(fcs.columns == term.factor_names[term.factor_order]) for fcs in factors.values())

    factors = term.get_prop_factors_subset()
    compare_dict_of_dfs(factors, dummyprior.prop_factors_subset)
    assert all(np.all(fcs.columns == term.factor_names[dummyprior.subset_prop]) for fcs in factors.values())

    factors = term.get_prop_factors_subset(ordered=True)
    compare_dict_of_dfs(factors, dummyprior.prop_factors_subset, factor_order_subset)
    assert all(
        np.all(fcs.columns == term.factor_names[dummyprior.subset_prop][factor_order_subset])
        for fcs in factors.values()
    )

    assert term.method_nofactors() == dummyprior.method_nofactors()
    with pytest.raises(TypeError, match="unexpected keyword argument"):
        assert term.method_nofactors(ordered=True) == dummyprior.method_nofactors()

    factors = term.method_factors()
    compare_dict_of_dfs(factors, dummyprior.method_factors())
    assert all(np.all(fcs.columns == term.factor_names) for fcs in factors.values())

    factors = term.method_factors(ordered=True)
    compare_dict_of_dfs(factors, dummyprior.method_factors(), term.factor_order)
    assert all(np.all(fcs.columns == term.factor_names[term.factor_order]) for fcs in factors.values())

    factors = term.method_factor_subset()
    compare_dict_of_dfs(factors, dummyprior.method_a̲x̲i̲s̲_subset())
    assert all(np.all(fcs.columns == term.factor_names[dummyprior.subset_prop]) for fcs in factors.values())

    factors = term.method_factor_subset(ordered=True)
    compare_dict_of_dfs(factors, dummyprior.method_a̲x̲i̲s̲_subset(), factor_order_subset)
    assert all(
        np.all(fcs.columns == term.factor_names[dummyprior.subset_prop][factor_order_subset])
        for fcs in factors.values()
    )


def test_saveload(dummyprior):
    state = dummyprior.save()
    loaded = DummyPrior.load(state)

    assert dummyprior._prop == loaded._prop
    assert dummyprior._meanstdprop == loaded._meanstdprop
    assert dummyprior._customsave == loaded._customsave
