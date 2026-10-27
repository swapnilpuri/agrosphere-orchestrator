import json,subprocess
from pathlib import Path
R=Path.cwd();E=R/'docs/milestones/AEO-6.1/design-after-requirements/evidence'
baseline=json.loads((E/'git-before.json').read_text())['stdout']
for name in ('aeo2-docs.json','aeo3-docs.json','aeo4-docs.json','design-tools.json'):
 rel='docs/validation/'+name
 assert rel not in baseline,'Never restore an originally dirty file'
 result=subprocess.run(['git','show','HEAD:'+rel],capture_output=True,check=True)
 target=R/rel
 (E/'regression'/name).write_bytes(target.read_bytes())
 target.write_bytes(result.stdout.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n'))
print('Restored four originally clean verifier report files; retained new outputs in review evidence')
