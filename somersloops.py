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

def power2(Np, N, I):
    m = len(Np)
    n0 = N - sum(Np)
    c0 = (I - 2.5*(N-n0))/n0
    return n0 * c0**e + 2.5**e * sum(Np[i] * (1+(i+1)/m)**2 for i in range(m))

def relaxed(N, I, S, m):
    res = minimize(power2, [S,]+[0,]*(m-1), args=(N, I), bounds=Bounds(lb=0, ub=N), constraints=[{"type":"eq", "fun":lambda x : sum((i+1)*x[i] for i in range(len(x)))-S},{"type":"ineq", "fun":lambda x:min(N,I/2.5)-sum(x)}])
    assert res.success
    n0 = N - sum(res.x)
    c0 = 2.5 - (2.5*N-I)/n0
    return [c0,n0,]+list(res.x)

def brute(N, I, S, m):
    best = None
    match m:
        case 2:
            for n2 in range(min(N,S//2)+1):
                n1 = S - 2*n2
                if n1<0:
                    continue
                n0 = N - n2 - n1
                if n0<0 or (n0==0 and 2*I!=5*N):
                    continue
                if n0>0:
                    c0 = 2.5 - (2.5*N - I)/n0
                else:
                    c0 = 1.0
                if c0 < 0.01 or c0 > 2.5:
                    continue
                P = power2((n1,n2),N,I)
                if best is None or P < best[0]:
                    best = [P, c0, n0, n1, n2]
        case 4:
            for n4 in range(min(N,S//4)+1):
                S4 = S - 4*n4
                N4 = N - n4
                I4 = I - 2.5*n4
                for n3 in range(min(N4, S4//3, I4//2.5)+1):
                    S3 = S4 - 3*n3
                    N3 = N4 - n3
                    I3 = I4 - 2.5*n3
                    for n2 in range(min(N3, S3//2, I3//2.5)+1):
                        S2 = S3 - 2*n2
                        N2 = N3 - n2
                        I2 = I3 - 2.5*n2
                        n1 = S2
                        n0 = N2 - n1
                        if n0<0 or (n0==0 and I2!=2.5*n1):
                            continue
                        if n0>0:
                            c0 = 2.5 - (2.5*N - I)/n0
                        else:
                            c0 = 1.0
                        if c0 < 0.01 or c0 > 2.5:
                            continue
                        P = power2((n1,n2,n3,n4),N,I)
                        if best is None or P<best[0]:
                            best = [P,c0,n0,n1,n2,n3,n4]
    return best