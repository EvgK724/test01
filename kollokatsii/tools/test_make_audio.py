"""Offline regression tests; ffmpeg and edge-tts must be installed.

Speech requests are replaced with local fixtures. Set FFMPEG_BINARY when the
decoder is not on PATH, then run python -m unittest discover -s kollokatsii/tools
-p test_make_audio.py. No production files or online services are changed.
"""
import asyncio
import importlib.util
import json
from pathlib import Path
import ssl
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch
SOURCE = Path(__file__).with_name('make_audio.py')
spec = importlib.util.spec_from_file_location('make_audio', SOURCE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
FF = m.decoder_path(None)

class Tests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'kollokatsii'
        self.root.mkdir()
        self.audio = self.root / 'audio'
        self.audio.mkdir()
        self.phrases = ['keep a promise', 'She always keeps her promises.']
        self.write_phrases()
        self.index = self.audio / 'index.json'
        self.index.write_text('{"voice":"en-GB-RyanNeural","files":[]}\n')
        self.original_index = self.index.read_bytes()
        self.fixture = Path(self.temp.name) / 'tone.mp3'
        subprocess.run([FF, '-v', 'error', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=0.5', '-codec:a', 'libmp3lame', str(self.fixture)], check=True)
        self.payload = self.fixture.read_bytes()
        self.calls = []
        self.sibling = Path(self.temp.name) / 'other-app'
        self.sibling.mkdir()
        (self.sibling / 'sentinel').write_bytes(b'preserve-me')

    def write_phrases(self):
        (self.root / 'phrases.json').write_text(json.dumps({'voice': m.VOICE, 'phrases': self.phrases}))

    def recording(self, text):
        return self.audio / (m.fnv(text) + '.mp3')

    async def fake(self, text, path, decoder):
        self.calls.append(text)
        path.write_bytes(self.payload)
        return True

    def run_audio(self, **kwargs):
        return asyncio.run(m.run(self.root, FF, **kwargs))

    def test_valid_and_invalid_mp3(self):
        self.assertTrue(m.valid_mp3(self.fixture, FF))
        corrupt = self.audio / 'bad.mp3'
        corrupt.write_bytes(b'<html>403</html>' * 30)
        self.assertFalse(m.valid_mp3(corrupt, FF))
        silent = self.audio / 'silent.mp3'
        subprocess.run([FF, '-v', 'error', '-f', 'lavfi', '-i', 'anullsrc=r=16000:cl=mono', '-t', '0.5', '-codec:a', 'libmp3lame', str(silent)], check=True)
        self.assertFalse(m.valid_mp3(silent, FF))

    def test_check_never_generates_or_changes_index(self):
        with patch.object(m, 'synth', AsyncMock(side_effect=AssertionError('network'))):
            self.assertEqual(self.run_audio(check=True), 1)
        self.assertEqual(self.index.read_bytes(), self.original_index)

    def test_complete_then_idempotent_preserves_existing_bytes(self):
        existing = self.recording(self.phrases[0])
        existing.write_bytes(self.payload)
        extra = self.audio / '01234567.mp3'
        extra.write_bytes(self.payload)
        with patch.object(m, 'synth', self.fake):
            self.assertEqual(self.run_audio(workers=1), 0)
        self.assertEqual(self.calls, [self.phrases[1]])
        self.assertEqual(existing.read_bytes(), self.payload)
        self.assertEqual(extra.read_bytes(), self.payload)
        self.assertEqual((self.sibling / 'sentinel').read_bytes(), b'preserve-me')
        timestamp = self.index.stat().st_mtime_ns
        with patch.object(m, 'synth', AsyncMock(side_effect=AssertionError('network'))):
            self.assertEqual(self.run_audio(), 0)
            self.assertEqual(self.run_audio(check=True), 0)
        self.assertEqual(self.index.stat().st_mtime_ns, timestamp)

    def test_failure_keeps_completed_mp3_and_old_index(self):

        async def failing(text, path, decoder):
            if text == self.phrases[0]:
                path.write_bytes(self.payload)
                return True
            return False
        with patch.object(m, 'synth', failing):
            self.assertEqual(self.run_audio(workers=1), 1)
        self.assertEqual(self.recording(self.phrases[0]).read_bytes(), self.payload)
        self.assertEqual(self.index.read_bytes(), self.original_index)
        with patch.object(m, 'synth', self.fake):
            self.assertEqual(self.run_audio(workers=1), 0)
        self.assertEqual(self.calls, [self.phrases[1]])

    def test_corrupt_existing_is_repaired(self):
        self.recording(self.phrases[0]).write_bytes(b'bad' * 100)
        with patch.object(m, 'synth', self.fake):
            self.assertEqual(self.run_audio(), 0)
        self.assertEqual(set(self.calls), set(self.phrases))
        self.assertEqual(self.run_audio(check=True), 0)

    def test_changed_phrase_adds_only_new_hash(self):
        with patch.object(m, 'synth', self.fake):
            self.assertEqual(self.run_audio(), 0)
        old = self.recording(self.phrases[1])
        self.calls.clear()
        self.phrases[1] = 'They always keep their promises.'
        self.write_phrases()
        with patch.object(m, 'synth', self.fake):
            self.assertEqual(self.run_audio(), 0)
        self.assertEqual(self.calls, [self.phrases[1]])
        self.assertEqual(old.read_bytes(), self.payload)

    def test_collision_is_rejected_before_any_audio(self):
        with patch.object(m, 'fnv', lambda text: 'same'):
            with self.assertRaisesRegex(ValueError, 'collision'):
                self.run_audio()
        self.assertEqual(self.index.read_bytes(), self.original_index)

    def test_deadline_keeps_index_and_no_new_recording(self):
        with patch.object(m, 'time', SimpleNamespace(monotonic=Mock(side_effect=[0, 10]))), patch.object(m, 'synth', AsyncMock(side_effect=AssertionError('network'))):
            self.assertEqual(self.run_audio(workers=1, time_limit=1), 1)
        self.assertEqual(self.index.read_bytes(), self.original_index)

    def test_synth_atomic_and_uses_ryan_original_rate(self):
        outer = self

        class Fake:

            def __init__(self, text, voice, rate):
                outer.assertEqual(voice, 'en-GB-RyanNeural')
                outer.assertEqual(rate, '-4%')

            async def save(self, path):
                Path(path).write_bytes(outer.payload)
        destination = self.recording(self.phrases[0])
        destination.write_bytes(b'old-recording')
        with patch.object(m.edge_tts, 'Communicate', Fake):
            self.assertTrue(asyncio.run(m.synth(self.phrases[0], destination, FF)))
        self.assertEqual(destination.read_bytes(), self.payload)
        self.assertEqual(list(self.audio.glob('.*')), [])

    def test_synth_network_retries_bounded_preserves_old(self):
        save = AsyncMock(side_effect=ConnectionError('temporary'))

        class Fake:

            def __init__(self, *args, **kwargs):
                self.save = save
        destination = self.recording(self.phrases[0])
        destination.write_bytes(b'old-recording')
        with patch.object(m.edge_tts, 'Communicate', Fake), patch.object(m.asyncio, 'sleep', AsyncMock()):
            self.assertFalse(asyncio.run(m.synth('x', destination, FF)))
        self.assertEqual(save.await_count, 3)
        self.assertEqual(destination.read_bytes(), b'old-recording')
        self.assertEqual(list(self.audio.glob('.*')), [])

    def test_access_and_tls_are_not_retried(self):

        class Denied(Exception):
            status = 403
        for failure in [Denied('denied'), ssl.SSLError('certificate')]:
            save = AsyncMock(side_effect=failure)

            class Fake:

                def __init__(self, *args, **kwargs):
                    self.save = save
            with patch.object(m.edge_tts, 'Communicate', Fake):
                with self.assertRaises(m.NonRetryableError):
                    asyncio.run(m.synth('x', self.recording('x'), FF))
            self.assertEqual(save.await_count, 1)
            self.assertEqual(list(self.audio.glob('.*')), [])
if __name__ == '__main__':
    unittest.main()
