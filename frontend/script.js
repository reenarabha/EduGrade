const SUBJECT = sessionStorage.getItem("edugrade_subject");
const STORE_KEY = "edugrade_students_" + SUBJECT;
const API_URL = "http://127.0.0.1:8000/predict";
const USE_FALLBACK = true;   // API band ho to rule-based estimate dikhao (screen par clearly likha hota hai)
const FIELDS = ["age","studytime","failures","absences","schoolsup","famsup","paid","activities","internet","higher","Medu","Fedu","G1","G2"];
const DEFAULTS = {age:17, studytime:2, failures:0, absences:4, schoolsup:0, famsup:0, paid:0, activities:0, internet:1, higher:1, Medu:2, Fedu:2, G1:10, G2:10};

const $ = id => document.getElementById(id);
let students = [];
try { students = JSON.parse(localStorage.getItem(STORE_KEY) || "[]"); } catch (e) { students = []; }
let editIndex = -1;

$("teacherName").textContent = sessionStorage.getItem("edugrade_auth");
$("heroSub").textContent = "Student Academic Performance & At-Risk Intervention System | " + SUBJECT;

$("logoutBtn").onclick = () => {
  sessionStorage.removeItem("edugrade_auth");
  sessionStorage.removeItem("edugrade_subject");
  location.replace("login.html");
};

function save() { localStorage.setItem(STORE_KEY, JSON.stringify(students)); }
function selectedIndex() { const v = $("studentSelect").value; return v === "" ? -1 : +v; }
function pill(type, text) { return '<span class="pill pill-' + type + '">' + text + '</span>'; }

/* ---- rule-based estimate (same rules as the "How Risk Is Decided" card) ---- */
function gradeBand(avg) {
  if (avg >= 17) return "Excellent";
  if (avg >= 14) return "Good";
  if (avg >= 10) return "Average";
  return "Low";
}
function riskLevel(s) {
  const avg = (s.G1 + s.G2) / 2;
  if (avg < 10 || s.failures >= 2) return "High";
  if (avg < 14 || s.absences > 15) return "Medium";
  return "Low";
}

/* ---- dropdown + selected student view ---- */
function render() {
  $("totalStudents").textContent = students.length;

  const sel = $("studentSelect");
  const keep = sel.value;
  sel.innerHTML = '<option value="">Select a student</option>' +
    students.map((s, i) => '<option value="' + i + '">' + s.sid + ' - ' + s.label + '</option>').join("");
  if (keep !== "" && students[+keep]) sel.value = keep;
  showSelected();
}

function setMetrics(pred) {
  $("metricGrade").textContent = pred ? pred.grade_band : "Awaiting";
  $("metricRisk").textContent = pred ? pred.risk : "Awaiting";
  document.querySelectorAll(".risk-card").forEach(c => c.classList.remove("active"));
  if (pred && $("rc-" + pred.risk)) $("rc-" + pred.risk).classList.add("active");
}

function showRecent(s) {
  if (!s) {
    $("recent").innerHTML = '<span class="muted">Select a student and click Predict.</span>';
    return;
  }
  if (!s.pred) {
    $("recent").innerHTML = '<span class="muted">No prediction yet for ' + s.sid + ' - ' + s.label + '. Click Predict.</span>';
    return;
  }
  const note = s.pred.source === "estimate"
    ? '<p class="muted note">Rule-based estimate. The ML model service is offline, so this is not a model result.</p>'
    : '<p class="muted note">Result from the ML model.</p>';
  $("recent").innerHTML =
    '<p><b>' + s.sid + ' - ' + s.label + '</b></p>' +
    '<p style="margin-top:10px">Grade band: ' + pill("grade", s.pred.grade_band) + ' &nbsp; Risk: ' + pill(String(s.pred.risk).toLowerCase(), s.pred.risk) + '</p>' +
    note +
    '<p class="muted note">Early-support signal only. Teacher review is required.</p>';
}

function showSelected() {
  const i = selectedIndex();
  if (i < 0) {
    $("chartMsg").classList.remove("hidden");
    $("perfBox").classList.add("hidden");
    setMetrics(null);
    showRecent(null);
    return;
  }
  const s = students[i];
  $("chartMsg").classList.add("hidden");
  $("perfBox").classList.remove("hidden");

  $("perfName").textContent = s.label;
  $("perfId").textContent = "Student ID: " + s.sid;

  const diff = s.G2 - s.G1;
  const t = $("perfTrend");
  if (diff > 0) { t.className = "trend trend-up"; t.textContent = "Improved by " + diff + " marks"; }
  else if (diff < 0) { t.className = "trend trend-down"; t.textContent = "Dropped by " + Math.abs(diff) + " marks"; }
  else { t.className = "trend trend-same"; t.textContent = "No change in marks"; }

  const avg = ((s.G1 + s.G2) / 2).toFixed(1);
  $("statRow").innerHTML =
    '<div class="stat"><span>Average marks</span><b>' + avg + ' / 20</b></div>' +
    '<div class="stat"><span>Absences</span><b>' + s.absences + '</b></div>' +
    '<div class="stat"><span>Past failures</span><b>' + s.failures + '</b></div>' +
    '<div class="stat"><span>Study time</span><b>' + s.studytime + ' / 4</b></div>';

  Plotly.newPlot("chart", [{
    x: ["First_Term", "Second_Term"],
    y: [s.G1, s.G2],
    type: "bar",
    text: [s.G1, s.G2],
    textposition: "outside",
    marker: { color: ["#C4B5FD", "#8B5CF6"] },
    width: [0.35, 0.35]
  }], {
    height: 300,
    paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
    font: { color: "#D4D4DC", size: 14 },
    margin: { t: 20, r: 10, b: 40, l: 40 },
    yaxis: { range: [0, 22], gridcolor: "#26262E", title: "Marks (out of 20)" },
    xaxis: { gridcolor: "#26262E" }
  }, { displayModeBar: false, responsive: true });

  setMetrics(s.pred || null);
  showRecent(s);
}

$("studentSelect").onchange = showSelected;

/* ---- form ---- */
function openForm(i) {
  editIndex = i;
  const s = i >= 0 ? students[i] : null;
  $("formTitle").textContent = s ? "Edit Student" : "Add Student";
  $("sid").value = s ? s.sid : "";
  $("label").value = s ? s.label : "";
  FIELDS.forEach(f => { $(f).value = s ? s[f] : DEFAULTS[f]; });
  $("modal").classList.remove("hidden");
}
function closeForm() { $("modal").classList.add("hidden"); }

$("addBtn").onclick = () => openForm(-1);
$("cancelBtn").onclick = closeForm;

$("editBtn").onclick = () => {
  const i = selectedIndex();
  if (i < 0) return alert("Pehle dropdown se student select karo.");
  openForm(i);
};

$("deleteBtn").onclick = () => {
  const i = selectedIndex();
  if (i < 0) return alert("Pehle dropdown se student select karo.");
  if (!confirm("Delete " + students[i].sid + " - " + students[i].label + " ?")) return;
  students.splice(i, 1);
  save();
  $("studentSelect").value = "";
  render();
};

$("studentForm").onsubmit = e => {
  e.preventDefault();
  const sid = $("sid").value.trim();
  const label = $("label").value.trim();
  if (students.some((s, i) => s.sid.toLowerCase() === sid.toLowerCase() && i !== editIndex)) {
    return alert("Ye Student ID pehle se hai.");
  }
  const data = { sid: sid, label: label, subject: SUBJECT };
  FIELDS.forEach(f => { data[f] = +$(f).value; });

  let idx;
  if (editIndex >= 0) {
    data.pred = null;          // data badal gaya, purani prediction hata do
    students[editIndex] = data;
    idx = editIndex;
  } else {
    students.push(data);
    idx = students.length - 1;
  }
  save();
  closeForm();
  render();
  $("studentSelect").value = String(idx);   // saved student ko turant select karo
  showSelected();
};

/* ---- predict ---- */
async function apiPredict(s) {
  const body = {};
  FIELDS.forEach(f => { body[f] = s[f]; });   // G3, ID aur name kabhi nahi bhejte
  const res = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!res.ok) throw new Error("API error " + res.status);
  return await res.json();
}

$("predictBtn").onclick = async () => {
  const i = selectedIndex();
  if (i < 0) return alert("Pehle dropdown se student select karo.");
  const s = students[i];
  $("recent").innerHTML = '<span class="muted">Predicting...</span>';
  try {
    const r = await apiPredict(s);
    s.pred = { grade_band: r.grade_band, risk: r.risk, source: "model" };
  } catch (err) {
    console.error(err);
    if (USE_FALLBACK) {
      s.pred = { grade_band: gradeBand((s.G1 + s.G2) / 2), risk: riskLevel(s), source: "estimate" };
    } else {
      $("recent").innerHTML = '<div class="error-box">Prediction failed: ' + err.message + '</div>';
      return;
    }
  }
  save();
  setMetrics(s.pred);
  showRecent(s);
};

render();
