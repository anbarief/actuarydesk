### actuarial_tables

## Usage example:

The code below gets the value of $q_{20}$

```
import actuarydesk.actuarial_tables as at

table = at.table_dictionary['UK_ONS_2016_to_2018_male']

print(table['x'])

q_20 = table['qx'][20]
p_20 = table['px'][20]
```


`"UK_ONS_2016_to_2018_male"`, `"UK_ONS_2016_to_2018_female"`, `"US_Life_Tables_1959_to_1961_male_NB"`, `"US_Life_Tables_1959_to_1961_female_NB"`.
