"""
Bot de dominó em duplas — Omega Prime HPC-Signaling Edition
Estratégia PIMC (Perfect Information Monte Carlo) com Eliminação de Candidatas,
Pre-computing de bitboards, inferência de mãos ocultas por naipes ausentes,
sinalização de parceiro e suporte incremental para regras de pontuação exatas.
"""

import time as _t
import random as _rd
from ast import literal_eval as _lev
from math import comb as _comb
from itertools import combinations as _cmb

NOME_ESTUDANTE = "Órion Moreira e Pereira"

_pc = _t.perf_counter
_R = _rd.Random(20260610)

_TILES = [(a, b) for a in range(7) for b in range(a, 7)]
_IDX = {t: i for i, t in enumerate(_TILES)}
_A = [t[0] for t in _TILES]
_B = [t[1] for t in _TILES]
_PIP = [a + b for a, b in _TILES]
_DBB = [2.5 if a == b else 0.0 for a, b in _TILES]
_ISD = [a == b for a, b in _TILES]

_C = [0] * 7
for _i, (_a, _b) in enumerate(_TILES):
    _C[_a] |= 1 << _i
    _C[_b] |= 1 << _i

_OTH = [[-1] * 28 for _ in range(7)]
for _i, (_a, _b) in enumerate(_TILES):
    _OTH[_a][_i] = _b
    _OTH[_b][_i] = _a

_EM = [_C[l] | _C[r] for l in range(7) for r in range(7)]

_PL = [0] * 16384
_PH = [0] * 16384
for _m in range(1, 16384):
    _lsb = (_m & -_m).bit_length() - 1
    _PL[_m] = _PL[_m & (_m - 1)] + _PIP[_lsb]
    _PH[_m] = _PH[_m & (_m - 1)] + _PIP[_lsb + 14]

_FULL = (1 << 28) - 1

_BUDGET = 0.078
_EXTOT = 16
_NCAP = 1400 
_MAXW = 400   
_TARGET = 50 
_MY = 0                    
_VW = [[0.0] * 5, [0.0] * 5] 
_SECAV = [0.0, 0.0]      

class _Bud(Exception):
    pass

_CTX = {"n": 0, "st": [1, None, 0, 0, 0]}

def _apply_res(st, res):
    v = res.get("time_vencedor")
    p = res.get("pontos", 0)
    t = res.get("tipo", "")
    if v is None or p <= 0:
        if t != "seca":
            st[1] = None; st[2] = 0
        if t == "fechado_pelas_pontas_e_empate":
            st[0] = 2
        return
    if t == "seca":
        p = p * st[0]; st[0] = 1
        if st[1] is None:
            if st[3] == 3 and st[4] == 0:
                st[1] = 1; st[2] = 0
            elif st[3] == 0 and st[4] == 3:
                st[1] = 0; st[2] = 0
        if st[1] == v:
            st[2] += 1
            if st[2] == 3:
                p = 2; st[1] = None; st[2] = 0
        else:
            st[1] = None; st[2] = 0
    else:
        st[1] = None; st[2] = 0; st[0] = 1
    st[3 + v] += p


def _scan_fim(hist, i0, st):
    for k in range(i0, len(hist)):
        ev = hist[k]
        if ev.get("jogada") != "fim_da_rodada":
            continue
        det = ev.get("detalhes", "")
        head = det.split("; placar=")[0]
        if head.startswith("resultado="):
            try:
                _apply_res(st, _lev(head[10:]))
            except Exception:
                pass

def _contexto(estado):
    hist = estado["historico"]
    n = len(hist)
    pts = estado.get("pontuacoes", [0, 0])
    if _CTX["n"] > n:
        _CTX["n"] = 0; _CTX["st"] = [1, None, 0, 0, 0]
    st = _CTX["st"]
    _scan_fim(hist, _CTX["n"], st)
    _CTX["n"] = n
    if [st[3], st[4]] != list(pts): 
        st = [1, None, 0, 0, 0]
        _scan_fim(hist, 0, st)
        _CTX["st"] = st
        if [st[3], st[4]] != list(pts):   
            st = [1, None, 0, st[3], st[4]]
    sv = [st[0], st[0]]
    if st[1] is not None and st[2] == 2:
        sv[st[1]] = 2
    if max(pts) >= _TARGET:
        need = [99, 99]
    else:
        need = [max(1, _TARGET - pts[0]), max(1, _TARGET - pts[1])]
    return sv, need

def _reconstroi(estado, mao, seat):
    my = 0
    for t in mao:
        a, b = t
        my |= 1 << _IDX[(a, b) if a <= b else (b, a)]
    seen = 0
    for t in estado["mesa"]:
        a, b = t
        seen |= 1 << _IDX[(a, b) if a <= b else (b, a)]
    sizes = [7, 7, 7, 7]
    voids = [set(), set(), set(), set()]
    hist = estado["historico"]
    rod = estado["rodada"]
    for k in range(len(hist) - 1, -1, -1):
        ev = hist[k]
        if ev.get("rodada") != rod or ev.get("jogada") == "fim_da_rodada":
            break
        j = ev.get("jogador")
        ac = ev.get("jogada")
        if (ac == "joga" or ac == "comeco") and j is not None:
            sizes[j] -= 1
        elif ac == "passo" and j is not None:
            e = ev.get("mesa_esquerda"); d = ev.get("mesa_direita")
            if e is not None: voids[j].add(e)
            if d is not None: voids[j].add(d)
    sizes[seat] = len(mao)
    return my, sizes, voids, seen

def _amostra(unk, order, elig, o0, o1, o2):
    rnd = _R.random
    for _try in range(3):
        cap = [o0, o1, o2]; mk = [0, 0, 0]; ok = 1
        for k in order:
            el = elig[k]; tot = 0
            for o in el: tot += cap[o]
            if not tot: ok = 0; break
            x = rnd() * tot
            for o in el:
                c = cap[o]
                if x < c: break
                x -= c
            cap[o] -= 1; mk[o] |= 1 << unk[k]
        if ok: return mk
    cap = [o0, o1, o2]; mk = [0, 0, 0] 
    for k in unk:
        ch = [o for o in (0, 1, 2) if cap[o]] or [0, 1, 2]
        o = ch[int(rnd() * len(ch))]
        if cap[o]: cap[o] -= 1
        mk[o] |= 1 << k
    return mk

def _playout(hm, l, r, turn, lastp):
    ps = 0
    while 1:
        if ps >= 4:
            c = lastp & 1; t0 = _PL[hm[0] & 16383] + _PH[hm[0] >> 14] + _PL[hm[2] & 16383] + _PH[hm[2] >> 14]; t1 = _PL[hm[1] & 16383] + _PH[hm[1] >> 14] + _PL[hm[3] & 16383] + _PH[hm[3] >> 14]
            if t0 == t1: return _VW[1 - c][2]
            lo = 0 if t0 < t1 else 1; return _VW[lo][1] if lo == c else _VW[lo][2]
        m = hm[turn]; cl = _C[l]; cr = _C[r]; x = m & (cl | cr)
        if not x:
            ps += 1; turn = (turn + 1) & 3; continue
        om = hm[(turn + 1) & 3]; pm = hm[(turn + 2) & 3]; bs = -1e18; same = l == r
        while x:
            bb = x & -x; x ^= bb; i = bb.bit_length() - 1; af = m ^ bb
            if cl & bb:
                e = _EM[_OTH[l][i] * 7 + r]; sc = _PIP[i] - 2.3 * ((om & e).bit_count()) + 1.1 * ((pm & e).bit_count()) + 0.6 * ((af & e).bit_count()) + _DBB[i] + (7.0 if not (om & e) else 0.0) + (1e6 if not af else 0.0) - (60.0 if om.bit_count() == 1 and (om & e) else 0.0) + (28.0 if pm.bit_count() == 1 and (pm & e) else 0.0) - (3.0 if af and not (af & (af - 1)) and _ISD[af.bit_length() - 1] else 0.0)
                if sc > bs: bs = sc; bbit = bb; bi = i; bl = _OTH[l][i]; br = r
            if (cr & bb) and not same:
                e = _EM[l * 7 + _OTH[r][i]]; sc = _PIP[i] - 2.3 * ((om & e).bit_count()) + 1.1 * ((pm & e).bit_count()) + 0.6 * ((af & e).bit_count()) + _DBB[i] + (7.0 if not (om & e) else 0.0) + (1e6 if not af else 0.0) - (60.0 if om.bit_count() == 1 and (om & e) else 0.0) + (28.0 if pm.bit_count() == 1 and (pm & e) else 0.0) - (3.0 if af and not (af & (af - 1)) and _ISD[af.bit_length() - 1] else 0.0)
                if sc > bs: bs = sc; bbit = bb; bi = i; bl = l; br = _OTH[r][i]
        af = m ^ bbit
        if not af:
            w = turn & 1; pres = ((hm[0] | hm[1] | hm[2] | hm[3]) & (cl | cr)).bit_count() == 1; a = _A[bi]; b = _B[bi]
            if a == b: return _VW[w][4] if pres else _VW[w][2]
            if (a == l or b == l) and (a == r or b == r) and l != r: return _VW[w][3] if pres else _VW[w][2]
            return _SECAV[w]
        hm[turn] = af
        if not ((hm[0] | hm[1] | hm[2] | hm[3]) & _EM[bl * 7 + br]):
            t0 = _PL[hm[0] & 16383] + _PH[hm[0] >> 14] + _PL[hm[2] & 16383] + _PH[hm[2] >> 14]; t1 = _PL[hm[1] & 16383] + _PH[hm[1] >> 14] + _PL[hm[3] & 16383] + _PH[hm[3] >> 14]
            if t0 == t1: return 0.0
            lo = 0 if t0 < t1 else 1; return _VW[lo][1]
        l = bl; r = br; lastp = turn; ps = 0; turn = (turn + 1) & 3

def _solve(hm, l, r, turn, ps, lastp, alpha, beta, ctl):
    n = ctl[0] - 1; ctl[0] = n
    if n < 0: raise _Bud()
    if not (n & 31) and _pc() > ctl[1]: raise _Bud()
    if ps >= 4:
        c = lastp & 1; t0 = _PL[hm[0] & 16383] + _PH[hm[0] >> 14] + _PL[hm[2] & 16383] + _PH[hm[2] >> 14]; t1 = _PL[hm[1] & 16383] + _PH[hm[1] >> 14] + _PL[hm[3] & 16383] + _PH[hm[3] >> 14]
        if t0 == t1: return _VW[1 - c][2]
        lo = 0 if t0 < t1 else 1; return _VW[lo][1] if lo == c else _VW[lo][2]
    m = hm[turn]; cl = _C[l]; cr = _C[r]; x = m & (cl | cr)
    nxt = (turn + 1) & 3
    if not x:
        return _solve(hm, l, r, nxt, ps + 1, lastp, alpha, beta, ctl)
    om = hm[nxt]; pm = hm[(turn + 2) & 3]; same = l == r; mv = []
    while x:
        bb = x & -x; x ^= bb; i = bb.bit_length() - 1; af = m ^ bb
        if cl & bb:
            nl = _OTH[l][i]; e = _EM[nl * 7 + r]; sc = _PIP[i] - 2.3 * ((om & e).bit_count()) + (1e6 if not af else 0.0) + (7.0 if not (om & e) else 0.0) + _DBB[i]
            mv.append((sc, i, bb, nl, r, af))
        if (cr & bb) and not same:
            nr = _OTH[r][i]; e = _EM[l * 7 + nr]; sc = _PIP[i] - 2.3 * ((om & e).bit_count()) + (1e6 if not af else 0.0) + (7.0 if not (om & e) else 0.0) + _DBB[i]
            mv.append((sc, i, bb, l, nr, af))
    mv.sort(reverse=True)
    mx = (turn & 1) == _MY; w = turn & 1
    best = -1e9 if mx else 1e9
    for _sc, i, bb, nl, nr, af in mv:
        if not af:
            pres = ((hm[0] | hm[1] | hm[2] | hm[3]) & (cl | cr)).bit_count() == 1; a = _A[i]; b = _B[i]
            if a == b: v = _VW[w][4] if pres else _VW[w][2]
            elif (a == l or b == l) and (a == r or b == r) and l != r: v = _VW[w][3] if pres else _VW[w][2]
            else: v = _SECAV[w]
        else:
            hm[turn] = af
            if not ((hm[0] | hm[1] | hm[2] | hm[3]) & _EM[nl * 7 + nr]):
                t0 = _PL[hm[0] & 16383] + _PH[hm[0] >> 14] + _PL[hm[2] & 16383] + _PH[hm[2] >> 14]; t1 = _PL[hm[1] & 16383] + _PH[hm[1] >> 14] + _PL[hm[3] & 16383] + _PH[hm[3] >> 14]
                v = 0.0 if t0 == t1 else _VW[0 if t0 < t1 else 1][1]
            else:
                v = _solve(hm, nl, nr, nxt, 0, turn, alpha, beta, ctl)
            hm[turn] = m
        if mx:
            if v > best:
                best = v
                if best > alpha:
                    alpha = best
                    if alpha >= beta: break
        else:
            if v < best:
                best = v
                if best < beta:
                    beta = best
                    if alpha >= beta: break
    return best

def _heur(i, nl, nr, my_af, unk, vn, vp, v_opp2, partner_p, opp_p):
    e = _EM[nl * 7 + nr]
    sc = _PIP[i] * 1.0 + (8.0 if _ISD[i] else 0.0) + 0.8 * ((my_af & e).bit_count()) - 0.15 * ((unk & e).bit_count())
    sc += 40.0 * ((1 if nl in vn else 0) + (1 if nr in vn else 0))
    sc -= 25.0 * ((1 if nl in vp else 0) + (1 if nr in vp else 0))
    sc += 15.0 * ((1 if nl in v_opp2 else 0) + (1 if nr in v_opp2 else 0))
    sc += 6.0 * (partner_p[nl] + partner_p[nr])
    sc -= 4.0 * (opp_p[nl] + opp_p[nr])
    return sc

def _decide(estado, t0):
    global _MY, _VW, _SECAV
    mv = estado["movimentos_validos"]
    esq = mv["esquerda"]; dirr = mv["direita"]
    if not esq and not dirr:
        return {"jogada": "passa"}

    l = estado["esquerda_end"]; r = estado["direita_end"]
    mao = estado["mao"]; seat = estado["jogador"]; my = estado["time"]

    cand = []; uniq = set()
    for p in esq:
        i = _IDX[p]; nl = _OTH[l][i]
        k = (i, nl, r) if nl <= r else (i, r, nl)
        if k not in uniq:
            uniq.add(k); cand.append((p, "esquerda", i, nl, r))
    for p in dirr:
        i = _IDX[p]; nr = _OTH[r][i]
        k = (i, l, nr) if l <= nr else (i, nr, l)
        if k not in uniq:
            uniq.add(k); cand.append((p, "direita", i, l, nr))

    if len(cand) == 1 or len(mao) == 1:
        c = cand[0]
        return {"jogada": "joga", "peca": c[0], "lado": c[1]}

    sv, need = _contexto(estado)
    _MY = my
    for w in (0, 1):
        s = 1.0 if w == my else -1.0
        for p in range(1, 5):
            _VW[w][p] = s * (min(p, need[w]) + 0.02 * p)
    _SECAV[0] = _VW[0][sv[0]]; _SECAV[1] = _VW[1][sv[1]]

    my_mask, sizes, voids, seen = _reconstroi(estado, mao, seat)
    o1, o2, o3 = (seat + 1) & 3, (seat + 2) & 3, (seat + 3) & 3
    s1, s2, s3 = sizes[o1], sizes[o2], sizes[o3]
    unk_mask = _FULL & ~my_mask & ~seen
    unk = [i for i in range(28) if (unk_mask >> i) & 1]

    elig = []
    for i in unk:
        a = _A[i]; b = _B[i]; e = []
        if a not in voids[o1] and b not in voids[o1]: e.append(0)
        if a not in voids[o2] and b not in voids[o2]: e.append(1)
        if a not in voids[o3] and b not in voids[o3]: e.append(2)
        elig.append(e or [0, 1, 2])
    order = sorted(range(len(unk)), key=lambda k: len(elig[k]))

    partner_p = [0] * 7
    opp_p = [0] * 7
    hist = estado["historico"]
    rod = estado["rodada"]
    for ev in hist:
        if ev.get("rodada") == rod and ev.get("jogada") in ("joga", "comeco"):
            j = ev.get("jogador")
            if j is not None:
                p = ev.get("peca")
                if p is not None:
                    if j == o2:
                        partner_p[p[0]] += 1
                        partner_p[p[1]] += 1
                    elif j in (o1, o3):
                        opp_p[p[0]] += 1
                        opp_p[p[1]] += 1

    hs = []
    for c in cand:
        hs.append(_heur(c[2], c[3], c[4], my_mask & ~(1 << c[2]), unk_mask, voids[o1], voids[o2], voids[o3], partner_p, opp_p))
    idxs = sorted(range(len(cand)), key=lambda k: -hs[k])[:10]
    cand = [cand[k] for k in idxs]; hs = [hs[k] for k in idxs]
    nc = len(cand)

    total = len(mao) + s1 + s2 + s3
    use_exact = total <= _EXTOT
    ext_ok = total <= 18
    nfail = 0
    dl = t0 + _BUDGET

    worlds = None
    nu = len(unk)
    if use_exact and _comb(nu, s1) * _comb(nu - s1, s2) <= 250:
        e1 = [k for k in range(nu) if 0 in elig[k]]
        ws = []
        allk = frozenset(range(nu))
        for c1 in _cmb(e1, s1):
            r1 = allk.difference(c1)
            e2 = [k for k in r1 if 1 in elig[k]]
            if len(e2) < s2:
                continue
            for c2 in _cmb(e2, s2):
                r2 = r1.difference(c2)
                ok = 1
                for k in r2:
                    if 2 not in elig[k]: ok = 0; break
                if ok:
                    m0 = 0
                    for k in c1: m0 |= 1 << unk[k]
                    m1 = 0
                    for k in c2: m1 |= 1 << unk[k]
                    m2 = 0
                    for k in r2: m2 |= 1 << unk[k]
                    ws.append((m0, m1, m2))
        if ws:
            _R.shuffle(ws)
            worlds = ws
    wmax = len(worlds) if worlds is not None else _MAXW

    tot = [0.0] * nc
    alive = list(range(nc))  
    wn = 0
    while wn < wmax and len(alive) > 1 and _pc() < dl:
        mk = worlds[wn] if worlds is not None else _amostra(unk, order, elig, s1, s2, s3)
        base = [0, 0, 0, 0]
        base[seat] = my_mask; base[o1] = mk[0]; base[o2] = mk[1]; base[o3] = mk[2]
        tmp = [0.0] * nc; full = True
        ex_w = use_exact or (ext_ok and len(alive) <= 2)
        for ci in alive:
            c = cand[ci]; af = my_mask & ~(1 << c[2]); nl = c[3]; nr = c[4]
            hm = base[:]; hm[seat] = af
            if not ((hm[0] | hm[1] | hm[2] | hm[3]) & _EM[nl * 7 + nr]):
                t0_ = _PL[hm[0] & 16383] + _PH[hm[0] >> 14] + _PL[hm[2] & 16383] + _PH[hm[2] >> 14]; t1_ = _PL[hm[1] & 16383] + _PH[hm[1] >> 14] + _PL[hm[3] & 16383] + _PH[hm[3] >> 14]
                v = 0.0 if t0_ == t1_ else _VW[0 if t0_ < t1_ else 1][1]
            elif ex_w:
                ctl = [_NCAP, dl]
                try:
                    v = _solve(hm, nl, nr, o1, 0, seat, -1e9, 1e9, ctl)
                except _Bud:
                    if ctl[0] >= 0 and _pc() > dl: full = False; break
                    nfail += 1
                    if nfail >= 2: use_exact = False; ext_ok = False
                    hm = base[:]; hm[seat] = af
                    v = _playout(hm, nl, nr, o1, seat)
            else:
                v = _playout(hm, nl, nr, o1, seat)
            tmp[ci] = v
            if _pc() > dl: full = (ci == alive[-1]); break
        if not full:
            break
        for ci in alive:
            tot[ci] += tmp[ci]
        wn += 1
        if wn >= 6 and not (wn & 3):
       
            if worlds is None:
                cap = 5 if wn < 14 else (4 if wn < 22 else (3 if wn < 36 else 2))
                mg = 6.0 / (wn ** 0.5) * wn   
            else:
                cap = 8 if wn < 22 else (4 if wn < 40 else 3)
                mg = 9.0 / (wn ** 0.5) * wn
            bestv = max(tot[ci] for ci in alive)
            alive = [ci for ci in alive if bestv - tot[ci] <= mg]
            if len(alive) > cap:
                alive.sort(key=lambda ci: -tot[ci])
                alive = alive[:cap]

    if wn == 0:
        c = cand[0]
        return {"jogada": "joga", "peca": c[0], "lado": c[1]}

    best = alive[0]; bv = tot[best]
    for ci in alive[1:]:
        if tot[ci] > bv + 1e-9:
            best = ci; bv = tot[ci]
    c = cand[best]
    return {"jogada": "joga", "peca": c[0], "lado": c[1]}

def joga(estado):
    t0 = _pc()
    try:
        return _decide(estado, t0)
    except Exception:
        try:
            mv = estado["movimentos_validos"]
            for lado in ("esquerda", "direita"):
                lst = mv.get(lado)
                if lst:
                    return {"jogada": "joga", "peca": lst[0], "lado": lado}
        except Exception:
            pass
        return {"jogada": "passa"}