const API_BASE = String(window.API_BASE || "http://localhost:8000").replace(/\/+$/, "");
const SESSION_ID = 'kiet_session_' + Date.now();
const BRANCH = "CSE/CS";

let currentView = "chat";
let isLoading = false;
let chatHistory = [];
let jsonData = {
  examSchedule: null,
  holidays: [],
  subjects3: [],
  subjects4: [],
};

function expandSemester4ProfessionalElectives(subjects) {
  const list = Array.isArray(subjects) ? subjects : [];
  const hasGenericPE = list.some(
    (subject) => String(subject?.code || "").toUpperCase() === "PE-I"
  );
  if (!hasGenericPE) {
    return list;
  }

  const namedProfessionalElectives = [
    { code: "CS318E", name: "Frontend Engineering with React & Next" },
    { code: "CS307E", name: "Intelligent Systems with Text & Vision API" },
    { code: "CS304E", name: "DevOps Foundations & Version Control" },
    { code: "CS321E", name: "Foundation of iOS App Development" },
  ].map((subject) => ({
    ...subject,
    credits: 4,
    total_marks: 200,
    type: "Blended",
    category: "Professional Elective",
  }));

  const withoutGeneric = list.filter(
    (subject) => String(subject?.code || "").toUpperCase() !== "PE-I"
  );
  return [...withoutGeneric, ...namedProfessionalElectives];
}

const el = {
  connectionDot: document.getElementById("connectionDot"),
  connectionText: document.getElementById("connectionText"),
  chatContainer: document.getElementById("chatContainer"),
  chatInput: document.getElementById("chatInput"),
  sendBtn: document.getElementById("sendBtn"),
  typingIndicator: document.getElementById("typingIndicator"),
  suggestionGrid: document.getElementById("suggestionGrid"),
  examCards: document.getElementById("examCards"),
  timelineTrack: document.getElementById("timelineTrack"),
  holidayGrid: document.getElementById("holidayGrid"),
  holidayCount: document.getElementById("holidayCount"),
  holidaySearch: document.getElementById("holidaySearch"),
  monthFilters: document.getElementById("monthFilters"),
  subjectGrid: document.getElementById("subjectGrid"),
  sem3Btn: document.getElementById("sem3Btn"),
  sem4Btn: document.getElementById("sem4Btn"),
  attendanceTotal: document.getElementById("attendanceTotal"),
  attendanceAttended: document.getElementById("attendanceAttended"),
  attendanceCalcBtn: document.getElementById("attendanceCalcBtn"),
  attendanceResetBtn: document.getElementById("attendanceResetBtn"),
  attendanceTips: document.getElementById("attendanceTips"),
  attendanceFillButtons: document.getElementById("attendanceFillButtons"),
  attendanceResult: document.getElementById("attendanceResult"),
  addSubjectBtn: document.getElementById("addSubjectBtn"),
  autofillSem3Btn: document.getElementById("autofillSem3Btn"),
  autofillSem4Btn: document.getElementById("autofillSem4Btn"),
  cgpaRows: document.getElementById("cgpaRows"),
  cgpaCalcBtn: document.getElementById("cgpaCalcBtn"),
  cgpaResult: document.getElementById("cgpaResult"),
  sidebar: document.getElementById("sidebar"),
  sidebarOverlay: document.getElementById("sidebarOverlay"),
  hamburgerBtn: document.getElementById("hamburgerBtn"),
  modalOverlay: document.getElementById("subjectModalOverlay"),
  modalTitle: document.getElementById("modalTitle"),
  modalBody: document.getElementById("modalBody"),
  closeModalBtn: document.getElementById("closeModalBtn"),
};

function formatText(text) {
  return (text || "").replace(/\n/g, "<br />");
}

function formatBotResponse(text) {
  if (!text) return "";

  let formatted = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  formatted = formatted.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  formatted = formatted.replace(/\*(.*?)\*/g, "<em>$1</em>");

  formatted = formatted.replace(/((\d+\.\s+.+\n?)+)/g, function(match) {
    const items = match.trim().split("\n").filter((line) => line.trim());
    const listItems = items.map(function(item) {
      return "<li>" + item.replace(/^\d+\.\s+/, "") + "</li>";
    }).join("");
    return "<ol>" + listItems + "</ol>";
  });

  formatted = formatted.replace(/((\-\s+.+\n?)+)/g, function(match) {
    const items = match.trim().split("\n").filter((line) => line.trim());
    const listItems = items.map(function(item) {
      return "<li>" + item.replace(/^[\-\*]\s+/, "") + "</li>";
    }).join("");
    return "<ul>" + listItems + "</ul>";
  });

  formatted = formatted.replace(
    /^(Hours|Credits|Total Hours|Semester|Course Code|Type):\s*(.+)$/gm,
    '<span class="response-label">$1:</span> <span class="response-value">$2</span><br>'
  );

  formatted = formatted.replace(/\n\n/g, '</p><p class="response-para">');
  formatted = formatted.replace(/\n/g, "<br>");
  formatted = '<p class="response-para">' + formatted + "</p>";
  formatted = formatted.replace(/<p class="response-para"><\/p>/g, "");

  return formatted;
}

function createBotMessageHTML(responseData) {
  const text = responseData?.response || responseData?.answer || responseData || "";

  const formattedText = formatBotResponse(text);

  return '<div class="bot-response-card">'
    + '<div class="response-body message-text">' + formattedText + "</div>"
    + "</div>";
}

function sourceTag(type, sources = []) {
  if (type === "json_lookup") {
    return { label: "📁 JSON Data", file: sources[0] || "Structured JSON" };
  }
  if (type === "rag") {
    const source = sources[0] || "PDF Documents";
    if (String(source).toLowerCase().includes("pdf")) {
      return { label: "📄 PDF", file: source };
    }
    return { label: "🤖 AI Answer", file: source };
  }
  if (type === "calculator") {
    return { label: "🧮 Calculator", file: "Mathematical calculation" };
  }
  return { label: "🤖 AI Answer", file: sources[0] || "Not specified" };
}

async function apiGet(path) {
  const response = await fetch(`${API_BASE}${path}`);
  let data = {};
  try {
    data = await response.json();
  } catch {
    data = {};
  }
  if (!response.ok) {
    throw new Error(data.detail || `Request failed: ${response.status}`);
  }
  return data;
}

async function apiPost(path, payload) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  let data = {};
  try {
    data = await response.json();
  } catch {
    data = {};
  }
  if (!response.ok) {
    throw new Error(data.detail || `Request failed: ${response.status}`);
  }
  return data;
}

function setConnectionStatus(ok, text = "Connected") {
  el.connectionDot.classList.toggle("online", ok);
  el.connectionDot.classList.toggle("offline", !ok);
  el.connectionText.textContent = text;
}

function renderMessage(text, meta = {}, isBot = true) {
  const wrap = document.createElement("div");
  wrap.className = `message ${isBot ? "message-bot bot-message" : "message-user"}`;
  if (isBot) {
    wrap.innerHTML = createBotMessageHTML({
      answer: text,
      type: meta.type,
      sources: meta.sources || [],
    });
  } else {
    wrap.innerHTML = formatText(text);
  }

  el.chatContainer.appendChild(wrap);
  el.chatContainer.scrollTop = el.chatContainer.scrollHeight;
}

function showTyping(show) {
  el.typingIndicator.classList.toggle("hidden", !show);
}

// Show three bouncing dots while waiting for API response
function showTypingIndicator() {
  const chatMessages = document.getElementById("chat-messages") || document.querySelector(".chat-messages") || el.chatContainer;
  if (!chatMessages) {
    return;
  }
  const typingDiv = document.createElement("div");
  typingDiv.id = "typing-indicator";
  typingDiv.className = "message bot-message";
  typingDiv.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
  chatMessages.appendChild(typingDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Remove the bouncing dots
function removeTypingIndicator() {
  const indicator = document.getElementById("typing-indicator");
  if (indicator) indicator.remove();
}

async function sendMessage(query) {
  const clean = (query || "").trim();
  if (!clean || isLoading) {
    return;
  }

  isLoading = true;
  renderMessage(clean, {}, false);
  el.chatInput.value = "";
  el.sendBtn.disabled = true;
  el.sendBtn.textContent = "Sending...";
  showTypingIndicator();

  try {
    const data = await apiPost("/chat", {
      query: query,
      session_id: SESSION_ID
    });

    removeTypingIndicator();
    const botWrap = document.createElement("div");
    botWrap.className = "message message-bot bot-message";
    botWrap.innerHTML = createBotMessageHTML(data);

    el.chatContainer.appendChild(botWrap);
    el.chatContainer.scrollTop = el.chatContainer.scrollHeight;
    el.sendBtn.disabled = false;
    el.sendBtn.textContent = "Send";

    chatHistory.push({ query: clean, answer: data.answer, type: data.type, timestamp: data.timestamp });
  } catch (error) {
    removeTypingIndicator();
    renderMessage(
      `Sorry, I couldn't reach the backend service. Please ensure FastAPI is running on ${API_BASE}.\nError: ${error.message}`,
      { type: "not_found", sources: [] },
      true
    );
    el.sendBtn.disabled = false;
    el.sendBtn.textContent = "Send";
  } finally {
    isLoading = false;
  }
}

function renderExamCards(data) {
  const exams = [
    {
      key: "MSE1",
      title: "Mid Semester Exam 1",
      lines: [
        (d) => `📅 Dates: ${d.exam_dates || "NA"}`,
        (d) => `📋 Detention list: ${d.detention_list_by_COE || "NA"}`,
        (d) => `✅ Result upload by: ${d.marks_upload_ERP_deadline || "NA"}`,
        (d) => `🔔 Grievance: Till ${d.grievance_redressal_deadline || "NA"}`,
      ],
    },
    {
      key: "MSE2",
      title: "Mid Semester Exam 2",
      lines: [
        (d) => `📅 Dates: ${d.exam_dates || "NA"}`,
        (d) => `📋 Detention list: ${d.detention_list_by_COE || "NA"}`,
        (d) => `✅ Result upload by: ${d.marks_upload_ERP_deadline || "NA"}`,
      ],
    },
    {
      key: "ESE",
      title: "End Semester Exam",
      lines: [
        (d) => `📅 Dates: ${d.exam_dates || "NA"}`,
        (d) => `🔬 Practicals: ${d.practical_exam || "NA"}`,
        (d) => `📊 Results: ${d.result_publication || "NA"}`,
        (d) => `⚠️ Make-up Exam: ${d.makeup_exam || "NA"}`,
      ],
    },
  ];

  el.examCards.innerHTML = "";
  exams.forEach((exam) => {
    const details = data[exam.key] || {};
    const card = document.createElement("div");
    card.className = "exam-card";
    const lines = exam.lines.map((fn) => `<p>${fn(details)}</p>`).join("");
    card.innerHTML = `<h3>${exam.title}</h3>${lines}`;
    el.examCards.appendChild(card);
  });

  const timeline = [
    { date: "Jan 22", event: "Classes Start" },
    { date: "Mar 9", event: "MSE1" },
    { date: "Apr 20", event: "MSE2" },
    { date: "May 15", event: "ESE" },
    { date: "Jun 23", event: "Results" },
  ];

  el.timelineTrack.innerHTML = "";
  timeline.forEach((node) => {
    const div = document.createElement("div");
    div.className = "timeline-node";
    div.innerHTML = `<strong>${node.date}</strong><br />${node.event}`;
    el.timelineTrack.appendChild(div);
  });
}

function renderHolidayCards(data, filter = null) {
  const holidays = Array.isArray(data) ? data : [];

  let filtered = holidays;
  if (filter && filter !== "all") {
    filtered = filtered.filter((item) => {
      const date = String(item.date || "").toLowerCase();
      return date.includes(filter.toLowerCase());
    });
  }

  const searchText = (el.holidaySearch.value || "").trim().toLowerCase();
  if (searchText) {
    filtered = filtered.filter((item) => {
      const hay = `${item.date} ${item.day} ${item.reason}`.toLowerCase();
      return hay.includes(searchText);
    });
  }

  el.holidayGrid.innerHTML = "";
  filtered.forEach((item) => {
    const card = document.createElement("div");
    const reason = String(item.reason || "").toLowerCase();
    const isWeekend = reason.includes("saturday") || reason.includes("sunday");
    card.className = `holiday-card ${isWeekend ? "weekend" : "gazette"}`;
    card.innerHTML = `
      <h4>📅 ${item.date || "NA"}</h4>
      <p><strong>Day:</strong> ${item.day || "NA"}</p>
      <p><strong>Holiday:</strong> ${item.reason || "NA"}</p>
    `;
    el.holidayGrid.appendChild(card);
  });

  el.holidayCount.textContent = `Total ${filtered.length} holidays in Even Semester 2025-26`;
}

function badgeClass(type) {
  const t = String(type || "").toLowerCase();
  if (t.includes("practical") || t.includes("lab")) {
    return "badge-practical";
  }
  if (t.includes("blended")) {
    return "badge-blended";
  }
  return "badge-theory";
}

function renderSubjectCards(data, semester) {
  el.subjectGrid.innerHTML = "";
  data.forEach((subject) => {
    const card = document.createElement("div");
    card.className = "subject-card";
    card.innerHTML = `
      <span class="grade-badge ${badgeClass(subject.type)}">${subject.type || "Theory"}</span>
      <h3>${subject.code || "NA"}</h3>
      <p>${subject.name || "Unnamed Subject"}</p>
      <p>
        <span class="grade-badge badge-theory">Credits: ${subject.credits ?? "NA"}</span>
        <span class="grade-badge badge-practical">Marks: ${subject.total_marks ?? "NA"}</span>
      </p>
      <button class="send-btn view-syllabus-btn" data-code="${subject.code}">View Syllabus →</button>
    `;
    el.subjectGrid.appendChild(card);
  });

  document.querySelectorAll(".view-syllabus-btn").forEach((btn) => {
    btn.addEventListener("click", () => openSubjectModal(btn.dataset.code));
  });

  el.sem3Btn.classList.toggle("active", semester === 3);
  el.sem4Btn.classList.toggle("active", semester === 4);
}

function marksRow(marks) {
  const keys = ["MSE1", "MSE2", "total_MSE", "CA1", "CA2", "CA3_ATT", "total_CA", "ESE", "total"];
  return keys
    .filter((key) => Object.prototype.hasOwnProperty.call(marks, key))
    .map((key) => `<tr><td>${key}</td><td>${marks[key]}</td></tr>`)
    .join("");
}

async function openSubjectModal(courseCode) {
  try {
    const data = await apiGet(`/syllabus/${encodeURIComponent(courseCode)}`);
    el.modalTitle.textContent = `${data.course_name} (${data.course_code})`;

    const unitsHtml = (data.units || [])
      .map(
        (unit) => `
        <details class="unit-accordion">
          <summary>Unit ${unit.unit_no}: ${unit.title}</summary>
          <div class="unit-content">
            <p><strong>Hours:</strong> ${unit.hours || "NA"}</p>
            <ul>${(unit.topics || []).map((topic) => `<li>${topic}</li>`).join("")}</ul>
          </div>
        </details>
      `
      )
      .join("");

    const books = (data.textbooks || []).map((book) => `<li>${book}</li>`).join("");
    const refs = (data.reference_books || []).map((book) => `<li>${book}</li>`).join("");

    el.modalBody.innerHTML = `
      <div class="card">
        <p><strong>Credits:</strong> ${data.credits || "NA"}</p>
        <p><strong>Total Lecture Hours:</strong> ${data.total_lecture_hours || "NA"}</p>
      </div>
      <h4>Units</h4>
      ${unitsHtml || "<p>No unit data available.</p>"}

      <h4>Marks Breakdown</h4>
      <table class="card" style="width:100%; border-collapse: collapse;">
        <tbody>${marksRow(data.marks || {}) || "<tr><td>No marks data</td><td>-</td></tr>"}</tbody>
      </table>

      <h4>Textbooks</h4>
      <ul>${books || "<li>No textbook information available.</li>"}</ul>

      <h4>Reference Books</h4>
      <ul>${refs || "<li>No reference books information available.</li>"}</ul>
    `;

    el.modalOverlay.classList.remove("hidden");
  } catch (error) {
    renderMessage(`Could not load syllabus for ${courseCode}: ${error.message}`, { type: "not_found", sources: [] }, true);
  }
}

function attendanceColor(percentage) {
  if (percentage >= 75) return "var(--success)";
  if (percentage >= 70) return "var(--warning)";
  return "var(--danger)";
}

function updateAttendanceHint() {
  if (!el.attendanceTips) return;

  const total = Number(el.attendanceTotal.value);
  const attended = Number(el.attendanceAttended.value);

  if (!Number.isFinite(total) || total <= 0 || !Number.isFinite(attended) || attended < 0) {
    el.attendanceTips.textContent = "Enter values to see your status and next action plan.";
    return;
  }

  if (attended > total) {
    el.attendanceTips.textContent = "Attended classes cannot be more than total classes.";
    return;
  }

  const current = (attended / total) * 100;
  if (current >= 75) {
    el.attendanceTips.textContent = `Great! Current attendance is ${current.toFixed(2)}%. You are in safe zone.`;
  } else if (current >= 70) {
    el.attendanceTips.textContent = `Current attendance is ${current.toFixed(2)}%. You are close, avoid missing classes.`;
  } else {
    el.attendanceTips.textContent = `Current attendance is ${current.toFixed(2)}%. You need recovery classes to reach 75%.`;
  }
}

function resetAttendanceForm() {
  el.attendanceTotal.value = "";
  el.attendanceAttended.value = "";
  el.attendanceResult.classList.add("hidden");
  updateAttendanceHint();
}

async function calculateAttendance() {
  const total = Number(el.attendanceTotal.value);
  const attended = Number(el.attendanceAttended.value);

  if (!Number.isFinite(total) || !Number.isFinite(attended) || total <= 0 || attended < 0 || attended > total) {
    renderMessage("Please enter valid attendance values: total > 0 and attended <= total.", { type: "calculator", sources: [] }, true);
    return;
  }

  try {
    const result = await apiPost("/calculate/attendance", {
      total_classes: total,
      attended_classes: attended,
    });

    const pct = Number(result.current_percentage || 0);
    const statusClass = pct >= 75 ? "status-safe" : pct >= 70 ? "status-risk" : "status-danger";
    const statusText = pct >= 75 ? "🟢 SAFE - You can appear in ESE" : pct >= 70 ? "🟡 AT RISK - Very close to limit" : "🔴 DETAINED - Below 75% threshold";
    const fillWidth = Math.max(0, Math.min(100, pct));

    el.attendanceResult.classList.remove("hidden");
    el.attendanceResult.innerHTML = `
      <div class="attendance-circle" style="background:${attendanceColor(pct)}">${pct.toFixed(2)}%</div>
      <div class="attendance-summary"><strong>${attended}</strong> attended out of <strong>${total}</strong> classes</div>
      <div class="attendance-meter">
        <div class="attendance-meter-fill" style="width:${fillWidth}%; background:${attendanceColor(pct)}"></div>
      </div>
      <div class="status-banner ${statusClass}">${statusText}</div>
      <div class="stats-grid">
        <div><strong>Classes to attend to reach 75%:</strong><br />${result.classes_needed_to_reach_75}</div>
        <div><strong>Classes you can still skip:</strong><br />${result.classes_can_skip}</div>
        <div><strong>Current streak needed:</strong><br />Attend next ${result.classes_needed_to_reach_75} classes</div>
      </div>
      <p><strong>Motivation:</strong> ${result.status_message}</p>
    `;
  } catch (error) {
    renderMessage(`Attendance calculation failed: ${error.message}`, { type: "calculator", sources: [] }, true);
  }
}

const KIET_GRADES = [
  { value: "A+", label: "A+ (10 points)", points: 10 },
  { value: "A", label: "A  (9 points)", points: 9 },
  { value: "B+", label: "B+ (8 points)", points: 8 },
  { value: "B", label: "B  (7 points)", points: 7 },
  { value: "C+", label: "C+ (6 points)", points: 6 },
  { value: "C", label: "C  (5 points)", points: 5 },
  { value: "D", label: "D  (4 points)", points: 4 },
  { value: "FF", label: "FF (Fail - 0)", points: 0 },
  { value: "NC", label: "NC (Non Credit)", points: null },
  { value: "AU", label: "AU (Audit)", points: null }
];

function calculateCGPAFrontend(subjects) {
  let totalEGP = 0;
  let totalCredits = 0;

  subjects.forEach(function(sub) {
    const gradeObj = KIET_GRADES.find(function(g) { return g.value === sub.grade; });
    if (!gradeObj || gradeObj.points === null) return;

    totalEGP += sub.credits * gradeObj.points;
    totalCredits += sub.credits;
  });

  if (totalCredits === 0) return { sgpa: 0, percentage: 0 };

  const sgpa = (totalEGP / totalCredits).toFixed(2);
  const percentage = (parseFloat(sgpa) * 10).toFixed(2);

  return { sgpa: sgpa, percentage: percentage, totalEGP: totalEGP, totalCredits: totalCredits };
}

function addCgpaRow(subject = { name: "", credits: 3, grade: "A" }) {
  const gradeOptions = KIET_GRADES
    .map((grade) => `<option value="${grade.value}" ${subject.grade === grade.value ? "selected" : ""}>${grade.label}</option>`)
    .join("");

  const row = document.createElement("div");
  row.className = "cgpa-row";
  row.innerHTML = `
    <input class="cgpa-name" type="text" placeholder="Subject Name" value="${subject.name}" />
    <select class="cgpa-grade">
      ${gradeOptions}
    </select>
    <input class="cgpa-credits" type="number" min="1" max="4" step="1" value="${subject.credits}" />
    <button class="icon-btn cgpa-remove">×</button>
  `;

  row.querySelector(".cgpa-remove").addEventListener("click", () => row.remove());
  el.cgpaRows.appendChild(row);
}

async function calculateCGPA() {
  const rows = [...document.querySelectorAll(".cgpa-row")];
  if (rows.length === 0) {
    renderMessage("Please add at least one subject for CGPA calculation.", { type: "calculator", sources: [] }, true);
    return;
  }

  const subjects = [];
  for (const row of rows) {
    const name = row.querySelector(".cgpa-name").value.trim();
    const grade = row.querySelector(".cgpa-grade").value;
    const credits = Number(row.querySelector(".cgpa-credits").value);

    if (!name || !Number.isFinite(credits) || credits <= 0) {
      renderMessage("Fill all CGPA subject fields correctly before calculating.", { type: "calculator", sources: [] }, true);
      return;
    }

    subjects.push({ name, grade, credits });
  }

  try {
    const result = calculateCGPAFrontend(subjects);

    el.cgpaResult.classList.remove("hidden");
    el.cgpaResult.innerHTML = `
      <h3 style="margin: 0 0 8px;">SGPA: ${result.sgpa}</h3>
      <p><strong>Equivalent Percentage:</strong> ${result.percentage}%</p>
      <p><strong>Formula:</strong> EGP / Credits = SGPA | CGPA x 10 = Percentage</p>
      <p><strong>EGP:</strong> ${result.totalEGP || 0} | <strong>Total Credits:</strong> ${result.totalCredits || 0}</p>
    `;
  } catch (error) {
    renderMessage(`CGPA calculation failed: ${error.message}`, { type: "calculator", sources: [] }, true);
  }
}

function autoFillCGPA(semester) {
  const data = semester === 3 ? jsonData.subjects3 : jsonData.subjects4;
  el.cgpaRows.innerHTML = "";
  data.forEach((subject) => {
    if (String(subject.code).toUpperCase().endsWith("P")) {
      return;
    }
    const credits = Number(subject.credits);
    if (!Number.isFinite(credits) || credits <= 0) {
      return;
    }
    addCgpaRow({ name: subject.name, credits, grade: "A" });
  });
}

function switchView(viewName) {
  currentView = viewName;
  document.querySelectorAll(".view").forEach((view) => {
    view.classList.toggle("active", view.id === `view-${viewName}`);
  });

  document.querySelectorAll(".sidebar-item").forEach((item) => {
    item.classList.toggle("active", item.dataset.view === viewName);
  });

  document.querySelectorAll(".mobile-nav-item").forEach((item) => {
    item.classList.toggle("active", item.dataset.view === viewName);
  });

  if (window.innerWidth < 768) {
    el.sidebar.classList.remove("open");
    el.sidebarOverlay.classList.remove("show");
  }
}

function toggleSidebar() {
  el.sidebar.classList.toggle("open");
  el.sidebarOverlay.classList.toggle("show");
}

function filterHolidays(month) {
  document.querySelectorAll(".month-filter-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.month === month);
  });
  renderHolidayCards(jsonData.holidays, month === "all" ? null : month);
}

function handleSuggestionClick(text) {
  el.chatInput.value = text;
  sendMessage(text);
}

async function init() {
  try {
    const health = await apiGet("/health");
    setConnectionStatus(true, health.vector_store_loaded ? "Connected" : "Connected (Index loading pending)");

    const exam = await apiGet("/calendar/exam-schedule");
    const holidaysRes = await apiGet("/calendar/holidays");
    const sem3 = await apiGet("/subjects/3");
    const sem4 = await apiGet("/subjects/4");

    jsonData.examSchedule = exam;
    jsonData.holidays = holidaysRes.holidays || [];
    jsonData.subjects3 = sem3.subjects || [];
    jsonData.subjects4 = expandSemester4ProfessionalElectives(sem4.subjects || []);

    renderExamCards(jsonData.examSchedule);
    renderHolidayCards(jsonData.holidays);
    renderSubjectCards(jsonData.subjects3, 3);

    if (el.cgpaRows.children.length === 0) {
      addCgpaRow();
    }
  } catch (error) {
    setConnectionStatus(false, "Offline");
    renderMessage(
      `Backend not reachable at ${API_BASE}. Start FastAPI server and refresh.\nError: ${error.message}`,
      { type: "not_found", sources: [] },
      true
    );
  }
}

window.addEventListener("DOMContentLoaded", () => {
  init();

  if (el.sendBtn) {
    el.sendBtn.disabled = true;
  }

  el.chatInput.addEventListener("input", () => {
    if (isLoading) {
      el.sendBtn.disabled = true;
      return;
    }
    el.sendBtn.disabled = !el.chatInput.value.trim();
  });

  el.sendBtn.addEventListener("click", () => sendMessage(el.chatInput.value));
  el.chatInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") sendMessage(el.chatInput.value);
  });

  el.suggestionGrid.addEventListener("click", (event) => {
    const chip = event.target.closest(".suggestion-chip");
    if (chip) handleSuggestionClick(chip.textContent.trim());
  });

  document.querySelectorAll(".sidebar-item").forEach((item) => {
    item.addEventListener("click", () => switchView(item.dataset.view));
  });

  document.querySelectorAll(".mobile-nav-item").forEach((item) => {
    item.addEventListener("click", () => switchView(item.dataset.view));
  });

  el.sem3Btn.addEventListener("click", () => renderSubjectCards(jsonData.subjects3, 3));
  el.sem4Btn.addEventListener("click", () => renderSubjectCards(jsonData.subjects4, 4));

  el.hamburgerBtn.addEventListener("click", toggleSidebar);
  el.sidebarOverlay.addEventListener("click", toggleSidebar);

  el.monthFilters.addEventListener("click", (event) => {
    const btn = event.target.closest(".month-filter-btn");
    if (!btn) return;
    filterHolidays(btn.dataset.month);
  });

  el.holidaySearch.addEventListener("input", () => {
    const active = document.querySelector(".month-filter-btn.active")?.dataset.month || "all";
    filterHolidays(active);
  });

  el.attendanceCalcBtn.addEventListener("click", calculateAttendance);
  el.attendanceResetBtn.addEventListener("click", resetAttendanceForm);
  el.attendanceFillButtons.addEventListener("click", (event) => {
    const btn = event.target.closest(".attendance-fill");
    if (!btn) return;
    el.attendanceTotal.value = btn.dataset.total || "";
    el.attendanceAttended.value = btn.dataset.attended || "";
    updateAttendanceHint();
  });

  [el.attendanceTotal, el.attendanceAttended].forEach((input) => {
    input.addEventListener("input", updateAttendanceHint);
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") calculateAttendance();
    });
  });
  updateAttendanceHint();

  el.addSubjectBtn.addEventListener("click", () => addCgpaRow());
  el.autofillSem3Btn.addEventListener("click", () => autoFillCGPA(3));
  el.autofillSem4Btn.addEventListener("click", () => autoFillCGPA(4));
  el.cgpaCalcBtn.addEventListener("click", calculateCGPA);

  el.closeModalBtn.addEventListener("click", () => el.modalOverlay.classList.add("hidden"));
  el.modalOverlay.addEventListener("click", (event) => {
    if (event.target === el.modalOverlay) {
      el.modalOverlay.classList.add("hidden");
    }
  });
});
