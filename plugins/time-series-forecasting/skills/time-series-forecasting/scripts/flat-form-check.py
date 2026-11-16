"""For each subset window, fit the flat form ETS(A,N,N) and the additive-season form ETS(A,N,A) on the same history, and count where the seasonal fit has the lower likelihood.
The two counts printed last are the ones the prose quotes."""
import numpy as np
import pandas as pd
from statsforecast import StatsForecast
from statsforecast.models import AutoETS

from lib.electricity import load
from lib.quirks import filled_history, mask_clock_changes
from lib.settings import EVAL_CUTOFFS, SEED, SUBSET8, show

np.random.seed(SEED)                                        # the seed from lib/settings.py, set before any fit
masked = mask_clock_changes(load(SUBSET8))
windows = seasonal_lower_loglik = seasonal_higher_aicc = 0
for c in pd.to_datetime(EVAL_CUTOFFS):
    hist = filled_history(masked, c)[["unique_id", "ds", "y"]]
    # ANN is additive error, no trend, no season: the flat form. ANA is the same with an additive season.
    sf = StatsForecast(models=[AutoETS(model="ANN", season_length=24, alias="flat"),
                               AutoETS(model="ANA", season_length=24, alias="seasonal")], freq="h", n_jobs=1)
    sf.fit(df=hist)
    for i in range(len(sf.uids)):
        flat = sf.fitted_[i, 0].model_                          # models are fitted in the order listed: 0 is the flat fit
        seasonal = sf.fitted_[i, 1].model_                      # 1 is the seasonal fit
        windows += 1
        # ANA contains ANN, so a lower seasonal likelihood points to a fit that stopped short of its best
        seasonal_lower_loglik += int(seasonal["loglik"] < flat["loglik"])
        # AICc charges each parameter, so this count can differ from the likelihood count
        seasonal_higher_aicc += int(seasonal["aicc"] > flat["aicc"])
show("windows", windows)
show("seasonal fit has the lower log-likelihood", seasonal_lower_loglik)
show("seasonal fit has the higher AICc", seasonal_higher_aicc)
