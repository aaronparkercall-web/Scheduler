from __future__ import annotations

import json
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from parsing import compute_displays_from_inputs, parse_mmdd_to_datetime, parse_planner_datetime
from storage import load_data, load_planner_items, save_data, save_planner_items

HOST = "0.0.0.0"
PORT = 8000


def _json_response(handler: BaseHTTPRequestHandler, payload: dict | list, status: int = 200) -> None:
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _serialize_assignment(item: dict, idx: int) -> dict:
    return {
        "id": idx,
        "Date": item.get("Date", ""),
        "Time": item.get("Time", ""),
        "Class": item.get("Class", ""),
        "Assignment": item.get("Assignment", ""),
        "Score": item.get("Score", ""),
        "MaxPoints": item.get("MaxPoints", ""),
        "Grade": item.get("Grade", ""),
        "Complete": bool(item.get("Complete", False)),
        "Flagged": bool(item.get("Flagged", False)),
        "Note": item.get("Note", ""),
        "datetime": item["datetime"].strftime("%Y/%m/%d %H:%M"),
    }


def _serialize_planner(item: dict, idx: int) -> dict:
    return {
        "id": idx,
        "Type": item.get("Type", "Assignment"),
        "TodoDate": item.get("TodoDate", ""),
        "TodoTime": item.get("TodoTime", ""),
        "Class": item.get("Class", ""),
        "Title": item.get("Title", ""),
    }


class SchedulerHandler(BaseHTTPRequestHandler):
    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        data = self.rfile.read(length) if length else b"{}"
        return json.loads(data.decode("utf-8"))

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            body = INDEX_HTML.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if path == "/api/assignments":
            data = load_data()
            data_sorted = sorted(enumerate(data), key=lambda x: x[1]["datetime"])
            _json_response(self, [_serialize_assignment(item, idx) for idx, item in data_sorted])
            return

        if path == "/api/planner":
            planner = load_planner_items()
            _json_response(self, [_serialize_planner(item, idx) for idx, item in enumerate(planner)])
            return

        _json_response(self, {"error": "Not found"}, status=404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            payload = self._read_json()
            if path == "/api/assignments":
                data = load_data()
                dt = parse_mmdd_to_datetime(payload["Date"], payload["Time"])
                grade, score, max_points = compute_displays_from_inputs(
                    payload.get("Grade", ""),
                    payload.get("Score", ""),
                    payload.get("MaxPoints", ""),
                )
                data.append(
                    {
                        "datetime": dt,
                        "Date": payload["Date"].strip(),
                        "Time": payload["Time"].strip(),
                        "Class": payload.get("Class", "").strip(),
                        "Assignment": payload.get("Assignment", "").strip(),
                        "Score": score,
                        "MaxPoints": max_points,
                        "Grade": grade,
                        "Complete": bool(payload.get("Complete", False)),
                        "Flagged": bool(payload.get("Flagged", False)),
                        "Note": payload.get("Note", "").strip(),
                    }
                )
                save_data(data)
                _json_response(self, {"ok": True}, status=201)
                return

            if path == "/api/planner":
                planner = load_planner_items()
                todo_dt = parse_planner_datetime(payload["TodoDate"], payload["TodoTime"])
                planner.append(
                    {
                        "Type": payload.get("Type", "Event"),
                        "TodoDate": payload["TodoDate"].strip(),
                        "TodoTime": todo_dt.strftime("%I:%M %p"),
                        "TodoDateTime": todo_dt.strftime("%Y/%m/%d %H:%M"),
                        "Class": payload.get("Class", "").strip(),
                        "Title": payload.get("Title", "").strip(),
                    }
                )
                save_planner_items(planner)
                _json_response(self, {"ok": True}, status=201)
                return

            if path.endswith("/toggle") and path.startswith("/api/assignments/"):
                idx = int(path.split("/")[3])
                field = payload.get("field")
                if field not in {"Complete", "Flagged"}:
                    raise ValueError("field must be Complete or Flagged")
                data = load_data()
                data[idx][field] = not bool(data[idx].get(field, False))
                save_data(data)
                _json_response(self, {"ok": True})
                return

            _json_response(self, {"error": "Not found"}, status=404)
        except Exception as exc:
            _json_response(self, {"error": str(exc)}, status=400)

    def do_PUT(self) -> None:
        path = urlparse(self.path).path
        try:
            if not path.startswith("/api/assignments/"):
                _json_response(self, {"error": "Not found"}, status=404)
                return
            idx = int(path.split("/")[3])
            payload = self._read_json()
            data = load_data()
            dt = parse_mmdd_to_datetime(payload["Date"], payload["Time"])
            grade, score, max_points = compute_displays_from_inputs(
                payload.get("Grade", ""),
                payload.get("Score", ""),
                payload.get("MaxPoints", ""),
            )
            data[idx].update(
                {
                    "datetime": dt,
                    "Date": payload["Date"].strip(),
                    "Time": payload["Time"].strip(),
                    "Class": payload.get("Class", "").strip(),
                    "Assignment": payload.get("Assignment", "").strip(),
                    "Score": score,
                    "MaxPoints": max_points,
                    "Grade": grade,
                    "Note": payload.get("Note", "").strip(),
                }
            )
            save_data(data)
            _json_response(self, {"ok": True})
        except Exception as exc:
            _json_response(self, {"error": str(exc)}, status=400)

    def do_DELETE(self) -> None:
        path = urlparse(self.path).path
        try:
            if path.startswith("/api/assignments/"):
                idx = int(path.split("/")[3])
                data = load_data()
                data.pop(idx)
                save_data(data)
                _json_response(self, {"ok": True})
                return
            if path.startswith("/api/planner/"):
                idx = int(path.split("/")[3])
                planner = load_planner_items()
                planner.pop(idx)
                save_planner_items(planner)
                _json_response(self, {"ok": True})
                return
            _json_response(self, {"error": "Not found"}, status=404)
        except Exception as exc:
            _json_response(self, {"error": str(exc)}, status=400)


INDEX_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Scheduler</title>
  <style>
    :root {
      --bg-start:#0b1220;
      --bg-end:#1b2a4a;
      --panel:#121b2f;
      --card:#17233c;
      --row:#0f1931;
      --text:#e7ecf7;
      --muted:#9fb0d1;
      --acc:#6ea8fe;
      --input-bg:#0e1830;
      --input-border:#2d3a58;
    }
    * { box-sizing:border-box; font-family: Inter, Segoe UI, system-ui, sans-serif; }
    body { margin:0; background:linear-gradient(170deg,var(--bg-start),var(--bg-end)); color:var(--text); }
    .wrap { max-width:1200px; margin:0 auto; padding:24px; }
    .hero, .card { background:color-mix(in srgb, var(--card) 92%, transparent); border:1px solid rgba(255,255,255,.08); border-radius:24px; padding:18px; box-shadow:0 16px 40px rgba(0,0,0,.28); }
    .hero h1 { margin:0; }
    .grid { display:grid; grid-template-columns: 1fr 1fr; gap:16px; margin-top:16px; }
    input, select, button, textarea { width:100%; border-radius:14px; border:1px solid var(--input-border); background:var(--input-bg); color:var(--text); padding:10px; }
    button { background:linear-gradient(130deg,#4e8cff,#7da8ff); border:none; font-weight:600; cursor:pointer; }
    table { width:100%; border-collapse:separate; border-spacing:0 8px; }
    td,th { text-align:left; padding:10px; }
    tbody tr { background:var(--row); }
    tbody tr td:first-child { border-radius:12px 0 0 12px; }
    tbody tr td:last-child { border-radius:0 12px 12px 0; }
    .pill { display:inline-block; border-radius:999px; padding:3px 10px; font-size:12px; }
    .ok { background:#214f33; } .warn { background:#5c4a18; } .flag { background:#54295e; }
    .actions { display:flex; gap:6px; }
    .actions button { padding:8px 10px; }
    .section-title { margin-top:18px; color:var(--muted); }
    .tabs { display:flex; flex-wrap:wrap; gap:8px; margin-top:14px; }
    .tab { width:auto; padding:8px 14px; border-radius:999px; background:#0e1830; border:1px solid rgba(255,255,255,.2); }
    .tab.active { background:linear-gradient(130deg,#4e8cff,#7da8ff); color:#071226; }
    .settings-grid { display:grid; grid-template-columns:repeat(3,minmax(150px,1fr)); gap:10px; margin-top:12px; }
    .hidden { display:none; }
  </style>
</head>
<body>
<div class="wrap">
  <div class="hero">
    <h1>Scheduler — Modern Edition</h1>
    <div style="color:var(--muted)">Rounded interface, cleaner contrast, and no Tkinter.</div>
    <div class="tabs" id="tabs"></div>
  </div>

  <div class="grid" id="formsGrid">
    <div class="card">
      <h3>Add / Update Assignment</h3>
      <input id="date" placeholder="Date MM/DD" />
      <input id="time" placeholder="Time HH:MM (24h)" />
      <input id="class" placeholder="Class" />
      <input id="assignment" placeholder="Assignment" />
      <input id="score" placeholder="Score (optional)" />
      <input id="max" placeholder="Max points (optional)" />
      <input id="grade" placeholder="Grade (optional)" />
      <textarea id="note" placeholder="Note"></textarea>
      <div class="actions" style="margin-top:8px">
        <button onclick="saveAssignment()">Save</button>
        <button onclick="resetForm()">Clear</button>
      </div>
      <input type="hidden" id="edit_id" />
    </div>
    <div class="card hidden" id="plannerFormSection">
      <h3>Add Planner Item</h3>
      <select id="ptype"><option>Assignment</option><option>Event</option></select>
      <input id="ptitle" placeholder="Title" />
      <input id="pclass" placeholder="Class (optional)" />
      <input id="pdate" placeholder="TODO date MM/DD" />
      <input id="ptime" placeholder="TODO time HH:MM (24h)" />
      <button style="margin-top:8px" onclick="addPlanner()">Add Planner Item</button>
    </div>
  </div>

  <div id="assignmentsSection">
    <h3 class="section-title">Assignments</h3>
    <div class="card"><table><thead><tr><th>Due</th><th>Class</th><th>Assignment</th><th>Grade</th><th>Points</th><th>Status</th><th></th></tr></thead><tbody id="assignments"></tbody></table></div>
  </div>

  <div id="plannerSection" class="hidden">
    <h3 class="section-title">Planner</h3>
    <div class="card"><table><thead><tr><th>Type</th><th>When</th><th>Class</th><th>Title</th><th></th></tr></thead><tbody id="planner"></tbody></table></div>
  </div>

  <div id="settingsSection" class="hidden">
    <h3 class="section-title">Settings</h3>
    <div class="card">
      <div class="settings-grid">
        <label>Background Start <input id="bgStart" type="color" value="#0b1220" onchange="updateTheme()" /></label>
        <label>Background End <input id="bgEnd" type="color" value="#1b2a4a" onchange="updateTheme()" /></label>
        <label>Card Background <input id="cardBg" type="color" value="#17233c" onchange="updateTheme()" /></label>
        <label>Row Background <input id="rowBg" type="color" value="#0f1931" onchange="updateTheme()" /></label>
        <label>Primary Text <input id="textColor" type="color" value="#e7ecf7" onchange="updateTheme()" /></label>
        <label>Muted Text <input id="mutedColor" type="color" value="#9fb0d1" onchange="updateTheme()" /></label>
        <label>Accent Color <input id="accentColor" type="color" value="#6ea8fe" onchange="updateTheme()" /></label>
        <label>Input Background <input id="inputBg" type="color" value="#0e1830" onchange="updateTheme()" /></label>
        <label>Input Border <input id="inputBorder" type="color" value="#2d3a58" onchange="updateTheme()" /></label>
      </div>
    </div>
  </div>
</div>
<script>
  async function api(path, opts={}) { const res = await fetch(path, {headers:{'Content-Type':'application/json'}, ...opts}); return res.json(); }
  function val(id){return document.getElementById(id).value.trim();}

  function resetForm(){ ['date','time','class','assignment','score','max','grade','note','edit_id'].forEach(id=>document.getElementById(id).value=''); }

  async function saveAssignment(){
    const payload = {Date:val('date'), Time:val('time'), Class:val('class'), Assignment:val('assignment'), Score:val('score'), MaxPoints:val('max'), Grade:val('grade'), Note:val('note')};
    const id = val('edit_id');
    const method = id ? 'PUT' : 'POST';
    const path = id ? `/api/assignments/${id}` : '/api/assignments';
    const out = await api(path, {method, body:JSON.stringify(payload)});
    if(out.error){alert(out.error);return;}
    resetForm();
    await refresh();
  }

  async function editAssignment(id){
    const a = currentAssignments.find(x => x.id === id);
    if(!a){ return; }
    document.getElementById('date').value=a.Date; document.getElementById('time').value=a.Time; document.getElementById('class').value=a.Class;
    document.getElementById('assignment').value=a.Assignment; document.getElementById('score').value=a.Score; document.getElementById('max').value=a.MaxPoints;
    document.getElementById('grade').value=a.Grade; document.getElementById('note').value=a.Note; document.getElementById('edit_id').value=a.id;
    window.scrollTo({top:0, behavior:'smooth'});
  }

  async function toggle(id, field){ await api(`/api/assignments/${id}/toggle`, {method:'POST', body:JSON.stringify({field})}); await refresh(); }
  async function delAssignment(id){ if(confirm('Delete assignment?')){ await api(`/api/assignments/${id}`, {method:'DELETE'}); await refresh(); } }

  async function addPlanner(){
    const payload={Type:val('ptype'), Title:val('ptitle'), Class:val('pclass'), TodoDate:val('pdate'), TodoTime:val('ptime')};
    const out = await api('/api/planner',{method:'POST',body:JSON.stringify(payload)});
    if(out.error){alert(out.error);return;}
    ['ptitle','pclass','pdate','ptime'].forEach(id=>document.getElementById(id).value='');
    await refresh();
  }
  async function delPlanner(id){ await api(`/api/planner/${id}`,{method:'DELETE'}); await refresh(); }

  let currentAssignments = [];
  let activeTab = 'All';

  function applyTheme(colors){
    document.documentElement.style.setProperty('--bg-start', colors.bgStart);
    document.documentElement.style.setProperty('--bg-end', colors.bgEnd);
    document.documentElement.style.setProperty('--card', colors.cardBg);
    document.documentElement.style.setProperty('--row', colors.rowBg);
    document.documentElement.style.setProperty('--text', colors.textColor);
    document.documentElement.style.setProperty('--muted', colors.mutedColor);
    document.documentElement.style.setProperty('--acc', colors.accentColor);
    document.documentElement.style.setProperty('--input-bg', colors.inputBg);
    document.documentElement.style.setProperty('--input-border', colors.inputBorder);
    document.getElementById('bgStart').value = colors.bgStart;
    document.getElementById('bgEnd').value = colors.bgEnd;
    document.getElementById('cardBg').value = colors.cardBg;
    document.getElementById('rowBg').value = colors.rowBg;
    document.getElementById('textColor').value = colors.textColor;
    document.getElementById('mutedColor').value = colors.mutedColor;
    document.getElementById('accentColor').value = colors.accentColor;
    document.getElementById('inputBg').value = colors.inputBg;
    document.getElementById('inputBorder').value = colors.inputBorder;
  }

  function updateTheme(){
    const colors = {
      bgStart: document.getElementById('bgStart').value,
      bgEnd: document.getElementById('bgEnd').value,
      cardBg: document.getElementById('cardBg').value,
      rowBg: document.getElementById('rowBg').value,
      textColor: document.getElementById('textColor').value,
      mutedColor: document.getElementById('mutedColor').value,
      accentColor: document.getElementById('accentColor').value,
      inputBg: document.getElementById('inputBg').value,
      inputBorder: document.getElementById('inputBorder').value,
    };
    applyTheme(colors);
    localStorage.setItem('schedulerTheme', JSON.stringify(colors));
  }

  function loadTheme(){
    const stored = localStorage.getItem('schedulerTheme');
    if(!stored){ return; }
    try { applyTheme(JSON.parse(stored)); } catch(e) { console.warn('Failed to load theme', e); }
  }

  function renderTabs(assignments){
    const classes = [...new Set(assignments.map(a => a.Class).filter(Boolean))].sort();
    const tabs = ['All', 'Flagged', ...classes, 'Planner', 'Settings'];
    if(!tabs.includes(activeTab)){ activeTab = 'All'; }
    const tabsEl = document.getElementById('tabs');
    tabsEl.innerHTML = '';
    tabs.forEach(name => {
      const btn = document.createElement('button');
      btn.className = `tab ${name === activeTab ? 'active' : ''}`;
      btn.textContent = name;
      btn.onclick = () => { activeTab = name; renderTabs(currentAssignments); renderTables(); };
      tabsEl.appendChild(btn);
    });

    const onPlanner = activeTab === 'Planner';
    const onSettings = activeTab === 'Settings';
    document.getElementById('plannerFormSection').classList.toggle('hidden', !onPlanner);
    document.getElementById('plannerSection').classList.toggle('hidden', !onPlanner);
    document.getElementById('settingsSection').classList.toggle('hidden', !onSettings);
    document.getElementById('formsGrid').classList.toggle('hidden', onPlanner || onSettings);
    document.getElementById('assignmentsSection').classList.toggle('hidden', onPlanner || onSettings);
  }

  function renderTables(){
    const filteredAssignments = activeTab === 'All' || activeTab === 'Planner' || activeTab === 'Settings'
      ? currentAssignments
      : activeTab === 'Flagged'
        ? currentAssignments.filter(a => a.Flagged)
        : currentAssignments.filter(a => a.Class === activeTab);

    const tbody = document.getElementById('assignments'); tbody.innerHTML='';
    filteredAssignments.forEach(a=>{
      const statuses = [];
      if(a.Complete){ statuses.push('<span class="pill ok">Complete</span>'); }
      if(a.Flagged){ statuses.push('<span class="pill flag">Flagged</span>'); }
      if(!statuses.length){ statuses.push('<span class="pill warn">Open</span>'); }
      const status = statuses.join(' ');
      const points = a.Score && a.MaxPoints ? `${a.Score}/${a.MaxPoints}` : (a.Score || a.MaxPoints ? `${a.Score || '-'}/${a.MaxPoints || '-'}` : '-');
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${a.Date} ${a.Time}</td><td>${a.Class}</td><td>${a.Assignment}</td><td>${a.Grade || '-'}</td><td>${points}</td><td>${status}</td>
      <td class="actions"><button onclick='editAssignment(${a.id})'>Edit</button><button onclick='toggle(${a.id},"Complete")'>✓</button><button onclick='toggle(${a.id},"Flagged")'>🚩</button><button onclick='delAssignment(${a.id})'>Delete</button></td>`;
      tbody.appendChild(tr);
    });
  }

  async function refresh(){
    const assignments = await api('/api/assignments');
    currentAssignments = assignments;
    renderTabs(assignments);
    renderTables();

    const planner = await api('/api/planner');
    const pbody = document.getElementById('planner'); pbody.innerHTML='';
    planner.forEach(p=>{
      const tr = document.createElement('tr');
      tr.innerHTML=`<td>${p.Type}</td><td>${p.TodoDate} ${p.TodoTime}</td><td>${p.Class}</td><td>${p.Title}</td><td><button onclick='delPlanner(${p.id})'>Delete</button></td>`;
      pbody.appendChild(tr);
    });
  }

  loadTheme();
  refresh();
</script>
</body></html>
"""



def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), SchedulerHandler)
    print(f"Scheduler web UI running at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
