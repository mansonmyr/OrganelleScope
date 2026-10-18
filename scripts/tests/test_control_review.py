"""An owner-approved candidate must not silently move on regeneration."""
import importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('control_review',Path(__file__).resolve().parents[1]/'validation/control_review.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class ReviewTests(unittest.TestCase):
    def test_review_invalidated_by_changed_candidate_position(self):
        centers={'1':[0,20,30]};review={'candidate_centers_zyx':centers,'accepted_candidates':[1],'rejected_candidates':[]}
        self.assertEqual(module.validated_review(review,centers),review)
        self.assertIsNone(module.validated_review(review,{'1':[1,20,30]}))
        self.assertIsNone(module.validated_review(review,{'1':[0,20,31]}))
        self.assertIsNone(module.validated_review(None,centers))

    def test_contradictory_or_unknown_candidates_are_not_accepted(self):
        centers={'1':[0,20,30]}
        for accepted,rejected in [([1],[1]),([2],[])]:
            with self.assertRaises(ValueError):module.validated_review({'candidate_centers_zyx':centers,'accepted_candidates':accepted,'rejected_candidates':rejected},centers)
