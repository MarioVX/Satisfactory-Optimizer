# -*- coding: utf-8 -*-
"""
Created on Sun Sep 15 17:29:40 2024

@author: pc
"""

from scipy.optimize import fsolve
from math import log

e = log(2.5, 2)
f = log(2, 1.25)

def clocks_M2(N0, N1, N2, I, O):
    res = fsolve(lambda x:[N0 * ((x[0]+x[1])/e)**f + N1 * ((x[0]+1.5*x[1])/2.25/e)**f + N2 * ((x[0]+2*x[1])/4/e)**f - I, 
                              N0 * ((x[0]+x[1])/e)**f + 1.5 * N1 * ((x[0]+1.5*x[1])/2.25/e)**f + 2 * N2 * ((x[0]+2*x[1])/4/e)**f - O], [1,1], full_output=True)
    if res[2] != 1:
        return None
    lI, lO = res[0]
    c0 = ((lI+lO)/e)**f
    c1 = ((lI+1.5*lO)/2.25/e)**f
    c2 = ((lI+2*lO)/4/e)**f
    return 1*N0*c0**e + 2.25*N1*c1**e + 4*N2*c2**e, c0, c1, c2

from scipy.optimize import minimize, Bounds

def clocks2(N, I, O):
    m = len(N)-1
    res = minimize(lambda x : sum(N[i] * x[i]**e * (1+i/m)**2 for i in range(m+1)), [1,]*(m+1), bounds=Bounds(0.01,2.5), constraints=[{"type":"eq","fun":lambda x : sum(N[i]*x[i] for i in range(m+1))-I}, {"type":"eq","fun":lambda x : sum(N[i]*x[i]*(1+i/m) for i in range(m+1))-O}])
    #print(res.message)
    if res.success:
        return res.fun, *(res.x)
    else:
        return 10**100, 1.0, 1.0, 1.0

def bruteforce_M2(I, O, maxS, maxN):
    assert O >= I
    assert maxS >= 0
    assert maxN >= 0
    best = None
    n_total = maxN
    for n0 in range(n_total+1):
        for n2 in range(n_total+1-n0):
            n1 = n_total - n0 - n2
            S = n1 + 2 * n2
            if S > maxS:
                continue
            # res = clocks_M2(n0, n1, n2, I, O)
            # if res is None:
            #     continue
            P, c0, c1, c2 = clocks2([n0,n1,n2],I,O)
            if best is None or P < best[0]:
                best = [P, n0, n1, n2, c0, c1, c2]
    return best

def power(N, C):
    m = len(N) - 1
    return sum(N[i] * (1+i/m)**2 * C[i]**e for i in range(m+1))