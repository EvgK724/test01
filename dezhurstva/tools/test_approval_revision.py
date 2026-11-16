import contextlib
import copy
import io
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch
import approval_revision
import publish
import build

BASE = pathlib.Path(__file__).resolve().parent.parent


class RevisionTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((BASE/'data/schedule.json').read_text())
        self.month = self.data['months']['2026-12']


    def test_ics_folding_keeps_spaces_roundtrip_and_byte_limit(self):
        samples = [
            "SUMMARY:Дежурства ПСО: согласование графика на декабрь 2026",
            "DESCRIPTION:График остаётся предварительным. Если вы ещё не отвечали, откройте приложение.",
            "SUMMARY:" + "a" * 66 + " " + "кириллица" * 20,
            "DESCRIPTION:" + "a" * 62 + "  " + "test" * 40,
        ]
        for source in samples:
            result = build.fold(source)
            self.assertEqual(result.replace("\r\n ", ""), source)
            for part in result.split("\r\n"):
                self.assertLessEqual(len(part.encode("utf-8")), 75)
                self.assertEqual(part, part.rstrip(" \t"))
        with self.assertRaises(ValueError):
            build.fold("SUMMARY:" + " " * 100 + "x")

    def test_all_calendars_preserve_logical_content_without_trailing_whitespace(self):
        self.month['confirm'].update(agreedCount=3, confirmed=[])
        items = list(build.shifts(self.data))
        for who in [*self.data['doctors'], None]:
            selected = [x for x in items if who is None or x[1] == who]
            args = (self.data, 'Synthetic calendar', selected, who is not None, '#3BE8FF', who)
            with patch.object(build, 'fold', side_effect=lambda line: line):
                logical = build.ics(*args)
            physical = build.ics(*args)
            self.assertEqual(physical.replace("\r\n ", ""), logical)
            for line in physical.split("\r\n"):
                self.assertLessEqual(len(line.encode()), 75)
                self.assertEqual(line, line.rstrip(" \t"))

    def test_mutable_state_does_not_change_digest(self):
        old = approval_revision.revision(self.month,self.data)
        self.month.update(status='final',final_at='2026-12-01T00:00:00Z',finalization={'anything':True})
        self.month['confirm'].update(confirmed=[],disagreed=7,digest='irrelevant',receiptIds=['receipt'])
        self.assertEqual(old,approval_revision.revision(self.month,self.data))

    def test_content_roster_timezone_and_doctor_changes_invalidate(self):
        original = approval_revision.revision(self.month,self.data)
        for mutate in [lambda d,m:m['duty'].update({'2026-12-01':['omutov']}),
                         lambda d,m:d.update(tz='UTC'),
                         lambda d,m:d['doctors']['klepikov'].update(name='Synthetic replacement'),
                         lambda d,m:m['confirm'].update(need=m['confirm']['need'][:-1]),
                         lambda d,m:m.update(version=m['version']+1)]:
            d=copy.deepcopy(self.data);m=d['months']['2026-12'];mutate(d,m)
            self.assertNotEqual(original,approval_revision.revision(m,d))

    def publication(self, final=False):
        with tempfile.TemporaryDirectory() as td:
            root=pathlib.Path(td);(root/'data').mkdir();(root/'private').mkdir()
            (root/'data/schedule.json').write_text(json.dumps(self.data))
            (root/'data/config.json').write_text(json.dumps({'organizer':'klepikov'}))
            draft=copy.deepcopy(self.month)
            for k in ['version','confirm','final_at','finalization','status']:draft.pop(k,None)
            (root/'private/2026-12-draft.json').write_text(json.dumps(draft))
            argv=['publish.py','2026-12']+(['--final'] if final else [])
            with patch.object(publish,'ROOT',root),patch.object(publish.build,'main'),patch.object(sys,'argv',argv),contextlib.redirect_stdout(io.StringIO()):publish.main()
            return json.loads((root/'data/schedule.json').read_text())['months']['2026-12']

    def test_final_to_preliminary_is_new_version_and_clears_final_metadata(self):
        self.month.update(status='final',version=3,final_at='old',finalization={'old':True})
        self.month['confirm']['version']=3
        result=self.publication()
        self.assertEqual(result['version'],4);self.assertEqual(result['status'],'preliminary')
        self.assertNotIn('final_at',result);self.assertNotIn('finalization',result)
        self.assertEqual(result['confirm']['confirmed'],['klepikov'])
        self.assertEqual(len(result['confirm']['digest']),64)

    def test_direct_final_keeps_monotonic_version(self):
        self.month['version']=5;self.month['confirm']['version']=5
        result=self.publication(final=True)
        self.assertEqual(result['version'],6);self.assertNotIn('confirm',result)

    def test_initial_publication_starts_at_one(self):
        self.data['months'].pop('2026-12')
        self.assertEqual(self.publication()['version'],1)

    def test_count_only_calendar_reminder_is_generic_for_every_doctor(self):
        self.month['confirm'].update(agreedCount=1, confirmed=[])
        normalized=[]
        for who in self.month['confirm']['need']:
            text='\n'.join(build.ack_events(self.data,who,self.data['tz'],'20261116T120000Z'))
            self.assertIn('Если вы ещё не отвечали',text)
            self.assertIn('повторять его из-за этого общего напоминания не нужно',text)
            self.assertNotIn('подтвердите график',text.lower())
            normalized.append(text.replace(who,'doctor'))
        self.assertEqual(len(set(normalized)),1)

    def test_count_only_final_has_no_ack_reminders(self):
        self.month['status']='final';self.month['confirm'].update(agreedCount=7,confirmed=[])
        self.assertEqual(build.ack_events(self.data,'klepikov',self.data['tz'],'20261116T120000Z'),[])


if __name__=='__main__':unittest.main()
