import random

import pandas


def clean_duplicate_time(list_of_objects):
    new = []; t_taken = []
    for i in range(len(list_of_objects)):
        if list_of_objects[i].t not in t_taken:
            new.append( list_of_objects[i] )
            t_taken.append(list_of_objects[i].t)
    return new


class Contribution(object):

    def __init__(self, t, amount):
        self.t = t
        self.amount = amount

    def filter_interest_rates(self, interest_rates, t_target):
        interest_rates = clean_duplicate_time(interest_rates)
        interest_rates = sorted(interest_rates, key = lambda x: x.t)
        if interest_rates[0].t != 0:
            interest_rates[0].t = 0
        if t_target > self.t:
            while True:
                if len(interest_rates)>1:
                    if (interest_rates[0].t <= self.t < interest_rates[0+1].t):
                        interest_rates = [i for i in interest_rates if i.t < t_target]
                        break
                    else:
                        interest_rates.pop(0)
                else:
                    break
        elif t_target < self.t:
            while True:
                if len(interest_rates)>1:
                    if (interest_rates[0].t <= t_target < interest_rates[0+1].t):
                        interest_rates = [i for i in interest_rates if i.t < self.t]
                        break
                    else:
                        interest_rates.pop(0)
                else:
                    break
        else:
            return []
        return interest_rates

    def accumulate(self, t_end, interest_rates):
        if t_end >= self.t:
            result = self.amount
            interest_rates = self.filter_interest_rates(sorted(interest_rates, key = lambda x: x.t), t_end)
            if len(interest_rates)>0:
                t_start = self.t
                for i in range(len(interest_rates)-1):
                    delta = (interest_rates[i+1].t - t_start)
                    result = interest_rates[i].apply(result, delta)
                    t_start = interest_rates[i+1].t

                delta = t_end-t_start
                result = interest_rates[-1].apply(result, delta)
            return result
        else:
            return 0

    def value_at(self, t, interest_rates):
        if t > self.t:
            return self.accumulate(t, interest_rates)
        elif t == self.t:
            return self.amount
        else:
            result = self.amount
            interest_rates = self.filter_interest_rates(sorted(interest_rates, key = lambda x: x.t), t)
            interest_rates = sorted(interest_rates, key = lambda x: x.t, reverse = True)
            if len(interest_rates)>0:
                t_start = self.t
                for i in range(len(interest_rates)-1):
                    delta = (interest_rates[i].t - t_start)
                    result = interest_rates[i].apply(result, delta)
                    t_start = interest_rates[i].t
                delta = t-t_start
                result = interest_rates[-1].apply(result, delta)
            return result
            

class InterestRate(object):

    periods = {'annual':1, \
               'semi-annual':1/2, \
               'quarter':1/4, \
               'month':1/12}

    @staticmethod
    def get_period_length(period_desc):
        if period_desc in InterestRate.periods:
            return InterestRate.periods[period_desc]
        return period_desc
    
    def __init__(self, t, rate, period_desc, compound = True, discount = False):
        self.t = t
        self.rate = rate
        self.period_desc = period_desc
        self.compound = compound
        self.discount = discount
        self.period_length = self.get_period_length(period_desc)
        
    def apply(self, amount, delta):
        power = delta/self.period_length
        if self.discount:
            return amount*((1-self.rate)**(-power))
        if self.compound:
            return amount*((1+self.rate)**power)
        return amount*(1+(power*self.rate))


class FinancialTL(object):

    def __init__(self, contributions, interest_rates):
        self.contributions = contributions
        self.interest_rates = interest_rates
        self.adjustments()
        
    def adjustments(self):
        self.contributions = sorted(self.contributions, key = lambda x: x.t)
        self.interest_rates = clean_duplicate_time(self.interest_rates)
        self.interest_rates = sorted(self.interest_rates, key = lambda x: x.t)
        if self.interest_rates[0].t != 0:
            self.interest_rates[0].t = 0
        
    def acc_value_at_point(self, t):
        return sum([\
            c.accumulate(t, self.interest_rates)\
            for c in self.contributions])

    def acc_value_dynamics(self, t_end, dt):
        n = round((t_end)/dt)
        t = [(t_end)*i/n for i in range(n+1)]
        acc_values = [self.acc_value_at_point(i) for i in t]
        if t_end not in t:
            t.append(t_end)
            acc_values.append(self.acc_value_at_point(t_end))
        return t, acc_values

    def acc_value_dynamics_df(self, t_end, dt):
        t, acc_values = self.acc_value_dynamics(t_end, dt)
        df = pandas.DataFrame(data = [[i,j] for i,j in zip(t, acc_values)], \
                              columns = ["t", "accum. value (A(t))"])
        return df        

    def value_at(self, t):
        return sum([\
            c.value_at(t, self.interest_rates)\
            for c in self.contributions])


class Bond(object):

    periods = {'annual':1, \
               'semi-annual':1/2, \
               'quarter':1/4, \
               'month':1/12}

    @staticmethod
    def get_period_length(period_desc):
        if period_desc in Bond.periods:
            return Bond.periods[period_desc]
        return period_desc

    def __init__(self, t_start, term, face_value, nominal_coupon_rate, coupon_period, \
                 redemption_value, interest_rates):
        self.t_start = t_start
        self.term = term
        self.face_value = face_value
        self.nominal_coupon_rate = nominal_coupon_rate
        self.coupon_period = coupon_period
        self.coupon_period_length = self.get_period_length(coupon_period)
        self.coupon_rate = self.nominal_coupon_rate*self.coupon_period_length
        self.n_coupons = int(self.term/self.coupon_period_length)
        self.coupon_amount = self.face_value*self.coupon_rate
        self.redemption_value = redemption_value
        self.interest_rates = interest_rates
        self.adjustments()

    def adjustments(self):
        self.interest_rates = clean_duplicate_time(self.interest_rates)
        self.interest_rates = sorted(self.interest_rates, key = lambda x: x.t)
        if self.interest_rates[0].t != 0:
            self.interest_rates[0].t = 0

    @property
    def coupon_payments(self):
        payments = [Contribution(self.t_start+self.coupon_period_length*i, \
                                  self.coupon_amount) for i in range(1, self.n_coupons+1)]
        return payments

    @property
    def price(self):
        redemption = Contribution(self.t_start + self.term, self.redemption_value)
        timeline = FinancialTL(self.coupon_payments + [redemption], \
                               self.interest_rates)
        return timeline.value_at(self.t_start)  


class Installments(object):

    def __init__(self, interval, principle_amount, payments, interest_rates, do_adjustments = True):
        self.interval = interval
        self.t_start = interval[0]
        self.t_end = interval[1]
        self.principle = Contribution(self.t_start, principle_amount)
        self.payments = sorted(payments, key = lambda x: x.t)
        self.interest_rates = sorted(interest_rates, key = lambda x: x.t)
        if do_adjustments:
            self.adjustments()
        
    def adjustments(self):
        payments = []; t_taken = []
        for i in range(len(self.payments)):
            if self.payments[i].t not in t_taken:
                payments.append( self.payments[i] )
                t_taken.append(self.payments[i].t)
        self.payments = payments
        
        int_rates = []; t_taken = []
        for i in range(len(self.interest_rates)):
            if self.interest_rates[i].t not in t_taken:
                int_rates.append( self.interest_rates[i] )
                t_taken.append(self.interest_rates[i].t)
        self.interest_rates = int_rates
        if 0 not in t_taken:
            self.interest_rates[0].t = 0

    def minimum_required_single_payment(self, t_payment):
        if t_payment >= self.t_start:
            unit_contribution = Contribution(t_payment, 1)
            unit_present_value = unit_contribution.value_at(self.t_start, self.interest_rates)
            return self.principle.amount/unit_present_value
        else:
            return None

    def outstanding_balance_at_point(self, t):
         accum_payments = sum([p.accumulate(t, self.interest_rates)\
                               for p in self.payments])
         loan_amount = self.principle.accumulate(t, self.interest_rates)
         return loan_amount - accum_payments

    def outstanding_balance_at_end(self):
        return self.outstanding_balance_at_point(self.t_end)

    def outstanding_balance_dynamics(self, dt):
        n = round((self.t_end-self.t_start)/dt)
        t = [self.t_start + (self.t_end-self.t_start)*i/n for i in range(n+1)]
        balances = [self.outstanding_balance_at_point(i) for i in t]
        if self.t_end not in t:
            t.append(self.t_end)
            balances.append(self.outstanding_balance_at_end())
        return t, balances

    def outstanding_balance_df(self, dt):
        t, balances = self.outstanding_balance_dynamics(dt)
        df = pandas.DataFrame(data = [[i,j] for i,j in zip(t, balances)], \
                              columns = ["t", "Outstanding Balance"])
        return df
