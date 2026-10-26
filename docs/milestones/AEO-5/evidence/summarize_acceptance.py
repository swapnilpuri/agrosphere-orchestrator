"""Consolidate actual JUnit, command, migration and source evidence; no database writes."""
import hashlib
import json
import shutil
import xml.etree.ElementTree as ET
from datetime import UTC,datetime
from pathlib import Path

root=Path.cwd()
base=root/"docs/milestones/AEO-5"
validation=base/"evidence/aeo5r-accepted-validation"
runner=json.loads((validation/"runner.json").read_text())
commands=json.loads((validation/"commands.json").read_text())
assert runner["exit_code"]==0
assert len(commands["commands"])==18 and all(c["exit_code"]==0 for c in commands["commands"])

def cases(path):
    xml=ET.parse(path).getroot()
    suite=xml.find("testsuite")
    ids={(c.attrib.get("classname"),c.attrib["name"]) for c in xml.iter("testcase")}
    return suite,ids
suite,current=cases(validation/"pytest.xml")
_,baseline=cases(base/"evidence/current-regression.xml")
assert not int(suite.attrib["failures"]) and not int(suite.attrib["errors"])
assert baseline<=current
migration=json.loads((base/"evidence/runtime-migration.json").read_text())
assert migration["all_existing_rows_preserved"] and all(c["exit_code"]==0 for c in migration["commands"])
fixture=Path(runner["fixture_root"])/"test_end_to_end_exact_authorit0/delivery-report.json"
shutil.copyfile(fixture,base/"evidence/mocked-end-to-end-delivery.json")
inventory=json.loads((base/"IMPLEMENTATION_INVENTORY.json").read_text())
for item in inventory["source_files"]:
    item["sha256"]=hashlib.sha256((root/item["file"]).read_bytes()).hexdigest()
inventory["generated_at"]=datetime.now(UTC).isoformat()
(base/"IMPLEMENTATION_INVENTORY.json").write_text(json.dumps(inventory,indent=2)+"\n",encoding="utf-8")
summary={"generated_at":datetime.now(UTC).isoformat(),"local_implementation_accepted":True,"formal_delivery_approved":False,"pytest":{"tests":int(suite.attrib["tests"]),"failures":int(suite.attrib["failures"]),"errors":int(suite.attrib["errors"]),"skipped":int(suite.attrib["skipped"]),"seconds":float(suite.attrib["time"]),"baseline_test_count":len(baseline),"baseline_ids_preserved":True,"new_test_count":len(current-baseline)},"validator_command_count":18,"all_validator_commands_passed":True,"schema":"0007","existing_table_count_preserved":len(migration["before"]),"source_inventory":"IMPLEMENTATION_INVENTORY.json","remote_writes_executed":False,"live_writes_tested":False,"aeo6_started":False}
(base/"evidence/acceptance-summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
print(json.dumps(summary,indent=2))
