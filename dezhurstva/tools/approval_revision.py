"""Content binding shared by publishing, rendering and aggregate consumption.

This hash identifies the schedule and roster, not the sender of a response.
Mutable collection/publication state must not invalidate the content binding.
"""
import hashlib
import json

EXCLUDED = {'status', 'final_at', 'finalization', 'confirm'}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def revision(month, data):
    copy = {k: v for k, v in month.items() if k not in EXCLUDED}
    copy['confirm'] = {k: month['confirm'][k] for k in ('version', 'published', 'need')}
    envelope = {
        'month': copy,
        'tz': data['tz'],
        'doctors': {who: data['doctors'][who] for who in month['confirm']['need']},
    }
    return digest(envelope)
