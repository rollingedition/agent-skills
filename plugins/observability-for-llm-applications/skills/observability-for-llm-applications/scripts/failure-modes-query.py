"""One query per failure mode over the stored rows: baseline day 1 (real) and the incident day (injected, labelled), each
kept in its own receiver file. The baseline's real failures are wrong routes and fallback replies; its span errors and
truncated replies print zero. A receiver holds spans only, so no query here counts a parse failure."""
import tempfile

from lib import query
from lib.dayrun import run_day_traced
from lib.export import write_jsonl
from lib.report import fmt_int

folder = tempfile.mkdtemp()
baseline = run_day_traced("2026-12-08", live=False)
write_jsonl(f"{folder}/baseline.jsonl", baseline.spans)
incident = run_day_traced("2026-12-09")  # live: the contacts server's rows go to the incident day's receiver
write_jsonl(f"{folder}/incident.jsonl", incident.spans + incident.server)
base, inc = query.connect(f"{folder}/baseline.jsonl"), query.connect(f"{folder}/incident.jsonl")

# A check event sits in the event list of its route span; the route the span chose is in the span's own attributes.
WRONG = """SELECT count(*) FROM spans, UNNEST(from_json(events, '["json"]')) AS t(e)
  WHERE json_extract_string(e, '$.name') = 'ambrewick.check'
  AND json_extract_string(e, '$.attributes."ambrewick.route.correct"') = 'false'"""
FALLBACK = """SELECT count(*) FROM spans, UNNEST(from_json(events, '["json"]')) AS t(e)
  WHERE json_extract_string(e, '$.name') = 'ambrewick.check'
  AND json_extract_string(e, '$.attributes."ambrewick.route.correct"') = 'false'
  AND json_extract_string(attributes, '$."ambrewick.route"') = 'fallback'
  AND json_extract_string(e, '$.attributes."ambrewick.route.expected"') != 'fallback'"""
TRUNCATED = """SELECT count(*) FROM spans WHERE name LIKE 'chat %'
  AND json_extract_string(attributes, '$."gen_ai.response.finish_reasons"') LIKE '%length%'"""
# Each error-result attempt joined to the contacts server's tools/call span in the same trace: one pair per injected error.
PAIRED = """SELECT count(*) FROM spans AS a JOIN spans AS s ON s.trace_id = a.trace_id
  WHERE a.name LIKE 'execute_tool %' AND s.name LIKE 'tools/call %'
  AND a.status = 'ERROR' AND json_extract_string(a.attributes, '$."error.type"') = 'tool_error'
  AND s.status = 'ERROR' AND json_extract_string(s.attributes, '$."error.type"') = 'tool_error'"""
# Errors on tool attempts and on the contacts server's spans, one row per span name and error.type, with a tie-break.
ERRORS = """SELECT name, json_extract_string(attributes, '$."error.type"') AS error_type, count(*) AS n FROM spans
  WHERE status = 'ERROR' AND (name LIKE 'execute_tool %' OR name LIKE 'tools/call %')
  GROUP BY name, error_type ORDER BY n DESC, name, error_type"""
REFUSED = """SELECT count(*) FROM spans WHERE json_extract_string(attributes, '$."error.type"') = 'RateLimitError'"""

def one(connection, sql):
    return connection.execute(sql).fetchone()[0]


print("wrong routes, baseline day 1 (real):", fmt_int(one(base, WRONG)))
print("wrong routes, incident day (real):", fmt_int(one(inc, WRONG)))
print("fallback replies to a scenario that is not fallback, baseline day 1 (real):", fmt_int(one(base, FALLBACK)))
print("truncated replies, baseline day 1 (real):", fmt_int(one(base, TRUNCATED)))
print("ERROR tool-attempt and server spans, baseline day 1 (real):", fmt_int(sum(n for *_, n in base.execute(ERRORS).fetchall())))
for name, error_type, n in inc.execute(ERRORS).fetchall():
    print(f"{name}, error.type {error_type}, incident day (injected): {fmt_int(n)}")
print("error-result attempts paired with their server span, incident day (injected):", fmt_int(one(inc, PAIRED)))
print("model requests refused, incident day (injected):", fmt_int(one(inc, REFUSED)))
