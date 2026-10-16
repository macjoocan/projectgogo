import math
import unittest

from tools.motion_remap.contacts import contact_weight,detect_contacts,smooth_bounded
from tools.motion_remap import core


class ContactsTests(unittest.TestCase):
    def test_stationary_and_swing_segments(self):
        times=[i*.1 for i in range(12)]
        points=[(0,0,0)]*4+[(.4,0,.4),(.8,0,.6),(1,0,.4)]+[(1,0,0)]*5
        result=detect_contacts(times,points,floor=0,height=.05,speed=.1,min_duration=.1,max_gap=0)
        self.assertEqual(result,[[0,2],[8,11]])

    def test_short_false_contact_rejected(self):
        result=detect_contacts([0,.01],[(0,0,0)]*2,floor=0,height=.1,speed=.1,min_duration=.1)
        self.assertEqual(result,[])

    def test_invalid_time_and_nan_rejected(self):
        for times,points in (([0,0],[(0,0,0)]*2),([0],[(0,math.nan,0)])):
            with self.assertRaises(ValueError):detect_contacts(times,points,floor=0,height=1,speed=1)

    def test_smooth_reduces_spike_and_preserves_boundaries(self):
        data=[0,0,2,0,0]
        result=smooth_bounded(data,4,.25)
        self.assertEqual(result[0],0);self.assertEqual(result[-1],0)
        self.assertLess(result[2],2)
        self.assertTrue(all(abs(a-b)<=.2500001 for a,b in zip(data,result)))

    def test_smooth_fixed_interior_and_zero_strength(self):
        self.assertEqual(smooth_bounded([1,2,3],0),[1,2,3])
        result=smooth_bounded([0,9,9,9,0],3,fixed={2:1})
        self.assertEqual(result[2],1)
        self.assertLess(result[1],9)

    def test_contact_blend_boundaries(self):
        self.assertEqual(contact_weight(0,1,10,2),0)
        self.assertEqual(contact_weight(1,1,10,2),0)
        self.assertEqual(contact_weight(3,1,10,2),1)
        self.assertEqual(contact_weight(9,1,10,2),.5)
        self.assertEqual(contact_weight(1,1,10,0),1)

    def test_invalid_postprocess_options_rejected(self):
        base=core.suggest_mapping(['root','upper','lower','end'],['root','upper','lower','end'])
        base.update(approved=True,root='root',ik_chains=[{'upper':'upper','lower':'lower','end':'end'}])
        import copy
        for config in ({'feet':[{'end':'missing'}]}, {'pelvis':{'max_shift':-1}},
                       {'feet':[{'end':'end','contact':{'mode':'manual','intervals':[[4,1]]}}]},
                       {'ground':{'max_tilt_degrees':999}}):
            p=copy.deepcopy(base);p['postprocess']=config
            with self.assertRaises(ValueError):core.validate(p,['root','upper','lower','end'],['root','upper','lower','end'])
