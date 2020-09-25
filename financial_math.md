### Usage Examples

```
import actuarydesk.financial_math as fm

int_rate = fm.InterestRate(0, 0.03, "annual")
contribution = fm.Contribution(3, 300)
contribution.accumulate(10, [int_rate])
```
