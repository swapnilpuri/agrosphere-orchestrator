"""Back up and additively migrate the authorized local database, preserving old rows."""
import hashlib
import json
import sqlite3
import subprocess
import sys
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from sqlalchemy.engine import make_url
from agrosphere_orchestrator.config.settings import Settings

root=Path.cwd()
settings=Settings()
database=Path(make_url(settings.database_url).database).resolve()
folder=root/".aeo/backups"
folder.mkdir(parents=True,exist_ok=True)
backup=folder/("pre-aeo5r-"+datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")+".db")
if backup.exists():raise RuntimeError("Backup already exists")
with closing(sqlite3.connect(database.as_uri()+"?mode=ro",uri=True)) as source,closing(sqlite3.connect(backup)) as target:
    source.backup(target)

def inventory():
    output={}
    with closing(sqlite3.connect(database.as_uri()+"?mode=ro",uri=True)) as connection:
        for (table,) in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name != 'alembic_version' ORDER BY name"):
            quoted='"'+table.replace('"','""')+'"'
            rows=connection.execute("SELECT * FROM "+quoted+" ORDER BY rowid").fetchall()
            raw=json.dumps(rows,sort_keys=True,default=str).encode()
            output[table]={"rows":len(rows),"sha256":hashlib.sha256(raw).hexdigest()}
    return output
before=inventory()
commands=[]
for args in (["upgrade","head"],["check"]):
    argv=[sys.executable,"-m","alembic",*args]
    completed=subprocess.run(argv,cwd=root,capture_output=True,text=True,timeout=120)
    commands.append({"argv":argv,"exit_code":completed.returncode,"stdout":completed.stdout,"stderr":completed.stderr})
    if completed.returncode:break
after=inventory()
preserved=all(after.get(table)==value for table,value in before.items())
result={"executed_at":datetime.now(UTC).isoformat(),"database":str(database),"backup":str(backup),"commands":commands,"before":before,"after":after,"all_existing_rows_preserved":preserved,"new_tables":sorted(set(after)-set(before)),"remote_mutations":False}
(root/"docs/milestones/AEO-5/evidence/runtime-migration.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"existing_tables":len(before),"existing_rows_preserved":preserved,"new_tables":result["new_tables"],"exit_codes":[c["exit_code"] for c in commands]},indent=2))
raise SystemExit(not preserved or any(c["exit_code"] for c in commands))
