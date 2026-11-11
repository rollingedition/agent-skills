# Data card: electricity_hourly.csv.gz

A subset of the UCI *ElectricityLoadDiagrams20112014* dataset, cut to hourly energy for the book's running case.

## Source and licence

- **Dataset:** ElectricityLoadDiagrams20112014, UCI Machine Learning Repository.
  - Page: https://archive.ics.uci.edu/dataset/321/electricityloaddiagrams20112014
  - Download used: https://archive.ics.uci.edu/static/public/321/electricityloaddiagrams20112014.zip
  - Retrieved 2026-11-10.
- **Citation:** Trindade, A. (2015). ElectricityLoadDiagrams20112014 [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C58C86
- **Licence:** CC BY 4.0, https://creativecommons.org/licenses/by/4.0/ (as stated on the UCI page).
- **Raw file checked:** `LD2011_2014.txt`, SHA-256 `d51565f2cb5a6b768d06ba1bbd3c084c6e2f3aab07f00c6f2dcb80e90175124b`
  (inside the zip, SHA-256 of the zip as downloaded `f6c4d0e0df12ecdb9ea008dd6eef3518adb52c559d04a9bac2e1b81dcfc8d4e1`).
- The clients are anonymous. The dataset's own ids (`MT_001` to `MT_370`) are kept.

## What the raw data is

- 370 clients, 140,256 rows of 15-minute consumption, labels from 2011-01-01 00:15 to 2015-01-01 00:00, local Portuguese clock time with no time zone.
- Values are kW averaged over each 15 minutes, with a decimal comma and `;` separators. Each day has 96 rows, whatever the clock change.

## What the output is

- `electricity_hourly.csv.gz`, long format, 525,600 rows, 30 clients by 17,520 hours.
- Columns: `unique_id` (client id), `ds` (start of the hour, local clock time, no time zone), `y` (kWh used in that hour), `quirk` (see below).
- SHA-256 of the file: `03bdee01e4cdae020a51997e2b4400ae82899c84c29348095093fc256b9e7e2b` (2,657,151 bytes).

## How it was cut (`data-prep/prepare.py`)

1. **Window:** 2013-01-01 00:00 to 2014-12-31 23:00, two whole years, 17,520 hours.
2. **Units:** a reading in kW held for 15 minutes is kW × 0.25 kWh, so the four readings of an hour give kWh for that hour, and the hourly kWh equals the mean of the four kW readings. Values are rounded to 3 decimals (watt-hours), half up.
3. **Timestamps:** a reading's label is taken as the start of its 15 minutes, so the four readings labelled H:00 to H:45 make hour H.
4. **Clients:**
   - 370 clients in the raw file; 369 have a non-zero reading in the window.
   - `MT_223` has no non-zero reading in the window and is dropped.
   - The other 369 are sorted by numeric id and 30 evenly spaced positions are taken (`np.linspace`, rounded). The result spans the range from about 5 kWh to about 17,000 kWh per hour on average.
5. **Not changed:** no value is filled, interpolated, removed or rescaled. The quirks below are flagged, not fixed.

## Quirks

Each row's `quirk` is one of four values. If an hour matches more than one rule, the first in this order applies: `before_first_reading`, `clock_change_gap`, `clock_change_repeat`.

| `quirk` | Rows | What it marks |
|---|---|---|
| `normal` | 501,329 | An ordinary hour. |
| `before_first_reading` | 24,156 | Hours before a client's first non-zero hour, which is zero. Late-starting clients only. |
| `clock_change_gap` | 57 | 01:00 on a March clock-change day. |
| `clock_change_repeat` | 58 | 01:00 on an October clock-change day. |

- **March (the hour that is mostly zero):** the dataset's note says the 01:00 to 02:00 values are zero for all clients on those days, but the file does not agree in every case. The clock-change days in the window are 2013-03-31 and 2014-03-30. Of the 57 flagged client-hours, 40 read zero and 17 do not. For the flagged client-hours with non-zero neighbours, the median ratio to the neighbouring hours is 0.000, and 55 of 57 are below 5% of their neighbours. Of the 17 that are not zero, 15 are below 5% of their neighbours and 2 are at or above it.
- **October (the doubled hour):** the note says the 01:00 to 02:00 values aggregate two hours. The clock-change days in the window are 2013-10-27 and 2014-10-26. The 01:00 hour is about 1.9 times its neighbours (median ratio 1.948 over 58 client-hours). This is one hour of time with about two hours of energy, so the day has 25 hours of energy. The hour is kept with its doubled value, and `clock_change_repeat` marks it. The timestamps do not repeat: the file has 24 labelled hours per day, one of them double.
- **Late starters:** 36 of the 369 eligible clients have their first non-zero hour inside the window. Three are in the cut:
  - `MT_039` from 2013-10-03 12:00,
  - `MT_179` from 2013-12-20 00:00,
  - `MT_115` from 2014-01-14 00:00.

  Their leading hours are zero in `y` and flagged `before_first_reading`. The data does not say why: the likeliest reading is that the meter was not yet recording, so the zeros are not demand. The book should treat them as missing, not as low use.
- **Zero readings elsewhere:** a client has a median of 9 zero readings (of 70,080) in the window. These are not flagged.
- **Check on the clock-change hours:** the 2011 and 2012 clock changes are not in the cut. Those years also have many clients with no readings yet, so the March check used 2013 and 2014 only.

## Holidays

The `holidays` package (MIT) covers Portugal: `holidays.country_holidays("PT", years=[2013, 2014])` returns 18 national holidays. Corpus Christi is revoked for 2013 to 2015 in its calendar, matching the national rule.

## Reproducing the file

With the pinned runtime in `examples/` (pandas 2.3.3, numpy 2.4.6) and the raw `LD2011_2014.txt` from the zip:

    python -I data-prep/prepare.py LD2011_2014.txt examples/data/electricity_hourly.csv.gz

The script refuses a raw file that is not `d51565f2...`. Its output bytes are the same from run to run in the pinned runtime. Another pandas version can flip one value at a rounding tie: pandas 3.1.1 gives one value differing by 0.001 in this cut (MT_256 on 2013-08-25 15:00). Regenerate only inside the pinned runtime.

## Limits

- Two years and 30 clients: enough for the book's case, not for a claim about all Portuguese electricity demand.
- Clients are anonymous and their sectors are unknown. Do not describe them as companies or households.
- The timestamps are local clock times without a time zone. The book's examples treat them as one naive hourly index.
