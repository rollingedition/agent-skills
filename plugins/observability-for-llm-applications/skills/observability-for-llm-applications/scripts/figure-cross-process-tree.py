"""Draw baseline day 1's message 16297 as one trace across the assistant and the contacts server, replayed with the live
server. The parent-links line rests on the printed count: two server spans have an SDK client span in the assistant as
their parent. Spans sit by depth, not time, since the server's clock is its own, so the figure shows structure only."""
from lib.dayrun import run_day_traced
from lib.figures import ACCENT, INK, MUTED, new_figure, save

traced = run_day_traced("2026-12-08", ["16297"])  # baseline day 1, with the live contacts server
# One row per span of the trace, from both processes. Span IDs link the rows and are never printed.
rows = [dict(r, process="assistant") for r in traced.spans] + [dict(r, process="contacts server") for r in traced.server]
trace_id = next(r["trace_id"] for r in rows if r["name"] == "execute_tool find_contact")
rows = [dict(r, id=r["span_id"], parent=r["parent_span_id"]) for r in rows if r["trace_id"] == trace_id]
by_id = {r["id"]: r for r in rows}
order = []  # depth-first: a span sits just below its parent, and its depth is its indent in the figure


def walk(row, depth):
    row.update(y=len(order), x=depth)
    order.append(row)
    for child in (r for r in rows if r["parent"] == row["id"]):
        walk(child, depth + 1)


for root in (r for r in rows if r["parent"] not in by_id):
    walk(root, 0)

fig, ax = new_figure(height=3.6, sharex=False)
for row in order:
    parent = by_id.get(row["parent"])
    if parent:  # an elbow from the parent's row down, then across; dashed where the link crosses the boundary
        cross = parent["process"] != row["process"]
        ax.plot([parent["x"], parent["x"], row["x"]], [parent["y"], row["y"], row["y"]], linewidth=1.2, zorder=1,
                color=ACCENT if cross else MUTED, linestyle="--" if cross else "-")
    server_row = row["process"] == "contacts server"  # squares for the server, dots for the assistant: shape, not colour alone
    ax.scatter(row["x"], row["y"], s=30, zorder=3, marker="s" if server_row else "o", color=ACCENT if server_row else INK)
    ax.text(row["x"] + 0.14, row["y"], f"{row['name']} ({row['process']})", va="center", fontsize=8, color=INK)
ax.invert_yaxis()
ax.set_xlim(-0.3, 6.4)
ax.axis("off")

cross = [r for r in rows if r["parent"] in by_id and by_id[r["parent"]]["process"] != r["process"]]
print("spans in the message's trace, assistant:", sum(r["process"] == "assistant" for r in rows))
print("spans in the message's trace, contacts server:", sum(r["process"] == "contacts server" for r in rows))
print("parent links across the boundary:", len(cross))
for r in cross:  # the SDK's client span is the parent; the server's span is the child
    print(f"{r['name']} in the contacts server, parent in the assistant:", by_id[r["parent"]]["name"])
assert sorted(r["name"] for r in cross) == ["tools/call find_contact", "tools/list"]  # the two links, and no other
save(fig, "cross-process-tree")
