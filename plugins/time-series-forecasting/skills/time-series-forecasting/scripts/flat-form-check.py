"""For each subset window, fit the flat form ETS(A,N,N) and the additive-season form ETS(A,N,A) on the same history, and compare them."""
import numpy as np
import pandas as pd
from statsforecast import StatsForecast
from statsforecast.models import AutoETS

from lib.electricity import load
from lib.quirks import filled_history, mask_clock_changes
from lib.settings import EVAL_CUTOFFS, SEED, SUBSET8, show

np.random.seed(SEED)
masked = mask_clock_changes(load(SUBSET8))
windows = seasonal_lower_loglik = seasonal_higher_aicc = 0
for c in pd.to_datetime(EVAL_CUTOFFS):
    hist = filled_history(masked, c)[["unique_id", "ds", "y"]]
    sf = StatsForecast(models=[AutoETS(model="ANN", season_length=24, alias="flat"),
                               AutoETS(model="ANA", season_length=24, alias="seasonal")], freq="h", n_jobs=1)
    sf.fit(df=hist)
    for i in range(len(sf.uids)):
        flat = sf.fitted_[i, 0].model_
        seasonal = sf.fitted_[i, 1].model_
        windows += 1
        seasonal_lower_loglik += int(seasonal["loglik"] < flat["loglik"])
        seasonal_higher_aicc += int(seasonal["aicc"] > flat["aicc"])
show("windows", windows)
show("seasonal fit has the lower log-likelihood", seasonal_lower_loglik)
show("seasonal fit has the higher AICc", seasonal_higher_aicc)
