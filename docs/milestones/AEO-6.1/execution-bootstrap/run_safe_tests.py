"""Safe targeted existing regression suites with exact command/output retention."""
import json, os, subprocess, sys, uuid
from pathlib import Path
ROOT=Path.cwd(); OUT=Path(__file__).resolve().parent
fixture=(ROOT.parent/('.t61-b-'+uuid.uuid4().hex[:8])).resolve()
assert fixture.parent==ROOT.parent.resolve() and not fixture.exists()
argv=[sys.executable,'-m','pytest','-q','-p','no:cacheprovider','--basetemp='+fixture.as_posix(),'--junitxml='+str(OUT/'pytest.xml'),'tests/test_configuration.py','tests/test_cli_planning.py','tests/test_persistence_state.py','tests/test_orchestration.py','tests/test_autonomous_recovery.py']
env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
p=subprocess.run(argv,cwd=ROOT,env=env,capture_output=True,text=True,timeout=600)
result={'argv':argv,'cwd':str(ROOT),'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'fixture_root':str(fixture),'live_model_or_provider':False,'test_note':'Existing suites use disposable SQLite/Git fixtures and injected test doubles; not live authentication or native certification.'}
(OUT/'test-results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps(result));sys.exit(p.returncode)
