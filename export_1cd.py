# export_any_1cd.py
import sys, json
from pathlib import Path
import pandas as pd

if len(sys.argv) < 3:
    print("Usage: python export_any_1cd.py /path/to/base.1cd /path/to/output_dir", file=sys.stderr)
    sys.exit(1)

onecd_path = Path(sys.argv[1]).resolve()
out_dir = Path(sys.argv[2]).resolve()
out_dir.mkdir(parents=True, exist_ok=True)

try:
    m = __import__("onec_dtools")
except Exception as e:
    print("Не найден модуль onec_dtools:", e, file=sys.stderr)
    sys.exit(2)

# Шаг 1: пытаемся создать объект БД/ридера
db = None
errors = {}
for name in ("open_db", "open", "Database", "DB", "Reader", "ReaderV8", "OneCD", "OneCDB"):
    if hasattr(m, name):
        obj = getattr(m, name)
        try:
            db = obj(str(onecd_path)) if callable(obj) else obj
            break
        except Exception as e:
            errors[f"ctor:{name}"] = repr(e)

if db is None:
    # иногда фабрики лежат во вложенных модулях
    for sub in ("db", "core", "v8", "reader"):
        try:
            sm = __import__(f"onec_dtools.{sub}", fromlist=["*"])
        except Exception as e:
            errors[f"submod:{sub}"] = repr(e); continue
        for name in dir(sm):
            obj = getattr(sm, name)
            if callable(obj):
                try:
                    db = obj(str(onecd_path))
                    break
                except Exception:
                    pass
        if db: break

if db is None:
    (out_dir / "_debug_onedtools_attrs.json").write_text(
        json.dumps(sorted([a for a in dir(m) if not a.startswith("_")]), indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print("Не удалось создать объект БД из onec_dtools. См. _debug_onedtools_attrs.json", file=sys.stderr)
    sys.exit(3)

# Шаг 2: получаем список таблиц
tables = None
for cand in ("tables", "table_names", "list_tables", "get_tables", "names"):
    if hasattr(db, cand):
        t = getattr(db, cand)
        try:
            tables = t() if callable(t) else t
            break
        except Exception:
            pass
if not tables:
    print("Не удалось получить список таблиц из onec_dtools.", file=sys.stderr)
    sys.exit(4)

# Шаг 3: читаем строки из каждой таблицы
exported = []
for t in tables:
    get_rows = None
    for cand in ("read_table", "table", "read", "iter_rows", "rows"):
        if hasattr(db, cand):
            get_rows = getattr(db, cand); break
    try:
        rows_iter = get_rows(t) if callable(get_rows) else []
    except TypeError:
        # на случай API вида: table(name)->obj; obj.rows() -> iter
        tbl = get_rows(t) if callable(get_rows) else None
        rows_iter = getattr(tbl, "rows", lambda: [])()
    rows = (dict(r) if not isinstance(r, dict) else r for r in rows_iter)

    safe = "".join(c if c.isalnum() or c in ("-","_") else "_" for c in str(t))
    df = pd.DataFrame(list(rows))
    df.to_csv(out_dir / f"{safe}.csv", index=False)
    df.to_json(out_dir / f"{safe}.jsonl", orient="records", lines=True, force_ascii=False)
    try:
        df.to_parquet(out_dir / f"{safe}.parquet", index=False)
    except Exception:
        pass
    exported.append(safe)

(out_dir / "_export_report.json").write_text(
    json.dumps({"tables": list(map(str, tables)), "exported": exported}, ensure_ascii=False, indent=2),
    encoding="utf-8"
)
print(f"Done. Exported {len(exported)} tables -> {out_dir}")
