"""Final read-only preservation checks and artifact inventory."""
import hashlib,json,re,sqlite3
from pathlib import Path
V=Path(__file__).resolve().parent; BASE=V.parent; ORCH=Path('C:/Projects/agrosphere/agrosphere-orchestrator')
v=json.loads((V/'read-only-verification.json').read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),default=str)
source_ok=all(sha(ORCH/p)==h for p,h in v['source_hashes'].items())
prior_ok=all(sha(BASE/p)==h for p,h in v['prior_artifact_hashes'].items())
snap=json.loads((V/'fresh-discovery.json').read_text())['snapshot']; checked=0
for repo in snap['repositories']:
 for p,h in repo['file_fingerprints'].items():
  assert sha(Path(repo['path'])/p)==h,(repo['id'],p)
  checked+=1
with sqlite3.connect((ORCH/'aeo.db').as_uri()+'?mode=ro',uri=True) as db:
 values={}
 for n in v['database_before']['tables']:
  rows=[list(r) for r in db.execute('SELECT * FROM "'+n.replace('"','""')+'"')]
  values[n]={'count':len(rows),'content_sha256':hashlib.sha256(canon(sorted(rows,key=canon)).encode()).hexdigest()}
db_ok=values==v['database_before']['tables'] and sha(ORCH/'aeo.db')==v['database_before']['file_sha256']
assert source_ok and prior_ok and db_ok
names=['MILESTONE_1B_FORENSIC_REPORT.md','MILESTONE_1B_ADJUDICATION_MATRIX.md','MILESTONE_1B_DECISION_PACKAGE.json','MILESTONE_1B_RECOVERY_VERIFICATION.md']
links=[]
for name in names:
 if not name.endswith('.md'):continue
 for target in re.findall(r'\]\(([^)]+)\)',(BASE/name).read_text(encoding='utf-8')):
  assert (BASE/target).is_file(),target
  links.append(target)
result={'runtime_sources_unchanged':source_ok,'prior_package_unchanged':prior_ok,'database_file_and_all_tables_unchanged':db_ok,'application_fingerprints_verified':checked,'application_repository_count':len(snap['repositories']),'required_artifacts_present':all((BASE/n).is_file() for n in names),'local_report_links_verified':len(links),'schema_and_context_validation':json.loads((V/'proposal-validation.json').read_text()),'tests_executed':[],'source_changes_authorized':False,'run_preserved':True,'outcome':'REQUIRES_AUTHENTICATED_HUMAN_DECISION'}
(V/'final-preservation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
files=[{'path':n,'sha256':sha(BASE/n)} for n in names]
files += [{'path':p.name,'sha256':sha(p)} for p in sorted(V.iterdir()) if p.is_file() and p.name!='ARTIFACT_MANIFEST.json']
(V/'ARTIFACT_MANIFEST.json').write_text(json.dumps({'approval_granted':False,'run_id':v['run_id'],'files':files},indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
