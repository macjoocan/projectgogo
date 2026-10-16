import unittest
from tools.motion_remap import core


class MotionRemapPresetTests(unittest.TestCase):
    def preset(self):
        p = core.suggest_mapping(['root', 'hand.L'], ['root', 'hand.L'])
        p.update(root='root', approved=True)
        return p

    def test_namespace_mapping_and_side_distinction(self):
        p = core.suggest_mapping(['mix:Hand.L', 'mix:Hand.R'], ['hand_l', 'hand_r'])
        self.assertEqual([x['target'] for x in p['bones']], ['hand_l', 'hand_r'])
        self.assertFalse(p['approved'])

    def test_ambiguous_aliases_are_never_silently_mapped(self):
        p = core.suggest_mapping(['n:Hand.L'], ['hand_l', 'hand.l'])
        self.assertEqual(p['bones'], [])
        self.assertEqual(len(p['unresolved'][0]['candidates']), 2)
        p = core.suggest_mapping(['a:root', 'b:root'], ['root'])
        self.assertEqual(p['bones'], [])

    def test_unreviewed_mapping_rejected(self):
        p = self.preset(); p['approved'] = False
        with self.assertRaisesRegex(ValueError, 'Review'): core.validate(p, ['root', 'hand.L'], ['root', 'hand.L'])

    def test_duplicate_and_unknown_bones_rejected(self):
        for update in ({'source': 'absent'}, {'source': 'root'}, {'target': 'root'}):
            p = self.preset(); p['bones'][1].update(update)
            with self.assertRaises(ValueError): core.validate(p, ['root', 'hand.L'], ['root', 'hand.L'])

    def test_invalid_math_and_policy_rejected(self):
        for field, value in (('scale_ratio', -1), ('scale_ratio', float('inf')),
                             ('scale_ratio', True), ('alignment_wxyz', [0, 0, 0, 0]),
                             ('in_place_axes', ['W']), ('root', 'missing')):
            p = self.preset(); p[field] = value
            with self.assertRaises(ValueError): core.validate(p, ['root', 'hand.L'], ['root', 'hand.L'])

    def test_valid_preset_and_translation_offsets(self):
        p = self.preset(); p['bones'][1].update(translation=True, location_multiplier=.5,
                                               rotation_offset_wxyz=[1, 0, 0, 0])
        self.assertIs(core.validate(p, ['root', 'hand.L'], ['root', 'hand.L']), p)

    def test_ik_overlapping_or_unknown_chain_rejected(self):
        p = self.preset(); p['ik_chains'] = [{'upper': 'root', 'lower': 'hand.L', 'end': 'absent'}]
        with self.assertRaises(ValueError): core.validate(p, ['root', 'hand.L'], ['root', 'hand.L'])

    def test_nan_offsets_rejected(self):
        p = self.preset(); p['bones'][1]['location_offset'] = [0, float('nan'), 0]
        with self.assertRaises(ValueError): core.validate(p, ['root', 'hand.L'], ['root', 'hand.L'])
