"""Facebook lead form answers -> CRM Lead fields.

The Facebook form asks the type of work in Tamil and the CRM sync copies that answer
into custom_type_of_work as-is (Meta sends the option key, with "_" for spaces, e.g.
"புதிய_கிணறு_வெட்டுதல்"). The Work Type dropdown (custom_work_type) only takes its English
options, so the answer is translated here on insert.
"""

WORK_TYPE_FIELD = "custom_work_type"
ANSWER_FIELD = "custom_type_of_work"

# Checked in order; the first rule with a keyword found in the answer wins. Keywords are
# word stems, so small wording changes to the form's options still match.
WORK_TYPE_KEYWORDS = [
	# கிணறு ஆழப்படுத்துதல் & தூர்வாருதல் (well deepening & desilting)
	("Well Deepening", ["ஆழப்படுத்து", "தூர்வாரு"]),
	# பண்ணை குட்டை வெட்டுதல் (farm pond digging)
	("Farm Pond", ["பண்ணை"]),
	# புதிய கிணறு வெட்டுதல் (new well digging)
	("New Well", ["புதிய"]),
]


def work_type_for_answer(answer: str | None, options: list[str]) -> str | None:
	"""English Work Type for a Facebook answer, or None when nothing matches.

	Returns None rather than a value missing from `options`, because a Select field
	rejects unknown values and the whole lead would then fail to sync.
	"""
	text = (answer or "").replace("_", " ")
	if not text.strip():
		return None
	for work_type, keywords in WORK_TYPE_KEYWORDS:
		if any(keyword in text for keyword in keywords):
			return work_type if work_type in options else None
	return None


def work_type_options() -> list[str]:
	import frappe

	field = frappe.get_meta("CRM Lead").get_field(WORK_TYPE_FIELD)
	return (field.options or "").split("\n") if field else []


def set_work_type_from_facebook(doc, method=None) -> None:
	"""CRM Lead before_insert: fill Work Type from the Facebook form's answer.

	Only Facebook leads are touched. An answer that matches no option leaves Work Type
	empty instead of the field default ("New Well"), so staff can see it needs setting.
	"""
	if doc.get("source") != "Facebook" or not doc.get(ANSWER_FIELD):
		return
	doc.set(WORK_TYPE_FIELD, work_type_for_answer(doc.get(ANSWER_FIELD), work_type_options()))
