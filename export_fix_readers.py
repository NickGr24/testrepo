#!/usr/bin/env python3
# export_fix_readers.py
# Попытка использовать reader-API, передавая file-like объект (open(..., "rb")).

import sys, json, importlib, inspect, traceback
from pathlib import Path

try:
    import pandas as pd
except Exception:
    print("Please: pip install pandas", file=sys.stderr)
    raise

if len(sys.argv) < 3:
    print("Usage: python export_fix_readers.py /path/to/1Cv8.1CD /path/to/out", file=sys.stderr)
    sys.exit(1)

SRC_PATH = Path(sys.argv[1]).expanduser().resolve()
OUT = Path(sys.argv[2]).expanduser().resolve()
OUT.mkdir(parents=True, exist_ok=True)

LOG = {"attempts": [], "errors": [], "exports": [], "notes": []}

def save_log():
    (OUT / "_export_fix_debug.json").write_text(json.dumps(LOG, indent=2, ensure_ascii=False), encoding="utf-8")

def try_database_reader(fobj):
    """Попытка создать DatabaseReader(fileobj)"""
    try:
        mod = importlib.import_module("onec_dtools.database_reader")
    except Exception as e:
        LOG["attempts"].append(("database_reader_import_err", str(e)))
        return False
    LOG["attempts"].append("database_reader_loaded")
    DBCls = getattr(mod, "DatabaseReader", None)
    if DBCls is None:
        # попытаться найти класс вручную
        for name, obj in inspect.getmembers(mod):
            if inspect.isclass(obj) and "Database" in name:
                DBCls = obj
                break
    if DBCls is None:
        LOG["attempts"].append("database_reader_no_class")
        return False

    try:
        db = DBCls(fobj)  # передаём file-like объект
    except Exception as e:
        LOG["errors"].append(("DatabaseReader_ctor", str(e)))
        return False

    LOG["attempts"].append("DatabaseReader_instantiated")
    # получить имена таблиц
    tables = None
    for cand in ("tables","table_names","list_tables","get_tables","names","objects"):
        if hasattr(db, cand):
            try:
                fn = getattr(db, cand)
                tables = fn() if callable(fn) else fn
                break
            except Exception as e:
                LOG["errors"].append(("DatabaseReader_table_get_"+cand, str(e)))
    if not tables:
        LOG["attempts"].append("DatabaseReader_no_tables")
        return False

    LOG["attempts"].append(("DatabaseReader_tables_count", len(tables) if hasattr(tables, "__len__") else "?"))
    # читать и экспортировать
    for t in list(tables):
        try:
            rows_iter = None
            for cand in ("read_table","table","read","iter_rows","rows","get_rows"):
                if hasattr(db, cand):
                    fn = getattr(db, cand)
                    try:
                        rows_iter = fn(t) if callable(fn) else fn
                        break
                    except Exception:
                        # попробовать db.table(t).rows()
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
                    # fallback: grab public attrs
                    try:
                        rows.append({k:getattr(r,k) for k in dir(r) if not k.startswith("_") and not callable(getattr(r,k))})
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

def try_container_reader_with_file(fobj):
    """Попытка вызвать функции контейнерного ридера, передав file-like объект"""
    try:
        mod = importlib.import_module("onec_dtools.container_reader")
    except Exception as e:
        LOG["attempts"].append(("container_reader_import_err", str(e)))
        return False
    LOG["attempts"].append("container_reader_loaded")
    # функции кандидаты
    candidates = ["read_document_gen","read_entries","read_full_document","read_document","extract","read_document_gen"]
    for cand in candidates:
        if hasattr(mod, cand):
            fn = getattr(mod, cand)
            LOG["attempts"].append(f"container_reader_fn:{cand}")
            try:
                gen = fn(fobj)  # передаём file obj
            except TypeError:
                try:
                    # иногда fn требует путь *или* fileobj; пробуем both patterns
                    gen = fn(str(SRC_PATH))
                except Exception as e:
                    LOG["errors"].append((cand, "call_failed", str(e)))
                    continue
            except Exception as e:
                LOG["errors"].append((cand, "call_failed", str(e)))
                continue

            # обработка генератора документов
            try:
                count = 0
                for doc in gen:
                    count += 1
                    if isinstance(doc, dict):
                        rec = doc
                    else:
                        rec = {}
                        for k in dir(doc):
                            if k.startswith("_"): continue
                            try:
                                v = getattr(doc, k)
                                if callable(v): continue
                                rec[k] = v
                            except Exception:
                                pass
                    outbase = OUT / f"doc_{cand}_{count}"
                    (outbase.with_suffix(".json")).write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
                    # вложения
                    for k,v in list(rec.items()):
                        if isinstance(v, (bytes, bytearray)):
                            try:
                                (outbase.parent / (outbase.name + f"_{k}.bin")).write_bytes(v)
                                rec[k] = f"{outbase.name}_{k}.bin"
                            except Exception:
                                pass
                    (outbase.with_suffix(".json")).write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
                    if count % 100 == 0:
                        save_log()
                LOG["attempts"].append(("container_reader_docs", count))
                save_log()
                return True
            except Exception as e:
                LOG["errors"].append(("container_iter_error", str(e), traceback.format_exc()))
                save_log()
                return False
    LOG["attempts"].append("container_reader_no_candidate_fn")
    return False

def try_supply_reader_with_file(fobj):
    try:
        mod = importlib.import_module("onec_dtools.supply_reader")
    except Exception as e:
        LOG["attempts"].append(("supply_reader_import_err", str(e)))
        return False
    LOG["attempts"].append("supply_reader_loaded")
    for name, obj in inspect.getmembers(mod):
        if inspect.isclass(obj):
            try:
                inst = obj(fobj)
                # try entries/read
                if hasattr(inst, "read") or hasattr(inst, "entries"):
                    try:
                        rows = list(inst.read() if hasattr(inst, "read") else inst.entries())
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

# Открываем файл один раз и пробуем все читатели, передавая file-like object.
with open(str(SRC_PATH), "rb") as f:
    # try DatabaseReader using file-like
    try:
        ok = try_database_reader(f)
        if ok:
            print("DatabaseReader succeeded. Exports:", LOG["exports"])
            save_log()
            sys.exit(0)
    except Exception as e:
        LOG["errors"].append(("try_database_reader_unexpected", str(e), traceback.format_exc()))

    # reset cursor to start
    try:
        f.seek(0)
    except Exception:
        pass

    try:
        ok = try_container_reader_with_file(f)
        if ok:
            print("Container reader succeeded. Check exported docs in out dir.")
            save_log()
            sys.exit(0)
    except Exception as e:
        LOG["errors"].append(("try_container_reader_unexpected", str(e), traceback.format_exc()))

    try:
        f.seek(0)
    except Exception:
        pass

    try:
        ok = try_supply_reader_with_file(f)
        if ok:
            print("Supply reader succeeded. Exports:", LOG["exports"])
            save_log()
            sys.exit(0)
    except Exception as e:
        LOG["errors"].append(("try_supply_reader_unexpected", str(e), traceback.format_exc()))

# nothing worked
save_log()
print("No reader produced exports. See log at:", OUT / "_export_fix_debug.json")
sys.exit(2)
