#!/usr/bin/env python3
import hashlib, json, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = [ROOT / "kokoro-model/database/70-model.init.mysql.sql", ROOT / "database/schema/70-model.init.mysql.sql"]
NOW = "CURRENT_TIMESTAMP(3)"

def sql(value):
    if value is None: return "NULL"
    if isinstance(value, (dict, list)): value = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return "'" + str(value).replace("\\", "\\\\").replace("'", "''") + "'"

def ident(prefix, value):
    return prefix + hashlib.sha256(value.encode()).hexdigest()[:20]

with urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=30) as response:
    models = sorted(json.load(response)["data"], key=lambda item: item["id"])

lines = [
    "-- Kokoro Model V1 OpenRouter catalog snapshot.",
    "-- Source: https://openrouter.ai/api/v1/models",
    f"-- Snapshot count: {len(models)} models.",
    "-- Generated from the public OpenRouter Models API; refresh instead of inventing provider/model names.",
    "-- OpenRouter entries are catalog references and start disabled until a matching gateway route is deployed.",
    "-- No credentials or tenant policies are stored here.",
    "",
    "INSERT INTO model_provider (provider_id,provider,provider_key,display_name,secret_handle_ref,status,priority,transport_kind,health_status,metadata,deleted_at,deleted_by,delete_reason,generation,created_at,updated_at)",
    "VALUES ('prv_openrouter_catalog','openrouter','catalog','OpenRouter Model Catalog','env:OPENROUTER_API_KEY','active',100,'litellm','unknown',JSON_OBJECT('source','https://openrouter.ai/api/v1/models','description','OpenRouter standardized model catalog'),NULL,NULL,NULL,1," + NOW + "," + NOW + ")",
    "AS new ON DUPLICATE KEY UPDATE display_name=new.display_name,secret_handle_ref=new.secret_handle_ref,status=new.status,metadata=new.metadata,deleted_at=NULL,deleted_by=NULL,delete_reason=NULL,updated_at=" + NOW + ";",
    "",
    "START TRANSACTION;",
    "",
    "INSERT INTO model_definition (model_id,model_key,display_name,status,generation,metadata,deleted_at,deleted_by,delete_reason,created_at,updated_at) VALUES",
]
defs=[]; revs=[]; labels=[]
for m in models:
    mid=ident("mdl_or_",m["id"]); rid=ident("rev_or_",m["id"]); lid=ident("lbl_or_",m["id"])
    a=m.get("architecture") or {}; ins=a.get("input_modalities") or ["text"]; outs=a.get("output_modalities") or ["text"]
    feature="image" if "image" in outs and "text" not in outs else ("audio" if "audio" in outs and "text" not in outs else "chat")
    name=m.get("name") or m["id"]
    meta={k:m.get(k) for k in ("id","canonical_slug","description","context_length","architecture","pricing","supported_parameters","created","top_provider","per_request_limits","default_parameters") if m.get(k) is not None}
    defs.append("(" + ",".join([sql(mid),sql(m["id"]),sql(name),"'active'","1",sql(meta),"NULL","NULL","NULL",NOW,NOW]) + ")")
    rmeta={"source":"openrouter","canonical_slug":m.get("canonical_slug"),"description":m.get("description"),"pricing":m.get("pricing"),"supported_parameters":m.get("supported_parameters")}
    revs.append("(" + ",".join([sql(rid),sql(mid),"1","'prv_openrouter_catalog'","'openrouter'",sql(m["id"]),sql(name),sql(feature),sql([m["id"]]),sql(ins),sql(outs),"'litellm'",sql(m["id"]),sql(m.get("context_length")),"100","'disabled'","NULL","NULL",sql(rmeta),"NULL","NULL","NULL",NOW,NOW]) + ")")
    labels.append("(" + ",".join([sql(lid),sql(m["id"]),sql(name),sql(m.get("description") or name),sql(feature),"'openrouter'",sql(rid),"'disabled'","NULL","NULL","NULL",NOW,NOW]) + ")")
lines.append(",\n".join(defs) + " AS new ON DUPLICATE KEY UPDATE display_name=new.display_name,status=new.status,metadata=new.metadata,deleted_at=NULL,deleted_by=NULL,delete_reason=NULL,updated_at=" + NOW + ";")
lines += ["", "INSERT INTO model_revision (model_revision_id,model_id,revision,provider_id,provider,provider_model_name,revision_display_name,feature_key,label_keys,input_modalities,output_modalities,transport,gateway_model_name,context_window,priority,revision_status,published_at,retired_at,metadata,deleted_at,deleted_by,delete_reason,created_at,updated_at) VALUES"]
lines.append(",\n".join(revs) + " AS new ON DUPLICATE KEY UPDATE model_id=new.model_id,revision_display_name=new.revision_display_name,label_keys=new.label_keys,input_modalities=new.input_modalities,output_modalities=new.output_modalities,gateway_model_name=new.gateway_model_name,context_window=new.context_window,metadata=new.metadata,updated_at=" + NOW + ";")
lines += ["", "INSERT INTO model_label (label_id,label_key,display_name,description,feature_key,tier,default_revision_id,status,deleted_at,deleted_by,delete_reason,created_at,updated_at) VALUES"]
lines.append(",\n".join(labels) + " AS new ON DUPLICATE KEY UPDATE display_name=new.display_name,description=new.description,feature_key=new.feature_key,tier=new.tier,default_revision_id=new.default_revision_id,status=new.status,updated_at=" + NOW + ";")
local_sql = """
-- Kokoro local facade entries (not OpenRouter IDs).
INSERT INTO model_definition (model_id,model_key,display_name,status,generation,metadata,deleted_at,deleted_by,delete_reason,created_at,updated_at)
VALUES ('mdl_claude_code','claude-code','Claude Code','active',1,JSON_OBJECT('description','Kokoro stable facade; backend selected by LiteLLM'),NULL,NULL,NULL,CURRENT_TIMESTAMP(3),CURRENT_TIMESTAMP(3)),
       ('mdl_kokoro_dev_mock','kokoro-dev-mock','Kokoro Dev Mock','active',1,JSON_OBJECT('description','Development-only fixed response model'),NULL,NULL,NULL,CURRENT_TIMESTAMP(3),CURRENT_TIMESTAMP(3))
AS new ON DUPLICATE KEY UPDATE display_name=new.display_name,status=new.status,metadata=new.metadata,updated_at=CURRENT_TIMESTAMP(3);

INSERT INTO model_provider (provider_id,provider,provider_key,display_name,secret_handle_ref,status,priority,transport_kind,health_status,metadata,deleted_at,deleted_by,delete_reason,generation,created_at,updated_at)
VALUES ('prv_litellm_gateway','litellm','gateway','Kokoro LiteLLM Gateway','env:LITELLM_MASTER_KEY','active',100,'litellm','unknown',JSON_OBJECT('description','Kokoro stable LiteLLM facade'),NULL,NULL,NULL,1,CURRENT_TIMESTAMP(3),CURRENT_TIMESTAMP(3))
AS new ON DUPLICATE KEY UPDATE display_name=new.display_name,secret_handle_ref=new.secret_handle_ref,status=new.status,metadata=new.metadata,updated_at=CURRENT_TIMESTAMP(3);

INSERT INTO model_revision (model_revision_id,model_id,revision,provider_id,provider,provider_model_name,revision_display_name,feature_key,label_keys,input_modalities,output_modalities,transport,gateway_model_name,context_window,priority,revision_status,published_at,retired_at,metadata,deleted_at,deleted_by,delete_reason,created_at,updated_at)
VALUES ('rev_claude_code_v1','mdl_claude_code',1,'prv_litellm_gateway','litellm','claude-code','Claude Code（LiteLLM 门面）','chat',JSON_ARRAY('claude-code'),JSON_ARRAY('text'),JSON_ARRAY('text'),'litellm','claude-code',NULL,100,'active',CURRENT_TIMESTAMP(3),NULL,JSON_OBJECT('description','Kokoro default facade; actual backend is LiteLLM configuration'),NULL,NULL,NULL,CURRENT_TIMESTAMP(3),CURRENT_TIMESTAMP(3)),
       ('rev_kokoro_dev_mock_v1','mdl_kokoro_dev_mock',1,'prv_litellm_gateway','litellm','kokoro-dev-mock','Kokoro Dev Mock（本地链路）','chat',JSON_ARRAY('kokoro-dev-mock'),JSON_ARRAY('text'),JSON_ARRAY('text'),'litellm','kokoro-dev-mock',NULL,900,'disabled',NULL,NULL,JSON_OBJECT('description','Development-only fixed response route'),NULL,NULL,NULL,CURRENT_TIMESTAMP(3),CURRENT_TIMESTAMP(3))
AS new ON DUPLICATE KEY UPDATE model_id=new.model_id,revision_display_name=new.revision_display_name,gateway_model_name=new.gateway_model_name,revision_status=new.revision_status,updated_at=CURRENT_TIMESTAMP(3);

INSERT INTO model_label (label_id,label_key,display_name,description,feature_key,tier,default_revision_id,status,deleted_at,deleted_by,delete_reason,created_at,updated_at)
VALUES ('lbl_claude_code','claude-code','Kokoro 默认','平台内置默认模型（claude-code 门面 → LiteLLM）','chat','standard','rev_claude_code_v1','active',NULL,NULL,NULL,CURRENT_TIMESTAMP(3),CURRENT_TIMESTAMP(3)),
       ('lbl_kokoro_dev_mock','kokoro-dev-mock','Kokoro Dev Mock','本地开发链路固定响应模型，不用于生产','chat','dev','rev_kokoro_dev_mock_v1','disabled',NULL,NULL,NULL,CURRENT_TIMESTAMP(3),CURRENT_TIMESTAMP(3))
AS new ON DUPLICATE KEY UPDATE display_name=new.display_name,description=new.description,default_revision_id=new.default_revision_id,status=new.status,updated_at=CURRENT_TIMESTAMP(3);
"""
text="\n".join(lines) + "\n" + local_sql + "\nCOMMIT;\n"
for path in OUTPUTS: path.write_text(text)
print(f"generated {len(models)} models")
