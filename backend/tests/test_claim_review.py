import json
import pytest
from organelle_scope.claim_review import review_claims
class Reviewer:
 def __init__(self,claims):self.claims=claims
 def completion(self,*args,**kwargs):return {'choices':[{'message':{'content':json.dumps({'claims':self.claims})},'finish_reason':'stop'}]}
def claim(kind='record_supported',index=0,quote='Pearson measures linear intensity correlation.',source='methods'):
 return {'index':index,'kind':kind,'quote':quote,'source_id':source}
PAYLOAD={'methods':'Pearson measures linear intensity correlation. This does not establish binding.'}
def test_record_links_include_verbatim_evidence_and_limitations():
 r=review_claims(Reviewer([claim()]),'Pearson measures linear intensity correlation. [methods]',PAYLOAD)
 assert r['claims'][0]['quote'] in PAYLOAD['methods'];assert 'not establish citation entailment' in r['limitations']
def test_invented_quote_does_not_enter_the_displayed_answer():
 r=review_claims(Reviewer([claim(quote='A fabricated validation result.')]),'The method is validated. [methods]',PAYLOAD)
 assert r['withheld_sentences']==1 and 'method is validated' not in r['checked_answer']
def test_binding_scope_guard_applies_even_if_reviewer_accepts():
 r=review_claims(Reviewer([claim()]),'This proves binding. [methods]',PAYLOAD)
 assert r['withheld_sentences']==1 and 'proves binding' not in r['checked_answer']
def test_uncertainty_is_withheld_instead_of_reported_as_supported():
 r=review_claims(Reviewer([claim(kind='unsupported')]),'An uncertain conclusion. [methods]',PAYLOAD)
 assert r['retained_sentences']==0 and not r['claims'][0]['retained']
def test_observation_cannot_be_relabelled_as_advice():
 r=review_claims(Reviewer([claim(kind='advice')]),'The sample has an activated pathway.',{})
 assert r['withheld_sentences']==1
def test_specimen_observation_cannot_hide_in_general_knowledge():
 r=review_claims(Reviewer([claim(kind='general_knowledge')]),'Your image shows increased localization.',{})
 assert r['withheld_sentences']==1
def test_ungrounded_factual_explanations_are_not_given_false_citations():
 r=review_claims(Reviewer([claim(kind='general_knowledge')]),'Your images cannot establish direct binding. [methods]',PAYLOAD)
 assert r['retained_sentences']==0 and '[methods]' not in r['checked_answer']
def test_omitted_sentence_and_duplicate_indices_are_withheld():
 with pytest.raises(ValueError,match='omitted'):review_claims(Reviewer([claim()]),'One claim. Another claim. [methods]',PAYLOAD)
 with pytest.raises(ValueError,match='sentence mapping'):review_claims(Reviewer([claim(),claim()]),'One claim. Another claim. [methods]',PAYLOAD)
def test_paragraph_citation_is_available_to_its_sentences():
 r=review_claims(Reviewer([claim(),claim(index=1,quote='This does not establish binding.')]),'Pearson measures linear intensity correlation. This does not establish binding. [methods]',PAYLOAD)
 assert len(r['claims'])==2
def test_supported_sentence_survives_unsupported_neighbour():
 r=review_claims(Reviewer([claim(),claim(index=1,kind='unsupported')]),'Pearson measures linear intensity correlation. The image proves binding. [methods]',PAYLOAD)
 assert r['retained_sentences']==1 and r['withheld_sentences']==1
 assert 'Pearson' in r['checked_answer'] and 'proves binding' not in r['checked_answer']


def test_manders_volume_misinterpretation_is_withheld_even_with_a_matching_quote():
 text='Manders quantifies the proportion of shared volume. [methods]'
 r=review_claims(Reviewer([claim(quote='Pearson measures linear intensity correlation.')]),text,PAYLOAD)
 assert r['withheld_sentences']==1 and 'shared volume' not in r['checked_answer']


def test_irrelevant_but_verbatim_boilerplate_cannot_support_binding_claim():
 payload={'interpretation':'General methodological advice is available; there are no current-image findings.'}
 reviewer=Reviewer([claim(source='interpretation',quote=payload['interpretation'])])
 r=review_claims(reviewer,'Database associations are not evidence of direct molecular interaction. [interpretation]',payload)
 assert r['withheld_sentences']==1 and 'direct molecular interaction' not in r['checked_answer']


def test_marker_specific_manders_claim_is_deferred_to_engine_even_with_valid_quote():
 payload={'measurements':{'pairs':[{'label_a':'Marker A','label_b':'Marker B','thresholded_m1':1.,'thresholded_m2':.1}]}}
 quote='"label_a": "Marker A", "label_b": "Marker B", "thresholded_m1": 1.0, "thresholded_m2": 0.1'
 r=review_claims(Reviewer([claim(source='measurements',quote=quote)]),'The Manders fraction indicates Marker B signal is largely contained within Marker A. [measurements]',payload)
 assert r['withheld_sentences']==1 and 'Marker B signal is largely contained' not in r['checked_answer']
 assert 'engine-defined' in r['claims'][0]['reason']


def test_direction_guard_normalizes_typographic_marker_separators():
 payload={'measurements':{'pairs':[{'label_a':'Marker-A','label_b':'Marker B','thresholded_m1':1.,'thresholded_m2':.1}]}}
 quote='"label_a": "Marker-A", "label_b": "Marker B", "thresholded_m1": 1.0, "thresholded_m2": 0.1'
 r=review_claims(Reviewer([claim(source='measurements',quote=quote)]),'The Manders fraction indicates Marker B signal is largely contained within Marker‑A. [measurements]',payload)
 assert r['withheld_sentences']==1
