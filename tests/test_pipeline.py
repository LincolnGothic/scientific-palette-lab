import io
import json
import tempfile
import unittest
import urllib.parse
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from palette_lab.app import Application
from palette_lab.colors import rgb_to_lab, extract_palette, palette_distance, accessibility, contrast, delta_e
from palette_lab.config import Study
from palette_lab.corpus import collect, excluded_record, main_figures, match_media, matches_journal, select_version, normalize_url
from palette_lab.figures import suggest_panels, validate_bbox
from palette_lab.recommend import recommend
from palette_lab.statistics import families
from palette_lab.store import Store


def palette(*values, role="unassigned"):
    return [{"hex": c, "role": role} for c in values]


class ColorsTests(unittest.TestCase):
    def test_lab_reference_and_contrast(self):
        np.testing.assert_allclose(rgb_to_lab([255,255,255]), [100,0,0], atol=.01)
        np.testing.assert_allclose(rgb_to_lab([255,0,0]), [53.24,80.09,67.2], atol=.03)
        self.assertAlmostEqual(contrast('#000000','#FFFFFF'),21.)

    def test_palette_matching_is_order_invariant_only_for_categories(self):
        a=palette('#FF0000','#0000FF','#00FF00')
        b=list(reversed(a))
        self.assertEqual(palette_distance(a,b),0)
        self.assertGreater(palette_distance(a,b,ordered=True),100)

    def test_roles_are_preserved(self):
        a=[{'hex':'#0072B2','role':'fill'},{'hex':'#111111','role':'text'}]
        b=[{'hex':'#0072B2','role':'text'},{'hex':'#111111','role':'fill'}]
        self.assertEqual(palette_distance(a,b),0)
        self.assertGreater(palette_distance(a,b,role_aware=True),50)

    def test_one_to_one_matching(self):
        a=palette('#FF0000','#FF0101')
        b=palette('#FF0000','#0000FF')
        self.assertGreater(palette_distance(a,b),100)
        self.assertEqual(palette_distance(a,a),0)

    def test_separation_simulations_are_finite(self):
        result=accessibility(['#0072B2','#E69F00','#009E73'])
        self.assertEqual(len(result['simulations']),3)
        self.assertTrue(np.isfinite(result['min_simulated_delta_e']))

    def test_raster_extraction_and_meaningful_neutral(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'chart.png'
            im=Image.new('RGB',(200,100),'white');draw=ImageDraw.Draw(im)
            for i,c in enumerate(['#0072B2','#E69F00','#009E73','#000000']):
                draw.rectangle((i*50,20,i*50+35,90),fill=c)
            im.save(path)
            chromatic=extract_palette(path)
            neutral=extract_palette(path,include_neutrals=True)
            self.assertEqual({c['hex'] for c in chromatic['colors']},{'#0072B2','#E69F00','#009E73'})
            self.assertIn('#000000',{c['hex'] for c in neutral['colors']})
            self.assertNotIn('#FFFFFF',{c['hex'] for c in neutral['colors']})
            cropped=extract_palette(path,[0,20,40,90])
            self.assertEqual(len(cropped['colors']),1)


class CorpusTests(unittest.TestCase):
    def test_official_s3_uris_are_normalized_without_widening_hosts(self):
        self.assertEqual(normalize_url('s3://pmc-oa-opendata/PMC1.1/figure.png?md5=abc'),
                         'https://pmc-oa-opendata.s3.amazonaws.com/PMC1.1/figure.png?md5=abc')
        self.assertEqual(normalize_url('s3://other-bucket/private.png'),'s3://other-bucket/private.png')

    def test_exact_journals(self):
        self.assertTrue(matches_journal({'journalInfo':{'journal':{'issn':'0028-0836'}}},'Nature'))
        self.assertFalse(matches_journal({'journalInfo':{'journal':{'issn':'2041-1723','title':'Nature Communications'}}},'Nature'))
        self.assertTrue(excluded_record({'pubTypeList':{'pubType':['Review','Journal Article']}}))

    def test_version_selection_is_not_blindly_largest(self):
        docs=[{'version':1,'is_pmc_openaccess':'yes','is_manuscript':'no','license_code':'CC BY'},
              {'version':2,'is_pmc_openaccess':'yes','is_manuscript':'yes','license_code':'CC BY'}]
        self.assertEqual(select_version(docs)['version'],1)
        with self.assertRaises(ValueError): select_version([{'is_pmc_openaccess':'no'}])
        self.assertEqual(select_version(docs,include_manuscripts=True)['version'],1)
        self.assertEqual(select_version([docs[1]],include_manuscripts=True)['version'],2)

    def test_main_figures_exclude_extended_data(self):
        xml=b'''<article xmlns:xlink="http://www.w3.org/1999/xlink"><body>
        <fig id="f1"><label>Fig. 1</label><caption><p>Chart <italic>caption</italic></p></caption><graphic xlink:href="a"/></fig>
        <fig><label>Extended Data Fig. 1</label><graphic xlink:href="b"/></fig>
        <supplementary-material><fig><graphic xlink:href="c"/></fig></supplementary-material>
        </body><back><fig><graphic xlink:href="d"/></fig></back></article>'''
        result=main_figures(xml)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]['caption'],'Chart caption')
        self.assertEqual(match_media(['a'],['https://pmc-oa-opendata.s3.amazonaws.com/PMC1.1/a.jpg?md5=x']),['https://pmc-oa-opendata.s3.amazonaws.com/PMC1.1/a.jpg?md5=x'])
    def test_main_figures_in_jats_floats_group(self):
        xml=b'<article xmlns:xlink="http://www.w3.org/1999/xlink"><body/><floats-group><fig id="f1"><label>Fig. 1</label><graphic xlink:href="a"/></fig></floats-group></article>'
        self.assertEqual(main_figures(xml)[0]['id'],'f1')

    def test_live_collector_contract_with_offline_fixture(self):
        class FakeRemote:
            def json(self,url):
                if '/search?' in url:
                    return {'hitCount':1,'resultList':{'result':[{'pmcid':'PMC123','firstPublicationDate':'2024-02-01','title':'Fixture paper','journalInfo':{'journal':{'issn':'0028-0836'}}}]},'nextCursorMark':'next'}
                return {'pmcid':'PMC123','version':1,'is_pmc_openaccess':'yes','is_manuscript':'no','license_code':'CC BY',
                        'xml_url':'https://pmc-oa-opendata.s3.amazonaws.com/article.xml','media_urls':['https://pmc-oa-opendata.s3.amazonaws.com/fig1.png']}
            def get(self,url):
                if '?list-type=' in url:
                    return b'<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><CommonPrefixes><Prefix>PMC123.1/</Prefix></CommonPrefixes></ListBucketResult>'
                if url.endswith('.xml'):
                    return b'<article article-type="research-article" xmlns:xlink="http://www.w3.org/1999/xlink"><front><journal-meta><issn>0028-0836</issn></journal-meta></front><body><fig id="f1"><label>Fig 1</label><graphic xlink:href="fig1"/></fig></body></article>'
                stream=io.BytesIO();Image.new('RGB',(50,50),'red').save(stream,'PNG');return stream.getvalue()
        with tempfile.TemporaryDirectory() as directory:
            store=Store(Path(directory))
            result=collect(store,Study(journals=('Nature',)),1,remote=FakeRemote())
            self.assertEqual(result['journals']['Nature']['new_figures'],1)
            self.assertEqual(result['errors'],[])
            self.assertEqual(store.overview()['pending'],1)
            again=collect(store,Study(journals=('Nature',)),1,remote=FakeRemote())
            self.assertEqual(again['journals']['Nature']['new_figures'],0)
            self.assertEqual(store.overview()['panels'],1)


class StoreAndAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.store=Store(self.root)
    def tearDown(self): self.temp.cleanup()
    def add_panel(self,paper_id,colors,kind='data',ptype='categorical',eligible='included',review=True,is_demo=False):
        self.store.put_paper({'id':paper_id,'journal':'Nature','year':2024,'title':'Fixture','is_demo':is_demo})
        index=len(self.store.panels("demo" if is_demo else "real"))
        image=self.root/'assets'/f'{paper_id}-{index}.png';im=Image.new('RGB',(100,100),'white');im.putpixel((0,0),(index,0,0));im.save(image)
        fid,_=self.store.put_figure(paper_id,image.name,'Figure','Caption',image,'',100,100)
        with self.store.connect() as db:
            row=db.execute('SELECT id FROM panels WHERE figure_id=?',(fid,)).fetchone()
        pid=row['id']
        if review:
            self.store.review(pid,{'kind':kind,'palette_type':ptype,'colors':colors,'revision':0,'eligibility':eligible,'confirmed_experimental':eligible=='included'})
        return pid
    def test_review_and_eligibility_gate(self):
        colors=palette('#0072B2','#E69F00','#009E73')
        self.add_panel('approved',colors)
        self.add_panel('unreviewed',colors,review=False)
        self.add_panel('excluded',colors,eligible='excluded')
        self.add_panel('pending',colors,eligible='pending')
        result=families(self.store,{'kind':'data'})
        self.assertEqual(result['analyzed_papers'],1)
        self.assertEqual(result['analyzed_panels'],1)
    def test_paper_votes_are_not_panel_votes(self):
        colors=palette('#0072B2','#E69F00','#009E73')
        self.add_panel('one',colors);self.add_panel('one',colors);self.add_panel('two',colors)
        f=families(self.store,{'kind':'data'})['families'][0]
        self.assertEqual(f['paper_count'],2);self.assertEqual(f['panel_count'],3);self.assertEqual(f['prevalence'],1.)
    def test_denominator_is_specific_to_color_count(self):
        self.add_panel('three',palette('#0072B2','#E69F00','#009E73'))
        self.add_panel('four',palette('#0072B2','#E69F00','#009E73','#CC79A7'))
        self.assertEqual([f['paper_denominator'] for f in families(self.store,{'kind':'data'})['families']],[1,1])
    def test_demo_and_flowcharts_never_mix(self):
        self.add_panel('real',palette('#0072B2','#E69F00','#009E73'))
        self.add_panel('demo',palette('#0072B2','#E69F00','#009E73'),is_demo=True)
        self.add_panel('flow',palette('#0072B2','#E69F00','#009E73',role='fill'),kind='flowchart',ptype='roles')
        self.assertEqual(families(self.store,{'kind':'data'})['analyzed_panels'],1)
        self.assertEqual(families(self.store,{'kind':'flowchart'})['analyzed_panels'],1)
        self.assertEqual(families(self.store,{'kind':'data','dataset':'demo'})['analyzed_panels'],1)
    def test_complete_link_avoids_color_chains(self):
        colors=['#0000C0','#0000D0','#0000E0']
        bound=max(delta_e(colors[0],colors[1]),delta_e(colors[1],colors[2]))+.001
        self.assertGreater(delta_e(colors[0],colors[2]),bound)
        for i,c in enumerate(colors): self.add_panel(str(i),palette(c))
        self.assertEqual(len(families(self.store,{'kind':'data'},bound)['families']),2)
    def test_review_rejects_stale_changes(self):
        pid=self.add_panel('one',palette('#0072B2'))
        with self.assertRaises(ValueError):self.store.review(pid,{'kind':'data','palette_type':'categorical','colors':palette('#E69F00'),'revision':0,'eligibility':'excluded'})
        self.assertEqual(self.store.panel(pid)['colors'][0]['hex'],'#0072B2')
    def test_reextraction_revokes_approval(self):
        pid=self.add_panel('one',palette('#0072B2'))
        self.store.set_extraction(pid,{'colors':palette('#E69F00')},[0,0,100,100])
        self.assertEqual(families(self.store,{'kind':'data'})['analyzed_panels'],0)
    def test_split_is_nonoverlapping_and_parent_bounded(self):
        pid=self.add_panel('one',palette('#0072B2'))
        with self.assertRaises(ValueError):self.store.split(pid,[[0,0,80,100],[50,0,100,100]])
        children=self.store.split(pid,[[0,0,50,100],[50,0,100,100]])
        with self.assertRaises(ValueError):self.store.split(children[0],[[0,0,100,100]])
        self.assertEqual(families(self.store,{'kind':'data'})['analyzed_panels'],0)
    def test_recommendations_distinguish_observed_and_reference(self):
        self.add_panel('one',palette('#0072B2','#E69F00','#009E73'))
        result=recommend(self.store,{'kind':'data','count':3})
        self.assertEqual({r['origin'] for r in result['recommendations']},{'observed','reference'})
        self.assertEqual(len(recommend(self.store,{'kind':'data','count':3,'include_references':False})['recommendations']),1)
        with self.assertRaises(ValueError):recommend(self.store,{'count':9})
    def test_locked_color_is_an_actual_constraint(self):
        result=recommend(self.store,{'kind':'data','count':3,'locked':'#123456'})
        self.assertEqual(result['recommendations'],[])
    def test_flowchart_roles_required(self):
        pid=self.add_panel('one',palette('#0072B2'),review=False)
        with self.assertRaises(ValueError):self.store.review(pid,{'kind':'flowchart','palette_type':'roles','colors':palette('#0072B2'),'revision':0})
    def test_bootstrap_is_deterministic(self):
        self.add_panel('one',palette('#0072B2'));self.add_panel('two',palette('#E69F00'))
        a=families(self.store,{'kind':'data'},bootstrap=100)
        b=families(self.store,{'kind':'data'},bootstrap=100)
        self.assertEqual(a,b)
    def test_import_image_api_and_duplicate_doi(self):
        import base64
        stream=io.BytesIO();Image.new('RGB',(30,30),'red').save(stream,'PNG')
        app=Application(self.store)
        request={'image':base64.b64encode(stream.getvalue()).decode(),'title':'Upload','journal':'Cell','year':2023,'doi':'10.1234/test'}
        first=app.post('/api/import',request);second=app.post('/api/import',request)
        self.assertTrue(first['new']);self.assertFalse(second['new']);self.assertEqual(self.store.overview()['papers'],1)
    def test_local_and_repository_imports_share_a_paper_vote(self):
        first=self.store.put_paper({'id':'PMC123','journal':'Cell','year':2023,'title':'Published','doi':'10.1234/test','pmcid':'PMC123','license':'CC BY','metadata':{'s3':{'xml_url':'s3://pmc-oa-opendata/a.xml','license_code':'CC BY'}}})
        second=self.store.put_paper({'id':'LOCAL-other','journal':'Cell','year':2023,'title':'Published','doi':'10.1234/TEST'})
        self.assertEqual(first,second)
        self.assertEqual(self.store.overview()['papers'],1)
        with self.assertRaises(ValueError):self.store.assert_source_snapshot('PMC123',{'xml_url':'s3://pmc-oa-opendata/changed.xml','license_code':'CC BY'})
    def test_accepted_manuscripts_are_explicitly_opt_in(self):
        self.add_panel('manuscript',palette('#0072B2','#E69F00','#009E73'))
        self.store.put_paper({'id':'manuscript','journal':'Nature','year':2024,'title':'Fixture','pmcid':'PMC12','metadata':{'s3':{'is_manuscript':True}}})
        self.assertEqual(families(self.store,{'kind':'data'})['analyzed_papers'],0)
        self.assertEqual(families(self.store,{'kind':'data','include_manuscripts':True})['analyzed_papers'],1)
        self.assertEqual(families(self.store,{'kind':'data','include_manuscripts':'false'})['analyzed_papers'],0)


if __name__=='__main__':unittest.main()
