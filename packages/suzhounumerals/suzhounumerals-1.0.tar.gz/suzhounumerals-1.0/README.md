# suzhounumerals
 [Suzhou numerals](https://en.wikipedia.org/wiki/Suzhou_numerals) (蘇州碼子) converter module for Python 3.7+.

## Usage

### Functions
 * `suzhou(x, /)`: Returns the suzhou numeral string of a number `x`.
 * `suzhou_to_type(s, /, type_=int)`: Returns the numeric value in `type` of the suzhou numeral string `s`.
 * `suzhou_to_int(s, /)`: Returns the numeric value in `int` of the suzhou numeral string `s`.
 * `suzhou_to_decimal_str(s, /)`: Returns the numeric value string of the suzhou numeral string `s`.
 * `suzhou_digit(i, /, alt=False)`: Returns the suzhou digit of a integer `i`.
 * `suzhou_digit_value(c, /, alt=False)`: Returns the numeric value of a suzhou digit character `c`, where `alt` specifies whether to use alternate digits or not (for digits 1 to 3).
 
### Constants
 * `ZERO` to `NINE`: Suzhou digits for 0 to 9 respectively.
 * `ONE_ALT`, `TWO_ALT`, `THREE_ALT`: Alternate Suzhou digits for 1 to 3 respectively, due to the digits one, two, and three are all represented by vertical bars, causing confusion when they appear next to each other.
 * `TEN`, `TWENTY`, `THIRTY`: Suzhou digits for 10, 20 and 30 respectively.
 
## Example
 ```python
 >>> from decimal import Decimal
 >>> from suzhou import *
 >>> i = suzhou(5201314)
 >>> print(i)
 〥〢〇〡三〡〤
 >>> f = suzhou(round(Decimal(11053406) / 96524333, 13))
 >>> print(f)
 〇．〡一〤〥〡〤〡〩〡〩〨〡〇
 >>> suzhou_to_int(i)
 >>> 5201314
 >>> _ + suzhou_to_type(f, Decimal)
 Decimal('5201314.1145141919810')
 ```
 
## Download & Installation
 
 The module requires Python 3.7 or up.
 
 The module is available on PyPI (https://pypi.org/project/suzhounumerals). To install the latest release with pip, simply run
 ```
 pip install suzhounumerals
 ```
 
 or from the source tree
 ```
 pip install .
 ```