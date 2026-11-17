"""Facebook answer -> Work Type mapping (hitech.facebook_leads), using the answers the live form sends."""

import unittest

from hitech.facebook_leads import work_type_for_answer

OPTIONS = ["New Well", "Well Deepening", "Wall Construction", "Desilting", "Water Survey", "Farm Pond"]


class TestWorkTypeForAnswer(unittest.TestCase):
	def test_live_form_answers(self):
		cases = {
			"புதிய_கிணறு_வெட்டுதல்": "New Well",
			"கிணறு_ஆழப்படுத்துதல்_&_தூர்வாருதல்": "Well Deepening",
			"பண்ணை_குட்டை_வெட்டுதல்": "Farm Pond",
		}
		for answer, expected in cases.items():
			with self.subTest(answer=answer):
				self.assertEqual(work_type_for_answer(answer, OPTIONS), expected)

	def test_spaces_instead_of_underscores(self):
		self.assertEqual(work_type_for_answer("புதிய கிணறு வெட்டுதல்", OPTIONS), "New Well")

	def test_desilting_only_answer_is_deepening(self):
		self.assertEqual(work_type_for_answer("கிணறு_தூர்வாருதல்", OPTIONS), "Well Deepening")

	def test_unknown_or_empty_answer(self):
		for answer in ["போர்வெல்", "", "   ", None]:
			with self.subTest(answer=answer):
				self.assertIsNone(work_type_for_answer(answer, OPTIONS))

	def test_value_missing_from_options_is_not_returned(self):
		# A Select rejects unknown values, which would fail the whole lead.
		without_farm_pond = [o for o in OPTIONS if o != "Farm Pond"]
		self.assertIsNone(work_type_for_answer("பண்ணை_குட்டை_வெட்டுதல்", without_farm_pond))


if __name__ == "__main__":
	unittest.main()
