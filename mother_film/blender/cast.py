"""The cast: clay figures built from MakeHuman."""
import bpy
import mhlib as M, garments as G, clay as K

EYES_SHUT = {'eye-left-closure': 1.0, 'eye-right-closure': 1.0}


def baby(name='baby', shut=True, wet=0.3):
    t = {'macrodetails/caucasian-male-baby': 1.0}
    if shut:
        t.update(EYES_SHUT)
    h = M.Human(name, t)
    G.finish(h, subsurf=1)
    h.mat = K.clay(name + '_skin', 'terracotta', wet=wet)
    K.assign(h.body, h.mat)
    return h


def fetal(h, k=1.0, twist=42, head=1.0):
    for b in ('spine05', 'spine04', 'spine03', 'spine02', 'spine01'):
        h.rot(b, 'X', 10 * k)
    for b in ('neck01', 'neck02', 'neck03'):
        h.rot(b, 'X', 6 * k * head)
    h.rot('head', 'X', 10 * k * head)
    h.flex2('upperleg01', 112 * k); h.both('upperleg01', 'Y', -6 * k)
    h.flex2('lowerleg01', -128 * k)
    h.flex2('foot', 15 * k)
    h.both('upperarm01', 'Y', 30 * k)
    h.flex2('upperarm01', 30 * k)
    h.twist('upperarm01.L', twist * k); h.twist('upperarm01.R', -twist * k)
    h.flex2('lowerarm01', 100 * k)
    h.curl_fingers('L', 60 * k, 30 * k); h.curl_fingers('R', 60 * k, 30 * k)
