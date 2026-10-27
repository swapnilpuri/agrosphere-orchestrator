import json,os,sqlite3,subprocess,sys,tempfile,shutil
from pathlib import Path
R=Path.cwd();O=R/'docs/milestones/AEO-6.1/design-after-requirements/evidence'; V=O/'regression';V.mkdir(exist_ok=True)
preserve=[p for p in (R/'docs/schemas').glob('*.json')]+[R/'docs/validation'/n for n in ('commands.json','pytest.xml','aeo2-docs.json','aeo3-docs.json','aeo4-docs.json','design-tools.json')]
originals={str(p):p.read_bytes() for p in preserve if p.exists()}
for p,b in originals.items():
 q=V/'prior'/Path(p).relative_to(R);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
with tempfile.TemporaryDirectory(prefix='aeo61-validation-',ignore_cleanup_errors=True) as t:
 backup=Path(t)/'validation.db'
 with sqlite3.connect((R/'aeo.db').as_uri()+'?mode=ro',uri=True) as source,sqlite3.connect(backup) as dest:source.backup(dest)
 source.close();dest.close()
 fixture=Path(tempfile.mkdtemp(prefix='.t61-',dir=R.parent)).resolve()
 assert fixture.is_relative_to(R.parent.resolve())
 env={**os.environ,'AEO_DATABASE_URL':'sqlite:///'+backup.as_posix(),'AEO_PLANTUML_JAR':str(R/'.aeo/tools/plantuml-1.2026.9.jar'),'PYTEST_ADDOPTS':'--basetemp='+fixture.as_posix()}
 try:
  p=subprocess.run([sys.executable,'scripts/validate.py'],cwd=R,env=env,capture_output=True,text=True,timeout=2400)
  (V/'runner.json').write_text(json.dumps({'argv':[sys.executable,'scripts/validate.py'],'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'database':'disposable SQLite backup; authoritative DB unchanged','fixture_root':str(fixture)},indent=2)+'\n')
  for name in ('commands.json','pytest.xml'):shutil.copyfile(R/'docs/validation'/name,V/name)
 finally:
  for name,b in originals.items():Path(name).write_bytes(b)
 print(json.dumps({'exit_code':p.returncode,'stdout_tail':p.stdout[-1800:],'stderr_tail':p.stderr[-800:]}))
 sys.exit(p.returncode)
