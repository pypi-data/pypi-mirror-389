# insurance_type_cache.py
# XP/Python 3.4.4 compatible helper for persisting insurance type codes
# Stored alongside the CSV file referenced by config['CSV_FILE_PATH']
#
# Schema (kept lean; avoid names/PHI where possible):
# {
#   "version": 1,
#   "lastUpdated": "YYYY-MM-DDTHH:MM:SSZ",
#   "by_patient_id": {
#       "<patient_id>": {"code": "12", "payer_id": "87726", "member_id": "...", "dob": "YYYY-MM-DD"}
#   },
#   "by_dob_member": {
#       "<dob>|<member_id>": {"code": "12", "payer_id": "87726"}
#   }
# }

from __future__ import print_function

import os
import io
import json
import time


def _now_iso_utc():
    # Minimal ISO-like timestamp to avoid pulling in datetime/tz complexities on XP
    try:
        # time.gmtime returns UTC; format YYYY-MM-DDTHH:MM:SSZ
        t = time.gmtime()
        return "%04d-%02d-%02dT%02d:%02d:%02dZ" % (
            t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec
        )
    except Exception:
        return ""


def get_csv_dir_from_config(config):
    """
    Resolve the CSV directory from the provided config without hardcoding paths.
    Falls back to empty string if not available.
    """
    try:
        csv_path = config.get('CSV_FILE_PATH', '')
        if csv_path:
            return os.path.dirname(csv_path)
    except Exception:
        pass
    return ''


def get_cache_path(csv_dir):
    """Return the full path to the cache file in the given directory."""
    return os.path.join(csv_dir or '', 'insurance_type_cache.json')


def _empty_cache():
    return {"version": 1, "lastUpdated": _now_iso_utc(), "by_patient_id": {}, "by_dob_member": {}}


def load_cache(csv_dir):
    """
    Load the cache JSON. Returns a dict. If file does not exist or is invalid, returns empty cache structure.
    """
    path = get_cache_path(csv_dir)
    try:
        if not path or not os.path.exists(path):
            return _empty_cache()
        # Use io.open for XP compatibility and explicit encoding
        with io.open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Basic shape validation
            if not isinstance(data, dict):
                return _empty_cache()
            if 'by_patient_id' not in data or 'by_dob_member' not in data:
                data.setdefault('by_patient_id', {})
                data.setdefault('by_dob_member', {})
            return data
    except Exception:
        # Never raise; return empty to avoid breaking flows
        return _empty_cache()


def save_cache(csv_dir, cache_dict):
    """
    Save the cache JSON with a best-effort atomic write (temp file + rename).
    Avoid verbose logging to keep PHI out of logs.
    """
    if not csv_dir:
        return
    try:
        if not os.path.isdir(csv_dir):
            # Best effort: attempt to create directory if missing
            try:
                os.makedirs(csv_dir)
            except Exception:
                pass

        cache_dict = cache_dict or _empty_cache()
        cache_dict['lastUpdated'] = _now_iso_utc()

        path = get_cache_path(csv_dir)
        tmp_path = path + '.tmp'
        # Write to temp file first
        with io.open(tmp_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(cache_dict, indent=2, sort_keys=True))

        # On Windows/XP, os.rename will overwrite if target exists when on same volume
        try:
            os.rename(tmp_path, path)
        except Exception:
            # Best effort fallback: try remove then rename
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass
            try:
                os.rename(tmp_path, path)
            except Exception:
                # Give up silently; the temp file remains
                pass
    except Exception:
        # Silent failure by design
        pass


def _normalize_str(value):
    try:
        if value is None:
            return ''
        s = str(value).strip()
        return s
    except Exception:
        return ''


def make_dob_member_key(dob, member_id):
    dob_norm = _normalize_str(dob)
    mem_norm = _normalize_str(member_id)
    return dob_norm + '|' + mem_norm if dob_norm or mem_norm else ''


def _put_by_patient_id(cache_dict, patient_id, payload):
    if not patient_id:
        return
    try:
        by_pid = cache_dict.setdefault('by_patient_id', {})
        by_pid[patient_id] = payload
    except Exception:
        pass


def _put_by_dob_member(cache_dict, dob, member_id, payload):
    key = make_dob_member_key(dob, member_id)
    if not key:
        return
    try:
        by_dm = cache_dict.setdefault('by_dob_member', {})
        by_dm[key] = payload
    except Exception:
        pass


def put_entry(csv_dir, patient_id, dob, member_id, payer_id, code):
    """
    Insert or update an entry in the cache. Stores under both indexes when possible.
    - patient_id: CHART when available (preferred key)
    - dob/member_id: fallback key for when patient_id is not available
    - payer_id: retained to aid debugging and potential future logic; avoid logging
    - code: insurance type code as provided by API
    """
    try:
        code_norm = _normalize_str(code)
        if not code_norm:
            return
        cache_dict = load_cache(csv_dir)
        payload_pid = {
            'code': code_norm,
            'payer_id': _normalize_str(payer_id),
            'member_id': _normalize_str(member_id),
            'dob': _normalize_str(dob)
        }
        payload_dm = {
            'code': code_norm,
            'payer_id': _normalize_str(payer_id)
        }
        _put_by_patient_id(cache_dict, _normalize_str(patient_id), payload_pid)
        _put_by_dob_member(cache_dict, dob, member_id, payload_dm)
        save_cache(csv_dir, cache_dict)
    except Exception:
        # Silent by design
        pass


def lookup(patient_id=None, dob=None, member_id=None, csv_dir=None):
    """
    Lookup insurance type code by patient_id first, then by (dob, member_id).
    Returns the code string or None.
    """
    try:
        cache_dict = load_cache(csv_dir)

        # Preferred: by patient_id
        pid = _normalize_str(patient_id)
        if pid:
            try:
                by_pid = cache_dict.get('by_patient_id', {})
                payload = by_pid.get(pid)
                if payload and 'code' in payload:
                    code = _normalize_str(payload.get('code'))
                    if code:
                        return code
            except Exception:
                pass

        # Fallback: by (dob, member_id)
        key = make_dob_member_key(dob, member_id)
        if key:
            try:
                by_dm = cache_dict.get('by_dob_member', {})
                payload2 = by_dm.get(key)
                if payload2 and 'code' in payload2:
                    code2 = _normalize_str(payload2.get('code'))
                    if code2:
                        return code2
            except Exception:
                pass
    except Exception:
        pass
    return None


