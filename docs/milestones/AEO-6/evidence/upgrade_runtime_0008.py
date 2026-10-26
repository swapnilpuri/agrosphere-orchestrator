"""Back up the configured runtime and apply only the approved additive schema migration."""
import hashlib
import json
import sqlite3
from datetime import UTC,datetime
from pathlib import Path
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url
from agrosphere_orchestrator.config.settings import Settings

root=Path.cwd().resolve()
out=root/'docs/milestones/AEO-6/evidence'
validation=json.loads((out/'implementation-validation/runner.json').read_text(encoding='utf-8'))
assert validation['exit_code']==0,'Full validator must pass before runtime schema upgrade'
inventory=json.loads((out/'implementation-source-manifest.json').read_text(encoding='utf-8'))
assert all(hashlib.sha256((root/f['path']).read_bytes()).hexdigest()==f['sha256'] for f in inventory['files'])
settings=Settings()
url=make_url(settings.database_url)
assert url.drivername=='sqlite' and url.database
runtime=Path(url.database).resolve()
assert runtime.parent==root and runtime.name=='aeo.db'
backup_directory=root/'.aeo/backups'
backup_directory.mkdir(parents=True,exist_ok=True)
backup=backup_directory/('aeo-before-0008-'+datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')+'.db')
with sqlite3.connect(runtime.as_uri()+'?mode=ro',uri=True) as source:
    names=[r[0] for r in source.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    version=source.execute('SELECT version_num FROM alembic_version').fetchone()[0]
    assert version=='0007'
    with sqlite3.connect(backup) as target:
        source.backup(target)
    before={name:list(source.execute('SELECT * FROM "'+name+'"')) for name in names if name!='alembic_version'}
config=Config(str(root/'alembic.ini'))
config.set_main_option('script_location',str(root/'migrations'))
command.upgrade(config,'0008')
with sqlite3.connect(runtime.as_uri()+'?mode=ro',uri=True) as current:
    after={name:list(current.execute('SELECT * FROM "'+name+'"')) for name in names if name!='alembic_version'}
    assert after==before,'Pre-existing data changed during additive upgrade'
    new_names=[r[0] for r in current.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    assert set(new_names)-set(names)=={'autonomous_runs','autonomous_operations','autonomous_events'}
    assert all(current.execute('SELECT COUNT(*) FROM "'+name+'"').fetchone()[0]==0 for name in set(new_names)-set(names))
    assert current.execute('SELECT version_num FROM alembic_version').fetchone()[0]=='0008'
command.check(config)
result={'database':str(runtime),'backup':str(backup),'before_migration':version,'after_migration':'0008','before_tables':len(names),'after_tables':len(new_names),'all_preexisting_table_records_preserved':True,'new_runtime_autonomous_records':0,'approval_records_changed':False,'source_inventory_verified':True}
(out/'runtime-migration-0008.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
