"""Reviewer packets must preserve answer identity without leaking automatic ratings."""
import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'backend'))
sys.path.insert(0,str(root/'scripts/validation'))
spec=importlib.util.spec_from_file_location('assistant_qualification',root/'scripts/validation/qualify_assistant.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class ReviewPacketTests(unittest.TestCase):
    def fixture(self):
        return {'suite_sha256':'frozen-protocol','model':{'name':'HIDDEN_MODEL_ID'},'frozen_cases':[
            {'id':'a','question':'First question?','record':{'image':None,'state':{}},'criteria':['Review evidence'],'reference':'https://example.org/reference'},
            {'id':'b','question':'Second question?','record':{'image':None,'state':{}},'criteria':['Review limits'],'reference':'https://example.org/reference'}],
            'cases':[{'id':'a','answer':'<script>alert(1)</script>','semantic_review':'HIDDEN_DEVELOPMENT_RATING','automatic_checks':{'rating':'HIDDEN_AUTO_RATING'},'audit':[]},
                     {'id':'b','answer':'Distinct second response.','audit':[]}]}

    def test_identity_and_ratings_withheld_and_answer_escaped(self):
        with tempfile.TemporaryDirectory() as directory:
            module.make_packet(self.fixture(),Path(directory));html=(Path(directory)/'REVIEW.html').read_text()
            for hidden in ('HIDDEN_MODEL_ID','HIDDEN_DEVELOPMENT_RATING','HIDDEN_AUTO_RATING','<script>'):self.assertNotIn(hidden,html)
            self.assertIn('&lt;script&gt;',html)
            self.assertIn('Application method definitions',html)

    def test_random_order_key_retains_exact_question_and_response_pair(self):
        with tempfile.TemporaryDirectory() as directory:
            report=self.fixture();module.make_packet(report,Path(directory));html=(Path(directory)/'REVIEW.html').read_text();key=json.loads((Path(directory)/'KEY.json').read_text())
            self.assertEqual({r['case_id'] for r in key['mapping']},{'a','b'})
            self.assertEqual(len({r['response_id'] for r in key['mapping']}),2)
            for row in key['mapping']:
                article=html.split('<h2>'+row['response_id']+'</h2>')[1].split('</article>')[0]
                expected='First question?' if row['case_id']=='a' else 'Second question?'
                self.assertIn(expected,article)
            self.assertEqual(key['status'],'independent human review pending')
