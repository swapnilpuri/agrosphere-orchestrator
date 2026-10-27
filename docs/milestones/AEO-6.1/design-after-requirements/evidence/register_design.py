"""Review-only adapter to existing AEO lifecycle; no approval or implementation."""
import hashlib,json
from pathlib import Path
from sqlalchemy.orm import Session
from agrosphere_orchestrator.design import generate_design,require_approval,design_status
from agrosphere_orchestrator.design_agents import SECTIONS
from agrosphere_orchestrator.design_artifacts import LocalPlantUML,digest
from agrosphere_orchestrator.design_models import Artifact,AgentResult
from agrosphere_orchestrator.persistence import DesignCase
from agrosphere_orchestrator.recovery import recovery_engine
from agrosphere_orchestrator.config.settings import Settings
R=Path.cwd();O=Path(__file__).resolve().parents[1]; spec=json.loads((O/'design-content.json').read_text()); content_hash=digest((O/'design-content.json').read_text())
class ReviewDocumentation:
 version='aeo61-reviewed-design-v1:'+content_hash
 def generate(self,task,inputs):
  result=AgentResult(); refs=[r.id for r in inputs.requirements]
  kinds={'business-analyst':['business'],'solution-architect':['architecture','service'],'technical-writer':['overview']}[task.role]
  for kind in kinds:
   assert set(SECTIONS[kind])==set(spec['sections'][kind])
   text=f'# {inputs.plan.id}: {kind} (design)\n\nScope: {task.scope_digest}\nRequirements: '+', '.join(refs)+'\n'
   for section in SECTIONS[kind]:text+='\n## '+section+'\n\n'+spec['sections'][kind][section]+'\n'
   text+='\n## Registered requirements and criteria\n\n'+'\n'.join(r.id+': '+r.text+'\n'+'\n'.join('- '+a for a in r.acceptance_criteria) for r in inputs.requirements)
   text+='\n\n## Verified context references\n\n'+'\n'.join(f'- {c.repository}/{c.path} sha256={c.sha256} HEAD={c.head}' for c in inputs.context)+'\n'
   result.artifacts.append(Artifact(type=kind,repository='agrosphere-orchestrator',path=kind+'.md',content=text,sha256=digest(text),requirement_ids=refs,agent=task.role))
  if task.role=='solution-architect':
   for name,source in spec['diagrams'].items():
    kind={'adjudication-components':'component','adjudication-state':'state','adjudication-sequence':'sequence'}[name]
    result.artifacts.append(Artifact(type='diagram:'+kind,repository='agrosphere-orchestrator',path='diagrams/'+name+'.puml',content=source,sha256=digest(source),requirement_ids=refs,agent=task.role))
  return result
s=Settings();e=recovery_engine(s.database_url)
jar=R/'.aeo/tools/plantuml-1.2026.9.jar'; assert jar.is_file()
with Session(e) as db:
 c=db.get(DesignCase,'agrosphere:AEO-6-ADJUDICATION'); d=require_approval(db,c,c.scope_id,'requirements')
 assert d.id=='67c78c9f-387d-426b-8e89-64092bd48fd0' and c.revision_id is None,'Do not recreate an existing revision'
revision=generate_design(e,c.id,ReviewDocumentation(),LocalPlantUML(jar,s.java_executable),digest(jar.read_bytes().hex()))
(O/'evidence/design-generation.json').write_text(json.dumps({'revision_id':revision,'adapter_version':ReviewDocumentation.version,'content_sha256':content_hash,'renderer_jar':str(jar),'renderer_sha256':hashlib.sha256(jar.read_bytes()).hexdigest(),'existing_generate_design_service':True,'approval_invoked':False},indent=2)+'\n')
print(json.dumps({'revision_id':revision,'state':design_status(e,c.id)['state']}));e.dispose()
