import json
from organelle_scope.completeness import request_parts,review_completeness
class Model:
    def __init__(self,rows):self.rows=rows
    def completion(self,*args,**kwargs):return {'choices':[{'finish_reason':'stop','message':{'content':json.dumps({'coverage':self.rows})}}]}


def test_coverage_maps_each_question_and_requires_an_actual_answer_span():
    question='Why is it undefined? Does it prove protein absence?'
    answer='The reference mask is empty.'
    r=review_completeness(Model([{'index':0,'status':'addressed','answer_quote':answer},{'index':1,'status':'addressed','answer_quote':'A fabricated answer span.'}]),question,answer)
    assert r['assessed'] and not r['all_parts_addressed']
    assert r['parts'][1]['status']=='unanswered'


def test_missing_or_duplicate_review_entries_do_not_claim_completeness():
    r=review_completeness(Model([{'index':0,'status':'addressed','answer_quote':'A substantive answer.'}]),'First question? Second question?','A substantive answer.')
    assert not r['assessed'] and not r['all_parts_addressed']


def test_long_numbered_requests_are_explicitly_bounded():
    parts,truncated=request_parts('\n'.join(f'{i}. Explain topic {i}' for i in range(1,9)))
    assert len(parts)==6 and truncated


def test_reviewer_cannot_use_duplicate_indices_or_claim_empty_requests_complete():
    entries=[{'index':0,'status':'addressed','answer_quote':'A substantive answer.'}]*2
    assert not review_completeness(Model(entries),'Why? How?','A substantive answer.')['assessed']
    assert not review_completeness(Model([]),'','A substantive answer.')['all_parts_addressed']
