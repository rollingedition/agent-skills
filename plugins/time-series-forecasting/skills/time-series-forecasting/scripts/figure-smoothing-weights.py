"""Draw the weight exponential smoothing gives each of the last 24 readings, for alpha 0.2 and 0.5.
The lines name the weight on the newest reading, how many readings hold half the weight, and what is left past a day."""
import numpy as np

from lib.figures import ACCENT, MUTED, new_figure, save
from lib.settings import show

ages = np.arange(24)                                            # 0 is the newest reading, 23 the oldest in a day
fig, ax = new_figure(height=2.6)
for alpha, color in ((0.2, MUTED), (0.5, ACCENT)):
    weights = alpha * (1 - alpha) ** ages                       # level_t = alpha*y_t + (1-alpha)*level_(t-1), unrolled
    half = int(np.argmax(np.cumsum(weights) >= 0.5)) + 1        # the fewest newest readings that carry half the weight
    show(f"weight on the newest reading, alpha {alpha}", weights[0])
    show(f"readings that carry half the weight, alpha {alpha}", half)
    show(f"weight left on readings older than a day, alpha {alpha}", (1 - alpha) ** 24, digits=4)
    ax.plot(ages, weights, color=color, marker="o", markersize=3, linewidth=1.4, label=f"alpha = {alpha}")
ax.set_xlabel("age of the reading, hours")
ax.set_ylabel("weight in the level")
ax.set_ylim(bottom=0)
ax.legend(frameon=False)
save(fig, "smoothing-weights")
