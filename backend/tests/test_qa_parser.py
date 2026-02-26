import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models import Paragraph
from qa_parser import extract_cards, sanitize_tag


BIPOLAR_PARAGRAPHS = [
    Paragraph(text="TREATMENT OF BIPOLAR DISORDER", text_color="#800080"),
    Paragraph(text="What are the most effective anti-psychotics for acute mania?", is_bold=True),
    Paragraph(text="-  SGA: risperidone, quetiapine, olanzapine"),
    Paragraph(text="-  haloperidol"),
    Paragraph(text="Why are antipsychotics given in acute mania?", is_bold=True),
    Paragraph(text="-  used acutely as mood stabilisers take more time to work; can sedate patient + treat psychotic symptoms"),
    Paragraph(text="-  may stop once euthymic and continue with mood stabiliser only"),
    Paragraph(text="Treatment ladder for maintenance of bipolar disorder", is_bold=True),
    Paragraph(text="1. 1st line/most effective: lithium"),
    Paragraph(text="2. 2nd line: change to valproate OR augmenting SGA (aripiprazole, quetiapine, risperidone)"),
    Paragraph(text="3. 3rd line: change to carbamazepine OR change to another antipsychotic"),
    Paragraph(text="4. 4th line: antipsychotic + two mood stabilisers"),
    Paragraph(text="How long are mood stabilising drugs continued for mania?", is_bold=True),
    Paragraph(text="-  Used for 6-12 months to prevent relapse"),
    Paragraph(text="-  Can be used longer term (3-5 years or lifelong) if high risk relapse"),
    Paragraph(text="Outline the principles of treatment of bipolar depression", is_bold=True),
    Paragraph(text="1. Education + CBT"),
    Paragraph(text="2. Drugs – mood stabiliser + ADJUNCT antidepressants (NOT monotherapy as activates mania!!)"),
    Paragraph(text="3. Brain stimulation if severe – ECT, TMS"),
    Paragraph(text="What are the drugs of choice in preventing bipolar depression?", is_bold=True),
    Paragraph(text="1. Mood stabiliser – lamotrigine (lithium, valproate may also be used)"),
    Paragraph(text="2. SGA – quetiapine, lurasidone, olanzapine"),
    Paragraph(text="·  Use as monotherapy or combination therapy if ineffective"),
    Paragraph(text="·  SSRIs adjunct"),
    Paragraph(text="State the adverse effects of lithium (LITHIUM)", is_bold=True),
    Paragraph(text="1. Leukocytosis (raised WCC)"),
    Paragraph(text="2. Increased weight"),
    Paragraph(text="3. Tremor and teratogen"),
    Paragraph(text="4. Hypothyroid (thyrotoxicity) and hyperparathyroidism"),
    Paragraph(text="5. Insipidus (diabetes insipidus from renal toxicity + hypernatremia)"),
    Paragraph(text="6. Upset stomach (N/V/D)"),
    Paragraph(text="7. Metallic taste"),
    Paragraph(text="8. Skin effects (acne, psoriasis)"),
    Paragraph(text="Which patients to be careful with when prescribing lithium?", is_bold=True),
    Paragraph(text="-  Pregnant (teratogen) or breastfeeding"),
    Paragraph(text="-  Pre-existing renal dysfunction"),
    Paragraph(text="-  Thiazide diuretic use or ACEi – can increase lithium reabsorption + cause toxicity"),
    Paragraph(text="Define lithium toxicity and when it occurs", is_bold=True),
    Paragraph(text="-  Lithium toxicity = too much lithium in the body"),
    Paragraph(text="-  Can occur as lithium has very narrow therapeutic window"),
    Paragraph(text="-  E.g. following vomiting/diarrhoea/excessive sweating – can throw off plasma[lithium]"),
    Paragraph(text="Symptoms of lithium toxicity", is_bold=True),
    Paragraph(text="-  GIT upset – N/V/D"),
    Paragraph(text="-  Motor signs; tremor, ataxia"),
    Paragraph(text="-  AMS - lethargic -> AMS -> seizures -> coma -> death"),
    Paragraph(text="Treatment lithium toxicity?", is_bold=True),
    Paragraph(text="-  start with saline; dialysis if severe"),
]


PSYCHOTIC_DISORDERS_PARAGRAPHS = [
    Paragraph(text="PSYCHOTIC DISORDERS", text_color="#ff6600"),
    Paragraph(text="INTRO TO PSYCHOTIC DISORDERS", text_color="#800080"),
    Paragraph(text="Define psychotic disorders", is_bold=True),
    Paragraph(text="- pt loses touch with reality, but consciousness intact"),
    Paragraph(text="5 features of psychotic disorders?", is_bold=True),
    Paragraph(text="· Delusions"),
    Paragraph(text="· Hallucinations"),
    Paragraph(text="· disorganised speech"),
    Paragraph(text="· disorganised motor behaviour"),
    Paragraph(text="· negative Sx"),
    Paragraph(text="FIRST EPISODE PSYCHOSIS", text_color="#800080"),
    Paragraph(text="Define first episode psychosis", is_bold=True),
    Paragraph(text="- 1 week or more of sustained positive symptoms"),
    Paragraph(text="SCHIZOPHRENIA", text_color="#800080"),
    Paragraph(text="Define schizophrenia", is_bold=True),
    Paragraph(text="- Chronic disorder with psychosis + negative/cognitive symptoms"),
]


def test_extracts_correct_number_of_cards():
    cards = extract_cards(BIPOLAR_PARAGRAPHS)
    assert len(cards) == 11


def test_all_bipolar_cards_tagged():
    cards = extract_cards(BIPOLAR_PARAGRAPHS)
    for card in cards:
        assert "Treatment-Of-Bipolar-Disorder" in card.tags


def test_first_card_content():
    cards = extract_cards(BIPOLAR_PARAGRAPHS)
    first = cards[0]
    assert first.front == "What are the most effective anti-psychotics for acute mania?"
    assert "SGA: risperidone, quetiapine, olanzapine" in first.back
    assert "haloperidol" in first.back


def test_imperative_question():
    cards = extract_cards(BIPOLAR_PARAGRAPHS)
    fronts = [c.front for c in cards]
    assert "State the adverse effects of lithium (LITHIUM)" in fronts


def test_last_card_captured():
    cards = extract_cards(BIPOLAR_PARAGRAPHS)
    last = cards[-1]
    assert last.front == "Treatment lithium toxicity?"
    assert "saline" in last.back


def test_empty_document():
    cards = extract_cards([])
    assert cards == []


def test_heading_only():
    paragraphs = [
        Paragraph(text="Some Heading", is_heading=True),
    ]
    cards = extract_cards(paragraphs)
    assert cards == []


def test_consecutive_bold_lines():
    paragraphs = [
        Paragraph(text="Question one?", is_bold=True),
        Paragraph(text="Question two?", is_bold=True),
        Paragraph(text="Answer to question two"),
    ]
    cards = extract_cards(paragraphs)
    assert len(cards) == 2
    assert cards[0].front == "Question one?"
    assert cards[0].back == ""
    assert cards[1].front == "Question two?"
    assert cards[1].back == "Answer to question two"


def test_nested_tags_orange_and_purple():
    cards = extract_cards(PSYCHOTIC_DISORDERS_PARAGRAPHS)
    assert len(cards) == 4
    assert cards[0].tags == ["Psychotic-Disorders::Intro-To-Psychotic-Disorders"]
    assert cards[1].tags == ["Psychotic-Disorders::Intro-To-Psychotic-Disorders"]
    assert cards[2].tags == ["Psychotic-Disorders::First-Episode-Psychosis"]
    assert cards[3].tags == ["Psychotic-Disorders::Schizophrenia"]


def test_purple_only_no_parent():
    cards = extract_cards(BIPOLAR_PARAGRAPHS)
    assert cards[0].tags == ["Treatment-Of-Bipolar-Disorder"]


def test_orange_resets_purple():
    paragraphs = [
        Paragraph(text="TOPIC A", text_color="#ff6600"),
        Paragraph(text="SUBTOPIC A1", text_color="#800080"),
        Paragraph(text="Q1?", is_bold=True),
        Paragraph(text="A1"),
        Paragraph(text="TOPIC B", text_color="#ff6600"),
        Paragraph(text="Q2?", is_bold=True),
        Paragraph(text="A2"),
    ]
    cards = extract_cards(paragraphs)
    assert cards[0].tags == ["Topic-A::Subtopic-A1"]
    assert cards[1].tags == ["Topic-B"]


def test_multiple_purple_under_one_orange():
    paragraphs = [
        Paragraph(text="MAIN TOPIC", text_color="#ff6600"),
        Paragraph(text="SUB ONE", text_color="#800080"),
        Paragraph(text="Q1?", is_bold=True),
        Paragraph(text="A1"),
        Paragraph(text="SUB TWO", text_color="#800080"),
        Paragraph(text="Q2?", is_bold=True),
        Paragraph(text="A2"),
    ]
    cards = extract_cards(paragraphs)
    assert cards[0].tags == ["Main-Topic::Sub-One"]
    assert cards[1].tags == ["Main-Topic::Sub-Two"]


def test_heading_level_explicit():
    paragraphs = [
        Paragraph(text="Level 1", heading_level=1),
        Paragraph(text="Level 2", heading_level=2),
        Paragraph(text="Q?", is_bold=True),
        Paragraph(text="A"),
    ]
    cards = extract_cards(paragraphs)
    assert cards[0].tags == ["Level-1::Level-2"]


def test_colored_text_as_heading():
    paragraphs = [
        Paragraph(text="Purple Topic", text_color="#800080"),
        Paragraph(text="Q?", is_bold=True),
        Paragraph(text="A"),
    ]
    cards = extract_cards(paragraphs)
    assert cards[0].tags == ["Purple-Topic"]


def test_black_text_not_heading():
    paragraphs = [
        Paragraph(text="Not a heading", text_color="#000000"),
        Paragraph(text="Q?", is_bold=True),
        Paragraph(text="A"),
    ]
    cards = extract_cards(paragraphs)
    assert cards[0].tags == []


def test_sanitize_tag():
    assert sanitize_tag("TREATMENT OF BIPOLAR DISORDER") == "Treatment-Of-Bipolar-Disorder"
    assert sanitize_tag("  spaces  ") == "Spaces"
    assert sanitize_tag("") == ""


def test_table_in_answer():
    paragraphs = [
        Paragraph(text="Compare drugs A and B", is_bold=True),
        Paragraph(text="Some intro text"),
        Paragraph(
            text="Drug A | Fast\nDrug B | Slow",
            is_table=True,
            table_html="<table><tr><th>Drug</th><th>Speed</th></tr><tr><td>Drug A</td><td>Fast</td></tr><tr><td>Drug B</td><td>Slow</td></tr></table>",
        ),
        Paragraph(text="Next question?", is_bold=True),
        Paragraph(text="Next answer"),
    ]
    cards = extract_cards(paragraphs)
    assert len(cards) == 2
    assert "<table>" in cards[0].back
    assert "Drug A" in cards[0].back


def test_images_collected():
    paragraphs = [
        Paragraph(text="What does this show?", is_bold=True),
        Paragraph(text="It shows X", images=["aW1hZ2VkYXRh"]),
    ]
    cards = extract_cards(paragraphs)
    assert len(cards) == 1
    assert cards[0].images == ["aW1hZ2VkYXRh"]


def test_images_across_multiple_answer_lines():
    paragraphs = [
        Paragraph(text="Describe the diagram", is_bold=True),
        Paragraph(text="Part A", images=["img1"]),
        Paragraph(text="Part B", images=["img2"]),
    ]
    cards = extract_cards(paragraphs)
    assert cards[0].images == ["img1", "img2"]
