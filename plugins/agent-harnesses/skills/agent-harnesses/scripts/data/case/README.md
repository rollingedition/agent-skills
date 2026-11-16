# unitcraft

unitcraft parses, converts and formats physical quantities written as text, such as `3.5 kg` or `1,000 m`. It uses only the Python standard library and needs Python 3.12 or later.

```python
from unitcraft import convert, format_quantity, parse_quantity

q = convert(parse_quantity("3 ft"), "m")
print(format_quantity(q))  # 0.91 m
```

## Units

| Dimension | Symbols |
| --- | --- |
| length | `m`, `km`, `cm`, `mm`, `ft` |
| mass | `kg`, `g`, `lb` |
| time | `s`, `min`, `h` |
| temperature | `C`, `F`, `K` |

Temperatures convert affinely. Every other unit converts through its factor to the base unit of its dimension.

## Table layout

`format_table` writes one line per quantity. Rows sort by dimension name, then unit symbol, then value. Each value has two decimal places and thousands commas, and the values are right-aligned so the decimal points line up. The unit follows after one space.

For the quantities `12.5 m`, `1200 m`, `3 kg`, `-40 C`, `2 h` and `90 s`, the table is:

```text
   12.50 m
1,200.00 m
    3.00 kg
  -40.00 C
    2.00 h
   90.00 s
```

## Running the tests

```text
python -m pytest
```
