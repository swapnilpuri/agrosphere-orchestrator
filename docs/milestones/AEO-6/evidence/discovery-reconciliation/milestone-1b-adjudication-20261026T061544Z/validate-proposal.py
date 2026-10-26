"""Validate only the unregistered proposed requirements and existing context guards."""
import json, hashlib, subprocess
from pathlib import Path
from agrosphere_orchestrator.design_models import DesignInput
from agrosphere_orchestrator.design_validation import verify_context
V=Path(__file__).resolve().parent; ROOT=V.parents[4]
# Resolve actual orchestrator path explicitly; never mutate registered scope.
ROOT=Path('C:/Projects/agrosphere/agrosphere-orchestrator')
p=V/'AEO-6-ADJUDICATION.requirements-proposed.json'
data=json.loads(p.read_text(encoding='utf-8'))
head=subprocess.run(['git','--no-optional-locks','-C',str(ROOT),'rev-parse','HEAD'],capture_output=True,text=True,check=True).stdout.strip()
for ref in data['context']: ref['head']=head
p.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
inputs=DesignInput.model_validate(data)
repositories=verify_context(inputs,V/'design-repositories-proposed.json',ROOT/'config/roles.yaml')
result={'schema_valid':True,'context_valid':True,'repositories':repositories,'proposal_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'registration_performed':False,'requirements_approval_granted':False,'design_approval_granted':False,'implementation_authorized':False,'autonomous_run_created':False}
(V/'proposal-validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
