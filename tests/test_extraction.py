import json
import os
import unittest
from unittest.mock import patch
from app.adapters.extraction import extract
class ExtractionTests(unittest.TestCase):
    def test_disabled_is_explicit(self):
        with patch.dict(os.environ,{'AI_MODE':'template'}),self.assertRaises(ValueError):extract({'type':'invoice','text':'Factura F001'})
    def test_extracts_draft_with_evidence(self):
        raw=json.dumps({'message':{'content':json.dumps({'id':'F001','evidence':'Factura F001'})}}).encode()
        with patch.dict(os.environ,{'AI_MODE':'ollama'}),patch('urllib.request.urlopen') as call:
            call.return_value.__enter__.return_value.read.return_value=raw
            self.assertTrue(extract({'type':'invoice','text':'Factura F001'})['review_required'])
    def test_rejects_invented_evidence(self):
        raw=json.dumps({'message':{'content':json.dumps({'id':'F001','evidence':'inventada'})}}).encode()
        with patch.dict(os.environ,{'AI_MODE':'ollama'}),patch('urllib.request.urlopen') as call:
            call.return_value.__enter__.return_value.read.return_value=raw
            with self.assertRaises(ValueError):extract({'type':'invoice','text':'Factura F001'})
