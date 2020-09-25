### actuarial_tables

In current version, the available tables are only mortality tables. 
The tables are collected from: https://www.ons.gov.uk/ , https://mort.soa.org/.

## Usage example:

As shown in the code below, using the `'UK_ONS_2016_to_2018_male'` mortality table,  the `table['x']` is a list of ages.
An age in the list `table['x']` corresponds to a value in `table['qx']`, `table['px']`, `table['lx']` according to the position in the list.
The lists `table['x']`, `table['qx']`, `table['px']`, and `table['lx']` have the same size.

```
import actuarydesk.actuarial_tables as at

table = at.table_dictionary['UK_ONS_2016_to_2018_male']

print(table['x'])

q_20 = table['qx'][20]
p_20 = table['px'][20]
```
Currently there are only four tables available: `"UK_ONS_2016_to_2018_male"`, `"UK_ONS_2016_to_2018_female"`, `"US_Life_Tables_1959_to_1961_male_NB"`, `"US_Life_Tables_1959_to_1961_female_NB"`.
