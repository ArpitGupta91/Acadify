const API_BASE = "http://localhost:8000";
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
  wrap.className = `message ${isBot ? "message-bot" : "message-user"}`;
  wrap.innerHTML = formatText(text);

  if (isBot) {
    const tagInfo = sourceTag(meta.type, meta.sources || []);
    const tag = document.createElement("span");
    tag.className = "message-source-tag";
    tag.textContent = tagInfo.label;
    wrap.appendChild(tag);

    const file = document.createElement("div");
    file.className = "message-source-file";
    file.textContent = `Source: ${tagInfo.file}`;
    wrap.appendChild(file);
  }

  el.chatContainer.appendChild(wrap);
  el.chatContainer.scrollTop = el.chatContainer.scrollHeight;
}

function showTyping(show) {
  el.typingIndicator.classList.toggle("hidden", !show);
}

async function sendMessage(query) {
  const clean = (query || "").trim();
  if (!clean || isLoading) {
    return;
  }

  isLoading = true;
  renderMessage(clean, {}, false);
  el.chatInput.value = "";
  showTyping(true);

  try {
    const data = await apiPost("/chat", {
      query: query,
      session_id: SESSION_ID
    });
    renderMessage(data.answer || "No answer found.", { type: data.type, sources: data.sources || [] }, true);
    chatHistory.push({ query: clean, answer: data.answer, type: data.type, timestamp: data.timestamp });
  } catch (error) {
    renderMessage(
      `Sorry, I couldn't reach the backend service. Please ensure FastAPI is running on ${API_BASE}.\nError: ${error.message}`,
      { type: "not_found", sources: [] },
      true
    );
  } finally {
    showTyping(false);
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

    el.attendanceResult.classList.remove("hidden");
    el.attendanceResult.innerHTML = `
      <div class="attendance-circle" style="background:${attendanceColor(pct)}">${pct.toFixed(2)}%</div>
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

function gradeToPoints(grade) {
  const map = { O: 10, "A+": 9, A: 8, "B+": 7, B: 6, C: 5, P: 4, F: 0 };
  return map[grade] ?? 0;
}

function addCgpaRow(subject = { name: "", credits: 3, grade: "A" }) {
  const row = document.createElement("div");
  row.className = "cgpa-row";
  row.innerHTML = `
    <input class="cgpa-name" type="text" placeholder="Subject Name" value="${subject.name}" />
    <select class="cgpa-grade">
      <option ${subject.grade === "O" ? "selected" : ""}>O</option>
      <option ${subject.grade === "A+" ? "selected" : ""}>A+</option>
      <option ${subject.grade === "A" ? "selected" : ""}>A</option>
      <option ${subject.grade === "B+" ? "selected" : ""}>B+</option>
      <option ${subject.grade === "B" ? "selected" : ""}>B</option>
      <option ${subject.grade === "C" ? "selected" : ""}>C</option>
      <option ${subject.grade === "P" ? "selected" : ""}>P</option>
      <option ${subject.grade === "F" ? "selected" : ""}>F</option>
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

    subjects.push({ name, grade_points: gradeToPoints(grade), credits });
  }

  try {
    const result = await apiPost("/calculate/cgpa", { subjects });
    const gradeMeaning = {
      O: "Outstanding",
      "A+": "Excellent",
      A: "Very Good",
      "B+": "Good",
      B: "Above Average",
      C: "Average",
      P: "Pass",
      F: "Fail",
    };

    el.cgpaResult.classList.remove("hidden");
    el.cgpaResult.innerHTML = `
      <h3 style="margin: 0 0 8px;">CGPA: ${Number(result.cgpa).toFixed(2)}</h3>
      <p><strong>Grade:</strong> ${result.grade_letter} (${gradeMeaning[result.grade_letter] || ""})</p>
      <p><strong>Total Credits:</strong> ${result.total_credits}</p>
      <p><strong>Weighted Score:</strong> ${result.weighted_sum}</p>
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
    jsonData.subjects4 = sem4.subjects || [];

    renderExamCards(jsonData.examSchedule);
    renderHolidayCards(jsonData.holidays);
    renderSubjectCards(jsonData.subjects3, 3);

    renderMessage(
      "👋 Hello! I'm CollegeAI, your academic assistant at KIET.\nI can help you with:\n• 📅 Exam dates and schedules\n• 📚 Subject syllabus and topics\n• 🎯 Marks and credit structure\n• 🗓️ Holidays and important dates\n• 📊 Attendance calculations\nNote: I serve CSE/CS branch students only.",
      { type: "json_lookup", sources: ["Structured JSON"] },
      true
    );

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
