#!/usr/bin/env python3
# export_1cd_v3.py
# Универсальный экспортёр, пробует DatabaseReader, затем container_reader, затем supply_reader.
# Сохраняет CSV/JSONL и сырые документы/вложенные файлы в out_dir.

import sys, json, importlib, inspect, traceback
from pathlib import Path

try:
    import pandas as pd
except Exception:
    print("Please: pip install pandas", file=sys.stderr)
    raise

if len(sys.argv) < 3:
    print("Usage: python export_1cd_v3.py /path/to/1Cv8.1CD /path/to/out", file=sys.stderr)
    sys.exit(1)

SRC = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
OUT.mkdir(parents=True, exist_ok=True)

LOG = {"tried": [], "errors": [], "found": {}, "exports": []}
def save_log():
    (OUT / "_export_1cd_v3_debug.json").write_text(json.dumps(LOG, indent=2, ensure_ascii=False), encoding="utf-8")

def safe(obj):
    try:
        return json.loads(json.dumps(obj, default=str))
    except Exception:
        return str(obj)

def try_database_reader():
    """Попробовать DatabaseReader (список "таблиц" / регистров)"""
    try:
        mod = importlib.import_module("onec_dtools.database_reader")
    except Exception as e:
        LOG["tried"].append(("database_reader_import", str(e)))
        return False
    LOG["tried"].append("database_reader_loaded")
    # найти класс DatabaseReader
    DBCls = None
    for name, obj in inspect.getmembers(mod):
        if name.lower().find("databaseread")!=-1 or name.lower().find("reader")!=-1:
            if inspect.isclass(obj):
                DBCls = obj
                break
    if DBCls is None:
        # fallback: look for DatabaseReader in root
        try:
            import onec_dtools
            DBCls = getattr(onec_dtools, "DatabaseReader", None)
        except Exception:
            DBCls = None
    if DBCls is None:
        LOG["tried"].append("database_reader_no_class")
        return False

    LOG["found"]["DatabaseReader"] = DBCls.__name__
    try:
        db = DBCls(str(SRC))
    except Exception as e:
        LOG["errors"].append(("DatabaseReader_ctor", str(e)))
        return False

    LOG["tried"].append("DatabaseReader_instantiated")
    # попытки получить список таблиц
    tables = None
    for cand in ("tables","table_names","list_tables","get_tables","names","objects"):
        if hasattr(db, cand):
            try:
                t = getattr(db, cand)
                tables = t() if callable(t) else t
                break
            except Exception as e:
                LOG["errors"].append(("DatabaseReader_table_get_"+cand, str(e)))
    if not tables:
        LOG["tried"].append("DatabaseReader_no_tables")
        return False

    LOG["found"]["tables_count"] = len(tables) if hasattr(tables, "__len__") else "?"
    # экспортировать каждую таблицу
    for t in list(tables):
        try:
            # попытки чтения строк таблицы
            rows_iter = None
            for cand in ("read_table","table","read","iter_rows","rows","get_rows"):
                if hasattr(db, cand):
                    fn = getattr(db, cand)
                    try:
                        rows_iter = fn(t) if callable(fn) else fn
                        break
                    except Exception:
                        # возможно API: db.table(t).rows()
                        try:
                            tbl = fn(t)
                            rows_iter = getattr(tbl, "rows", lambda: [])()
                            break
                        except Exception:
                            continue
            if rows_iter is None:
                LOG["errors"].append(("no_rows_iter", str(t)))
                continue
            rows = []
            for r in rows_iter:
                try:
                    rows.append(dict(r) if not isinstance(r, dict) else r)
                except Exception:
                    # best-effort convert object to dict via attributes
                    try:
                        rows.append({k:getattr(r,k) for k in dir(r) if not k.startswith("_")})
                    except Exception:
                        rows.append(str(r))
            if not rows:
                continue
            safe_name = "".join(c if c.isalnum() or c in ("-","_") else "_" for c in str(t))
            df = pd.DataFrame(rows)
            csvf = OUT / f"{safe_name}.csv"
            jsonlf = OUT / f"{safe_name}.jsonl"
            df.to_csv(csvf, index=False)
            df.to_json(jsonlf, orient="records", lines=True, force_ascii=False)
            LOG["exports"].append(str(csvf))
        except Exception as e:
            LOG["errors"].append(("export_table", str(t), str(e)))
    save_log()
    return True

def try_container_reader():
    """Попытка через container_reader - генерирует документы / записи."""
    try:
        mod = importlib.import_module("onec_dtools.container_reader")
    except Exception as e:
        LOG["tried"].append(("container_reader_import", str(e)))
        return False
    LOG["tried"].append("container_reader_loaded")
    # возможные функции: read_document_gen, read_entries, read_full_document, extract, read_document
    candidates = ["read_document_gen","read_entries","read_full_document","read_document","read_entries_gen","extract"]
    for cand in candidates:
        if hasattr(mod, cand):
            fn = getattr(mod, cand)
            LOG["tried"].append(f"container_reader_fn:{cand}")
            try:
                gen = fn(str(SRC))
            except TypeError:
                try:
                    gen = fn(open(str(SRC),"rb"))
                except Exception as e:
                    LOG["errors"].append((cand, "call_failed", str(e)))
                    continue
            except Exception as e:
                LOG["errors"].append((cand, "call_failed", str(e)))
                continue

            # если получили итератор/генератор — обрабатываем документы
            try:
                count = 0
                for doc in gen:
                    count += 1
                    # пытаемся извлечь понятный словарь
                    if isinstance(doc, dict):
                        rec = doc
                    else:
                        # объект: собираем публичные атрибуты
                        rec = {}
                        for k in dir(doc):
                            if k.startswith("_"): continue
                            try:
                                val = getattr(doc, k)
                                # skip methods
                                if callable(val): continue
                                rec[k] = val
                            except Exception:
                                pass
                    # создаём для каждого документа JSON файл и, если есть файлы-вложения, сохраняем
                    outbase = OUT / f"doc_{cand}_{count}"
                    outbase.parent.mkdir(parents=True, exist_ok=True)
                    (outbase.with_suffix(".json")).write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
                    # try to detect files inside doc (attributes that look like bytes or file-like)
                    for k,v in list(rec.items()):
                        if isinstance(v, (bytes, bytearray)):
                            try:
                                (outbase / f"{k}.bin").write_bytes(v)
                                # replace with filename in json
                                rec[k] = f"{outbase.name}/{k}.bin"
                            except Exception:
                                pass
                    # rewrite json with potential file refs
                    (outbase.with_suffix(".json")).write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
                    if count % 100 == 0:
                        save_log()
                LOG["found"]["container_docs_count"] = count
                save_log()
                return True
            except Exception as e:
                LOG["errors"].append(("container_iter_error", str(e), traceback.format_exc()))
                save_log()
                return False
    LOG["tried"].append("container_reader_no_candidate_fn")
    return False

def try_supply_reader():
    try:
        mod = importlib.import_module("onec_dtools.supply_reader")
    except Exception as e:
        LOG["tried"].append(("supply_reader_import", str(e)))
        return False
    LOG["tried"].append("supply_reader_loaded")
    # try classes
    for name, obj in inspect.getmembers(mod):
        if inspect.isclass(obj):
            try:
                inst = obj(str(SRC))
                # try to iterate entries
                if hasattr(inst, "entries") or hasattr(inst, "read"):
                    try:
                        rows = list(inst.read() if hasattr(inst, "read") else inst.entries())
                        # dump
                        safe_name = f"supply_{name}"
                        df = pd.DataFrame(rows)
                        df.to_csv(OUT / f"{safe_name}.csv", index=False)
                        LOG["exports"].append(str(OUT / f"{safe_name}.csv"))
                        save_log()
                        return True
                    except Exception as e:
                        LOG["errors"].append(("supply_reader_iter", str(e)))
            except Exception as e:
                LOG["errors"].append(("supply_reader_ctor_"+name, str(e)))
    return False

# Попытки в порядке приоритета
if try_database_reader():
    print("DatabaseReader succeeded. See exports in:", OUT)
    save_log()
    sys.exit(0)

print("DatabaseReader failed; trying container_reader...")
if try_container_reader():
    print("Container reader exported documents to:", OUT)
    save_log()
    sys.exit(0)

print("container_reader failed; trying supply_reader...")
if try_supply_reader():
    print("Supply reader exported to:", OUT)
    save_log()
    sys.exit(0)

print("All attempts failed. See debug log at:", OUT / "_export_1cd_v3_debug.json")
save_log()
sys.exit(2)
