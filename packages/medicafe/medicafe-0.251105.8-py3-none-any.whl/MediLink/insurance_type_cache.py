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

# Safe logger import with fallback
try:
    from MediCafe.core_utils import get_shared_config_loader
    _logger = get_shared_config_loader()
except Exception:
    _logger = None

def _log(message, level="DEBUG"):
    """Helper to log messages if logger is available."""
    if _logger and hasattr(_logger, 'log'):
        try:
            _logger.log(message, level=level)
        except Exception:
            pass


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
        if not path:
            _log("Cache load: path is empty (csv_dir='{}')".format(csv_dir), level="DEBUG")
            return _empty_cache()
        if not os.path.exists(path):
            _log("Cache load: file not found at '{}'".format(path), level="DEBUG")
            return _empty_cache()
        # Use io.open for XP compatibility and explicit encoding
        with io.open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Basic shape validation
            if not isinstance(data, dict):
                _log("Cache load: invalid data type (not dict) at '{}'".format(path), level="WARNING")
                return _empty_cache()
            if 'by_patient_id' not in data or 'by_dob_member' not in data:
                data.setdefault('by_patient_id', {})
                data.setdefault('by_dob_member', {})
            _log("Cache load: SUCCESS from '{}'".format(path), level="DEBUG")
            return data
    except Exception as e:
        _log("Cache load: exception '{}' at '{}'".format(str(e), path), level="WARNING")
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
            _log("Cache put_entry SKIP: empty code for patient_id='{}'".format(_normalize_str(patient_id)), level="DEBUG")
            return
        cache_dict = load_cache(csv_dir)
        pid_norm = _normalize_str(patient_id)
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
        _put_by_patient_id(cache_dict, pid_norm, payload_pid)
        _put_by_dob_member(cache_dict, dob, member_id, payload_dm)
        save_cache(csv_dir, cache_dict)
        # Log successful persist (no PHI - patient_id only, no DOB/member_id)
        if pid_norm:
            _log("Cache put_entry SUCCESS: patient_id='{}', code='{}'".format(pid_norm, code_norm), level="DEBUG")
        else:
            dob_member_key = make_dob_member_key(dob, member_id)
            key_display = dob_member_key[:10] + '...' if len(dob_member_key) > 10 else dob_member_key
            _log("Cache put_entry SUCCESS: dob|member_id key='{}', code='{}'".format(key_display, code_norm), level="DEBUG")
    except Exception as e:
        _log("Cache put_entry ERROR: {}".format(str(e)), level="WARNING")


def _lookup_csv_for_dob_member_id(csv_dir, patient_name, service_date, insurance_name, config=None):
    """
    Helper function to look up DOB and member_id from CSV by matching on patient name, service date, and insurance.
    This bridges the gap between fixed-width files (which have CHART) and CSV files (which have Patient ID, DOB, member_id).
    
    Returns tuple (dob, member_id) or (None, None) if not found.
    """
    if not csv_dir:
        return None, None
    
    try:
        # Try to import CSV loading function
        try:
            from MediBot import MediBot_Preprocessor_lib
            # Try to get CSV file path from config first
            csv_file_path = None
            if config:
                try:
                    csv_file_path = config.get('CSV_FILE_PATH', '')
                except Exception:
                    pass
            
            # If not in config, try to find CSV file in directory
            if not csv_file_path or not os.path.exists(csv_file_path):
                try:
                    csv_files = [f for f in os.listdir(csv_dir) if f.lower().endswith('.csv')]
                    if csv_files:
                        csv_file_path = os.path.join(csv_dir, csv_files[0])
                    else:
                        return None, None
                except Exception:
                    return None, None
            
            if not csv_file_path or not os.path.exists(csv_file_path):
                return None, None
            
            csv_data = MediBot_Preprocessor_lib.load_csv_data(csv_file_path)
            
            # Normalize patient name for comparison (simple approach)
            name_parts = _normalize_str(patient_name).upper().split()
            if not name_parts:
                return None, None
            
            # Try to match on name + service date + insurance
            for row in csv_data:
                csv_name = _normalize_str(row.get('Patient Name', '') or row.get('Name', '') or 
                                         ' '.join([row.get('First Name', ''), row.get('Last Name', '')])).upper()
                csv_dob = _normalize_str(row.get('Patient DOB', row.get('DOB', '')))
                csv_member_id = _normalize_str(row.get('Primary Policy Number', row.get('Ins1 Member ID', '')))
                csv_service_date = _normalize_str(row.get('Service Date', row.get('Surgery Date', row.get('Date', ''))))
                csv_insurance = _normalize_str(row.get('Insurance Name', row.get('Ins1 Name', ''))).upper()
                
                # Simple name matching (check if key parts match)
                csv_name_parts = csv_name.split()
                if (len(name_parts) >= 2 and len(csv_name_parts) >= 2 and
                    name_parts[0] in csv_name_parts and name_parts[-1] in csv_name_parts):
                    # Name matches, check service date and insurance if available
                    date_match = not service_date or not csv_service_date or csv_service_date == service_date
                    ins_match = not insurance_name or not csv_insurance or insurance_name in csv_insurance or csv_insurance in insurance_name
                    
                    if date_match and ins_match and csv_dob and csv_member_id:
                        _log("CSV bridge lookup found match: dob='{}', member_id='{}'".format(
                            csv_dob[:10] + '...' if len(csv_dob) > 10 else csv_dob, 
                            csv_member_id[:10] + '...' if len(csv_member_id) > 10 else csv_member_id), level="DEBUG")
                        return csv_dob, csv_member_id
        except Exception as e:
            _log("CSV bridge lookup error: {}".format(str(e)), level="DEBUG")
            return None, None
    except Exception:
        pass
    return None, None


def lookup(patient_id=None, dob=None, member_id=None, csv_dir=None, patient_name=None, payer_id=None, service_date=None, insurance_name=None, config=None):
    """
    Lookup insurance type code using multiple matching strategies (in order of preference):
    1. Exact patient_id match (normalized)
    2. Case-insensitive patient_id match (for format variations)
    3. dob|member_id match (most reliable cross-flow match)
    4. CSV bridge lookup (if dob/member_id not available, try to find via CSV using name/date/insurance)
    5. Patient name + payer_id match (fallback for name-based matching)
    
    Returns the code string or None.
    """
    try:
        cache_dict = load_cache(csv_dir)
        
        # Log cache structure for debugging (no PHI)
        try:
            by_pid_count = len(cache_dict.get('by_patient_id', {}))
            by_dm_count = len(cache_dict.get('by_dob_member', {}))
            # Only log if we have something to report (avoid noise on empty cache)
            if by_pid_count > 0 or by_dm_count > 0:
                _log("Cache loaded: {} patient_id entries, {} dob|member_id entries".format(
                    by_pid_count, by_dm_count), level="DEBUG")
        except Exception:
            pass

        # Strategy 1: Exact patient_id match (normalized)
        pid = _normalize_str(patient_id)
        if pid:
            try:
                by_pid = cache_dict.get('by_patient_id', {})
                # Log available keys for debugging (first 5 only, no PHI concern for patient_id)
                if by_pid:
                    sample_keys = list(by_pid.keys())[:5]
                    _log("Cache lookup Strategy 1 (exact patient_id): searching for '{}', sample keys in cache: {}".format(
                        pid, sample_keys), level="DEBUG")
                payload = by_pid.get(pid)
                if payload and 'code' in payload:
                    code = _normalize_str(payload.get('code'))
                    if code:
                        _log("Cache lookup FOUND by exact patient_id '{}': code='{}'".format(pid, code), level="DEBUG")
                        return code
            except Exception as e:
                _log("Cache lookup exception (exact patient_id): {}".format(str(e)), level="DEBUG")
            
            # Strategy 2: Case-insensitive patient_id match (handle format variations)
            try:
                if by_pid:
                    pid_upper = pid.upper()
                    pid_lower = pid.lower()
                    # Try case-insensitive match
                    for cache_key in by_pid.keys():
                        if _normalize_str(cache_key).upper() == pid_upper or _normalize_str(cache_key).lower() == pid_lower:
                            payload = by_pid.get(cache_key)
                            if payload and 'code' in payload:
                                code = _normalize_str(payload.get('code'))
                                if code:
                                    _log("Cache lookup FOUND by case-insensitive patient_id '{}' (matched '{}'): code='{}'".format(
                                        pid, cache_key, code), level="DEBUG")
                                    return code
                    _log("Cache lookup Strategy 2 (case-insensitive): no match for '{}'".format(pid), level="DEBUG")
            except Exception as e:
                _log("Cache lookup exception (case-insensitive patient_id): {}".format(str(e)), level="DEBUG")

        # Strategy 3: dob|member_id match (most reliable cross-flow match)
        key = make_dob_member_key(dob, member_id)
        if key:
            try:
                by_dm = cache_dict.get('by_dob_member', {})
                payload2 = by_dm.get(key)
                if payload2 and 'code' in payload2:
                    code2 = _normalize_str(payload2.get('code'))
                    if code2:
                        _log("Cache lookup FOUND by dob|member_id: code='{}'".format(code2), level="DEBUG")
                        return code2
                else:
                    # Log sample keys for debugging (first 3 dob|member_id keys, truncated)
                    if by_dm:
                        sample_dm_keys = list(by_dm.keys())[:3]
                        sample_display = [k[:15] + '...' if len(k) > 15 else k for k in sample_dm_keys]
                        _log("Cache lookup Strategy 3 (dob|member_id): searching for '{}...', sample keys: {}".format(
                            key[:15] if len(key) > 15 else key, sample_display), level="DEBUG")
            except Exception as e:
                _log("Cache lookup exception (dob|member_id): {}".format(str(e)), level="DEBUG")
        
        # Strategy 4: CSV bridge lookup - if we don't have dob/member_id, try to find them via CSV
        if not key and patient_name and csv_dir:
            try:
                _log("Cache lookup Strategy 4 (CSV bridge): attempting to find dob/member_id via CSV lookup", level="DEBUG")
                csv_dob, csv_member_id = _lookup_csv_for_dob_member_id(csv_dir, patient_name, service_date, insurance_name, config)
                if csv_dob and csv_member_id:
                    key2 = make_dob_member_key(csv_dob, csv_member_id)
                    if key2:
                        by_dm = cache_dict.get('by_dob_member', {})
                        payload3 = by_dm.get(key2)
                        if payload3 and 'code' in payload3:
                            code3 = _normalize_str(payload3.get('code'))
                            if code3:
                                _log("Cache lookup FOUND via CSV bridge (dob|member_id): code='{}'".format(code3), level="DEBUG")
                                return code3
            except Exception as e:
                _log("Cache lookup exception (CSV bridge): {}".format(str(e)), level="DEBUG")
        
        # Strategy 5: Patient name + payer_id match (fallback - requires both)
        # Note: This is a future enhancement; name matching can be error-prone
        # For now, we'll skip this to avoid false matches
        
        _log("Cache lookup: all strategies exhausted for patient_id='{}'".format(pid), level="DEBUG")
    except Exception as e:
        _log("Cache lookup error: {}".format(str(e)), level="WARNING")
    return None


