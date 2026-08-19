/**
 * Admin dashboard SPA logic
 */
const content = document.getElementById("pageContent");
const pageTitle = document.getElementById("pageTitle");

document.getElementById("adminName").textContent =
  localStorage.getItem("user_name") || "المدير";

// Navigation
document.querySelectorAll(".nav-item").forEach((el) => {
  el.addEventListener("click", (e) => {
    e.preventDefault();
    document.querySelectorAll(".nav-item").forEach((n) => n.classList.remove("active"));
    el.classList.add("active");
    const page = el.dataset.page;
    loadPage(page);
    history.replaceState(null, "", "#" + page);
    document.getElementById("sidebar")?.classList.remove("open");
  });
});

async function loadPage(page) {
  const titles = {
    dashboard: "لوحة التحكم",
    students: "إدارة الطلاب",
    exams: "الاختبارات والدرجات",
    progress: "تتبع الحفظ",
    schedules: "الجداول",
    events: "الفعاليات",
    announcements: "الإعلانات",
    notifications: "إرسال إشعارات",
  };
  pageTitle.textContent = titles[page] || page;
  content.innerHTML = '<div class="empty-state"><div class="icon">⏳</div>جاري التحميل...</div>';

  try {
    switch (page) {
      case "dashboard": await renderDashboard(); break;
      case "students": await renderStudents(); break;
      case "exams": await renderExams(); break;
      case "progress": await renderProgress(); break;
      case "schedules": await renderSchedules(); break;
      case "events": await renderEvents(); break;
      case "announcements": await renderAnnouncements(); break;
      case "notifications": await renderNotifications(); break;
      default: content.innerHTML = "<p>صفحة غير معروفة</p>";
    }
  } catch (err) {
    content.innerHTML = `<div class="empty-state"><div class="icon">⚠️</div>${escapeHtml(err.message)}</div>`;
  }
}

/* ─── Dashboard ─── */
async function renderDashboard() {
  const d = await API.get("/api/dashboard/admin");
  content.innerHTML = `
    <div class="stats-grid">
      <div class="stat-card"><div class="stat-value">${d.stats.total_students}</div><div class="stat-label">إجمالي الطلاب</div></div>
      <div class="stat-card"><div class="stat-value">${d.stats.active_students}</div><div class="stat-label">طلاب نشطون</div></div>
      <div class="stat-card"><div class="stat-value">${d.stats.total_exams}</div><div class="stat-label">الاختبارات</div></div>
      <div class="stat-card"><div class="stat-value">${d.stats.average_grade ?? "—"}</div><div class="stat-label">متوسط الدرجات</div></div>
    </div>
    <div class="grid-2">
      <div class="card">
        <div class="card-title">أعلى تقدماً</div>
        ${d.top_students.length ? `<table><thead><tr><th>الاسم</th><th>الجزء</th><th>صفحات</th></tr></thead>
          <tbody>${d.top_students.map(s => `<tr><td>${escapeHtml(s.name)}</td><td>${s.juz}</td><td>${s.pages}</td></tr>`).join("")}</tbody></table>`
          : '<div class="empty-state">لا يوجد بيانات</div>'}
      </div>
      <div class="card">
        <div class="card-title">يحتاجون انتباه</div>
        ${d.need_attention.length ? `<table><thead><tr><th>الاسم</th><th>المعدل</th><th>الجزء</th></tr></thead>
          <tbody>${d.need_attention.map(s => `<tr><td>${escapeHtml(s.name)}</td><td>${s.avg_grade ?? "—"}</td><td>${s.juz}</td></tr>`).join("")}</tbody></table>`
          : '<div class="empty-state">لا يوجد</div>'}
      </div>
    </div>
    <div class="grid-2">
      <div class="card">
        <div class="card-title">الإعلانات الأخيرة</div>
        ${d.recent_announcements.map(a => `<div style="padding:0.5rem 0;border-bottom:1px solid var(--border)">${a.important ? "⭐ " : ""}${escapeHtml(a.title)}</div>`).join("") || '<div class="empty-state">لا إعلانات</div>'}
      </div>
      <div class="card">
        <div class="card-title">الفعاليات القادمة</div>
        ${d.upcoming_events.map(e => `<div style="padding:0.5rem 0;border-bottom:1px solid var(--border)">${escapeHtml(e.title)} — ${formatDate(e.date)}</div>`).join("") || '<div class="empty-state">لا فعاليات</div>'}
      </div>
    </div>
  `;
}

/* ─── Students ─── */
let studentsCache = [];

async function renderStudents() {
  studentsCache = await API.get("/api/students/");
  content.innerHTML = `
    <div class="actions" style="margin-bottom:1rem">
      <button class="btn btn-primary" onclick="showAddStudent()">+ إضافة طالب</button>
      <input type="text" id="searchStudent" placeholder="بحث بالاسم أو اسم المستخدم..." style="flex:1;padding:0.6rem 1rem;border:1.5px solid var(--border);border-radius:8px;font-family:var(--font)" oninput="filterStudents()" />
    </div>
    <div class="card table-wrap">
      <table>
        <thead><tr>
          <th>الاسم</th><th>اسم المستخدم</th><th>الجزء</th><th>المجموعة</th><th>المعلم</th><th>الحالة</th><th>إجراءات</th>
        </tr></thead>
        <tbody id="studentsTable">${renderStudentRows(studentsCache)}</tbody>
      </table>
    </div>
  `;
}

function renderStudentRows(list) {
  if (!list.length) return '<tr><td colspan="7"><div class="empty-state">لا يوجد طلاب</div></td></tr>';
  return list.map(s => `
    <tr>
      <td>${escapeHtml(s.full_name)}</td>
      <td dir="ltr">${escapeHtml(s.username)}</td>
      <td>${s.current_juz}</td>
      <td>${escapeHtml(s.group_name || "—")}</td>
      <td>${escapeHtml(s.teacher_name || "—")}</td>
      <td class="status-${s.status === "ACTIVE" ? "active" : "inactive"}">${s.status === "ACTIVE" ? "نشط" : "معطل"}</td>
      <td class="actions">
        <button class="btn btn-sm btn-secondary" onclick="viewStudent(${s.id})">عرض</button>
        <button class="btn btn-sm btn-secondary" onclick="editStudent(${s.id})">تعديل</button>
        <button class="btn btn-sm btn-accent" onclick="resetPass(${s.id})">كلمة المرور</button>
        <button class="btn btn-sm btn-secondary" onclick="toggleStatus(${s.id})">${s.status === "ACTIVE" ? "تعطيل" : "تفعيل"}</button>
        <button class="btn btn-sm btn-danger" onclick="deleteStudent(${s.id}, '${escapeHtml(s.full_name)}')">حذف</button>
      </td>
    </tr>
  `).join("");
}

function filterStudents() {
  const q = document.getElementById("searchStudent").value.trim().toLowerCase();
  const filtered = studentsCache.filter(s =>
    s.full_name.toLowerCase().includes(q) || s.username.toLowerCase().includes(q)
  );
  document.getElementById("studentsTable").innerHTML = renderStudentRows(filtered);
}

function showAddStudent() {
  openModal("إضافة طالب جديد", `
    <form id="addStudentForm">
      <div class="form-row">
        <div class="form-group"><label>الاسم الكامل *</label><input name="full_name" required /></div>
        <div class="form-group"><label>اسم المستخدم *</label><input name="username" required dir="ltr" /></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>كلمة المرور *</label><input name="password" type="password" required dir="ltr" /></div>
        <div class="form-group"><label>الهاتف</label><input name="phone" dir="ltr" /></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>ولي الأمر</label><input name="parent_name" /></div>
        <div class="form-group"><label>هاتف ولي الأمر</label><input name="parent_phone" dir="ltr" /></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>المعلم</label><input name="teacher_name" /></div>
        <div class="form-group"><label>المجموعة</label><input name="group_name" /></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>الجزء الحالي</label><input name="current_juz" type="number" value="1" min="1" max="30" /></div>
        <div class="form-group"><label>السورة الحالية</label><input name="current_surah" type="number" value="1" min="1" max="114" /></div>
      </div>
      <div class="form-group"><label>ملاحظات</label><textarea name="notes"></textarea></div>
      <button type="submit" class="btn btn-primary btn-block">حفظ</button>
    </form>
  `);
  document.getElementById("addStudentForm").onsubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const body = Object.fromEntries(fd.entries());
    body.current_juz = parseInt(body.current_juz) || 1;
    body.current_surah = parseInt(body.current_surah) || 1;
    try {
      await API.post("/api/students/", body);
      closeModal();
      renderStudents();
    } catch (err) { alert(err.message); }
  };
}

async function viewStudent(id) {
  const s = await API.get(`/api/students/${id}`);
  const stats = await API.get(`/api/students/${id}/stats`);
  openModal(s.full_name, `
    <p><strong>اسم المستخدم:</strong> <span dir="ltr">${escapeHtml(s.username)}</span></p>
    <p><strong>الهاتف:</strong> ${escapeHtml(s.phone || "—")}</p>
    <p><strong>ولي الأمر:</strong> ${escapeHtml(s.parent_name || "—")} (${escapeHtml(s.parent_phone || "—")})</p>
    <p><strong>المعلم / المجموعة:</strong> ${escapeHtml(s.teacher_name || "—")} / ${escapeHtml(s.group_name || "—")}</p>
    <p><strong>الموضع الحالي:</strong> جزء ${s.current_juz} — سورة ${s.current_surah}</p>
    <p><strong>صفحات محفوظة:</strong> ${s.total_pages_memorized} | <strong>مراجعة:</strong> ${s.total_pages_revised}</p>
    <p><strong>متوسط الدرجات:</strong> ${stats.average_grade ?? "—"} (${stats.exams_count} اختبار)</p>
    <p><strong>ملاحظات:</strong> ${escapeHtml(s.notes || "—")}</p>
  `);
}

async function editStudent(id) {
  const s = await API.get(`/api/students/${id}`);
  openModal("تعديل طالب", `
    <form id="editStudentForm">
      <div class="form-row">
        <div class="form-group"><label>الاسم</label><input name="full_name" value="${escapeHtml(s.full_name)}" /></div>
        <div class="form-group"><label>الهاتف</label><input name="phone" value="${escapeHtml(s.phone || "")}" dir="ltr" /></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>ولي الأمر</label><input name="parent_name" value="${escapeHtml(s.parent_name || "")}" /></div>
        <div class="form-group"><label>هاتف ولي الأمر</label><input name="parent_phone" value="${escapeHtml(s.parent_phone || "")}" dir="ltr" /></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>المعلم</label><input name="teacher_name" value="${escapeHtml(s.teacher_name || "")}" /></div>
        <div class="form-group"><label>المجموعة</label><input name="group_name" value="${escapeHtml(s.group_name || "")}" /></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>الجزء</label><input name="current_juz" type="number" value="${s.current_juz}" min="1" max="30" /></div>
        <div class="form-group"><label>السورة</label><input name="current_surah" type="number" value="${s.current_surah}" min="1" max="114" /></div>
      </div>
      <div class="form-group"><label>ملاحظات</label><textarea name="notes">${escapeHtml(s.notes || "")}</textarea></div>
      <div class="form-group"><label><input type="checkbox" name="notes_visible_to_student" ${s.notes_visible_to_student ? "checked" : ""} /> إظهار الملاحظات للطالب</label></div>
      <button type="submit" class="btn btn-primary btn-block">حفظ التعديلات</button>
    </form>
  `);
  document.getElementById("editStudentForm").onsubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const body = Object.fromEntries(fd.entries());
    body.current_juz = parseInt(body.current_juz);
    body.current_surah = parseInt(body.current_surah);
    body.notes_visible_to_student = !!fd.get("notes_visible_to_student");
    try {
      await API.put(`/api/students/${id}`, body);
      closeModal();
      renderStudents();
    } catch (err) { alert(err.message); }
  };
}

async function resetPass(id) {
  const pw = prompt("كلمة المرور الجديدة:");
  if (!pw || pw.length < 4) return;
  try {
    await API.post(`/api/students/${id}/reset-password`, { new_password: pw });
    alert("تم إعادة تعيين كلمة المرور");
  } catch (err) { alert(err.message); }
}

async function toggleStatus(id) {
  try {
    const r = await API.post(`/api/students/${id}/toggle-status`);
    alert(r.message);
    renderStudents();
  } catch (err) { alert(err.message); }
}

async function deleteStudent(id, name) {
  if (!confirm(`هل أنت متأكد من حذف الطالب "${name}"؟ لا يمكن التراجع.`)) return;
  try {
    await API.del(`/api/students/${id}`);
    renderStudents();
  } catch (err) { alert(err.message); }
}

/* ─── Exams ─── */
async function renderExams() {
  const exams = await API.get("/api/exams/");
  const students = await API.get("/api/students/");
  content.innerHTML = `
    <div class="actions" style="margin-bottom:1rem">
      <button class="btn btn-primary" onclick="showAddExam()">+ إضافة اختبار</button>
    </div>
    <div class="card table-wrap">
      <table>
        <thead><tr><th>العنوان</th><th>النوع</th><th>التاريخ</th><th>الدرجة</th><th>ملاحظات</th><th></th></tr></thead>
        <tbody>
          ${exams.length ? exams.map(e => `
            <tr>
              <td>${escapeHtml(e.title)}</td>
              <td>${escapeHtml(e.exam_type)}</td>
              <td>${formatDate(e.exam_date)}</td>
              <td><strong>${e.grade}</strong> / ${e.max_grade} (${e.percentage}%)</td>
              <td>${escapeHtml(e.teacher_notes || "—")}</td>
              <td><button class="btn btn-sm btn-danger" onclick="deleteExam(${e.id})">حذف</button></td>
            </tr>
          `).join("") : '<tr><td colspan="6"><div class="empty-state">لا اختبارات بعد</div></td></tr>'}
        </tbody>
      </table>
    </div>
  `;
  window._studentsForExam = students;
}

function showAddExam() {
  const opts = (window._studentsForExam || []).map(s =>
    `<option value="${s.id}">${escapeHtml(s.full_name)}</option>`
  ).join("");
  openModal("إضافة اختبار / درجة", `
    <form id="addExamForm">
      <div class="form-group"><label>الطالب *</label><select name="student_id" required>${opts}</select></div>
      <div class="form-group"><label>عنوان الاختبار *</label><input name="title" required /></div>
      <div class="form-row">
        <div class="form-group"><label>النوع</label>
          <select name="exam_type">
            <option value="NEW_MEMORIZATION">حفظ جديد</option>
            <option value="REVISION">مراجعة</option>
            <option value="RECITATION">تلاوة</option>
            <option value="TAJWEED">تجويد</option>
            <option value="MONTHLY">شهري</option>
            <option value="FINAL">نهائي</option>
            <option value="GENERAL">عام</option>
          </select>
        </div>
        <div class="form-group"><label>التاريخ *</label><input name="exam_date" type="date" required value="${new Date().toISOString().slice(0,10)}" /></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>الدرجة *</label><input name="grade" type="number" step="0.5" required /></div>
        <div class="form-group"><label>من</label><input name="max_grade" type="number" value="100" /></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>الجزء</label><input name="juz" type="number" min="1" max="30" /></div>
        <div class="form-group"><label>السورة</label><input name="surah" type="number" min="1" max="114" /></div>
      </div>
      <div class="form-group"><label>ملاحظات المعلم</label><textarea name="teacher_notes"></textarea></div>
      <button type="submit" class="btn btn-primary btn-block">حفظ</button>
    </form>
  `);
  document.getElementById("addExamForm").onsubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const body = Object.fromEntries(fd.entries());
    body.student_id = parseInt(body.student_id);
    body.grade = parseFloat(body.grade);
    body.max_grade = parseFloat(body.max_grade) || 100;
    if (body.juz) body.juz = parseInt(body.juz);
    if (body.surah) body.surah = parseInt(body.surah);
    try {
      await API.post("/api/exams/", body);
      closeModal();
      renderExams();
    } catch (err) { alert(err.message); }
  };
}

async function deleteExam(id) {
  if (!confirm("حذف هذا الاختبار؟")) return;
  await API.del(`/api/exams/${id}`);
  renderExams();
}

/* ─── Progress ─── */
async function renderProgress() {
  const students = await API.get("/api/students/");
  content.innerHTML = `
    <div class="actions" style="margin-bottom:1rem">
      <button class="btn btn-primary" onclick="showAddProgress()">+ تسجيل تقدم</button>
    </div>
    <div class="card">
      <div class="card-title">اختر طالباً لعرض سجله</div>
      <select id="progStudent" onchange="loadProgressHistory()" style="width:100%;padding:0.6rem;border-radius:8px;border:1.5px solid var(--border);font-family:var(--font)">
        <option value="">— اختر —</option>
        ${students.map(s => `<option value="${s.id}">${escapeHtml(s.full_name)} (جزء ${s.current_juz})</option>`).join("")}
      </select>
      <div id="progHistory" style="margin-top:1rem"></div>
    </div>
  `;
  window._studentsForProg = students;
}

async function loadProgressHistory() {
  const id = document.getElementById("progStudent").value;
  if (!id) return;
  const hist = await API.get(`/api/progress/student/${id}`);
  document.getElementById("progHistory").innerHTML = hist.length
    ? `<table><thead><tr><th>التاريخ</th><th>الجزء</th><th>السورة</th><th>الآيات</th><th>صفحات</th><th>نوع</th></tr></thead>
       <tbody>${hist.map(r => `<tr>
         <td>${formatDate(r.record_date)}</td><td>${r.juz}</td><td>${r.surah}</td>
         <td>${r.from_ayah}–${r.to_ayah}</td><td>${r.pages_amount}</td>
         <td>${r.is_revision ? "مراجعة" : "حفظ"}</td>
       </tr>`).join("")}</tbody></table>`
    : '<div class="empty-state">لا سجلات بعد</div>';
}

function showAddProgress() {
  const opts = (window._studentsForProg || []).map(s =>
    `<option value="${s.id}">${escapeHtml(s.full_name)}</option>`
  ).join("");
  openModal("تسجيل تقدم حفظ", `
    <form id="addProgForm">
      <div class="form-group"><label>الطالب *</label><select name="student_id" required>${opts}</select></div>
      <div class="form-row">
        <div class="form-group"><label>الجزء *</label><input name="juz" type="number" min="1" max="30" required /></div>
        <div class="form-group"><label>السورة *</label><input name="surah" type="number" min="1" max="114" required /></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>من آية *</label><input name="from_ayah" type="number" min="1" required /></div>
        <div class="form-group"><label>إلى آية *</label><input name="to_ayah" type="number" min="1" required /></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>عدد الصفحات</label><input name="pages_amount" type="number" step="0.5" value="1" /></div>
        <div class="form-group"><label>النوع</label>
          <select name="is_revision"><option value="false">حفظ جديد</option><option value="true">مراجعة</option></select>
        </div>
      </div>
      <div class="form-group"><label>ملاحظات</label><textarea name="notes"></textarea></div>
      <button type="submit" class="btn btn-primary btn-block">حفظ</button>
    </form>
  `);
  document.getElementById("addProgForm").onsubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const body = {
      student_id: parseInt(fd.get("student_id")),
      juz: parseInt(fd.get("juz")),
      surah: parseInt(fd.get("surah")),
      from_ayah: parseInt(fd.get("from_ayah")),
      to_ayah: parseInt(fd.get("to_ayah")),
      pages_amount: parseFloat(fd.get("pages_amount")) || 0,
      is_revision: fd.get("is_revision") === "true",
      notes: fd.get("notes") || null,
      status: "COMPLETED",
    };
    try {
      await API.post("/api/progress/", body);
      closeModal();
      renderProgress();
    } catch (err) { alert(err.message); }
  };
}

/* ─── Schedules ─── */
async function renderSchedules() {
  const items = await API.get("/api/schedules");
  const students = await API.get("/api/students/");
  content.innerHTML = `
    <div class="actions" style="margin-bottom:1rem">
      <button class="btn btn-primary" onclick="showAddSchedule()">+ إضافة موعد</button>
    </div>
    <div class="card table-wrap">
      <table>
        <thead><tr><th>العنوان</th><th>النوع</th><th>التاريخ</th><th>الوقت</th><th>المكان</th><th></th></tr></thead>
        <tbody>
          ${items.length ? items.map(s => `
            <tr>
              <td>${escapeHtml(s.title)}</td>
              <td>${escapeHtml(s.schedule_type)}</td>
              <td>${formatDate(s.schedule_date)}</td>
              <td>${s.start_time || "—"} – ${s.end_time || ""}</td>
              <td>${escapeHtml(s.location || "—")}</td>
              <td><button class="btn btn-sm btn-danger" onclick="API.del('/api/schedules/${s.id}').then(renderSchedules)">حذف</button></td>
            </tr>
          `).join("") : '<tr><td colspan="6"><div class="empty-state">لا مواعيد</div></td></tr>'}
        </tbody>
      </table>
    </div>
  `;
  window._studentsForSch = students;
}

function showAddSchedule() {
  const opts = '<option value="">— عام / مجموعة —</option>' +
    (window._studentsForSch || []).map(s => `<option value="${s.id}">${escapeHtml(s.full_name)}</option>`).join("");
  openModal("إضافة موعد", `
    <form id="addSchForm">
      <div class="form-group"><label>العنوان *</label><input name="title" required /></div>
      <div class="form-row">
        <div class="form-group"><label>الطالب</label><select name="student_id">${opts}</select></div>
        <div class="form-group"><label>النوع</label>
          <select name="schedule_type">
            <option value="memorization">جلسة حفظ</option>
            <option value="revision">مراجعة</option>
            <option value="exam">اختبار</option>
            <option value="class">حصة</option>
            <option value="individual">فردي</option>
            <option value="group">جماعي</option>
          </select>
        </div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>التاريخ *</label><input name="schedule_date" type="date" required value="${new Date().toISOString().slice(0,10)}" /></div>
        <div class="form-group"><label>من</label><input name="start_time" type="time" /></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>إلى</label><input name="end_time" type="time" /></div>
        <div class="form-group"><label>المكان</label><input name="location" /></div>
      </div>
      <div class="form-group"><label>المعلم</label><input name="teacher_name" /></div>
      <div class="form-group"><label>ملاحظات</label><textarea name="notes"></textarea></div>
      <button type="submit" class="btn btn-primary btn-block">حفظ</button>
    </form>
  `);
  document.getElementById("addSchForm").onsubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const body = Object.fromEntries(fd.entries());
    if (body.student_id) body.student_id = parseInt(body.student_id);
    else delete body.student_id;
    try {
      await API.post("/api/schedules", body);
      closeModal();
      renderSchedules();
    } catch (err) { alert(err.message); }
  };
}

/* ─── Events ─── */
async function renderEvents() {
  const items = await API.get("/api/events");
  content.innerHTML = `
    <div class="actions" style="margin-bottom:1rem">
      <button class="btn btn-primary" onclick="showAddEvent()">+ إضافة فعالية</button>
    </div>
    <div class="card">
      ${items.length ? items.map(e => `
        <div style="padding:0.75rem 0;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center">
          <div>
            <strong>${escapeHtml(e.title)}</strong><br>
            <small>${formatDate(e.event_date)} ${e.start_time || ""} — ${escapeHtml(e.location || "")}</small>
            ${e.description ? `<p style="margin-top:0.3rem;color:var(--text-muted)">${escapeHtml(e.description)}</p>` : ""}
          </div>
          <button class="btn btn-sm btn-danger" onclick="API.del('/api/events/${e.id}').then(renderEvents)">حذف</button>
        </div>
      `).join("") : '<div class="empty-state">لا فعاليات قادمة</div>'}
    </div>
  `;
}

function showAddEvent() {
  openModal("إضافة فعالية", `
    <form id="addEvForm">
      <div class="form-group"><label>العنوان *</label><input name="title" required /></div>
      <div class="form-group"><label>الوصف</label><textarea name="description"></textarea></div>
      <div class="form-row">
        <div class="form-group"><label>التاريخ *</label><input name="event_date" type="date" required /></div>
        <div class="form-group"><label>الوقت</label><input name="start_time" type="time" /></div>
      </div>
      <div class="form-group"><label>المكان</label><input name="location" /></div>
      <button type="submit" class="btn btn-primary btn-block">حفظ</button>
    </form>
  `);
  document.getElementById("addEvForm").onsubmit = async (e) => {
    e.preventDefault();
    const body = Object.fromEntries(new FormData(e.target).entries());
    try {
      await API.post("/api/events", body);
      closeModal();
      renderEvents();
    } catch (err) { alert(err.message); }
  };
}

/* ─── Announcements ─── */
async function renderAnnouncements() {
  const items = await API.get("/api/announcements");
  content.innerHTML = `
    <div class="actions" style="margin-bottom:1rem">
      <button class="btn btn-primary" onclick="showAddAnn()">+ إعلان جديد</button>
    </div>
    <div class="card">
      ${items.length ? items.map(a => `
        <div style="padding:0.75rem 0;border-bottom:1px solid var(--border);display:flex;justify-content:space-between">
          <div>
            ${a.is_important ? "⭐ " : ""}<strong>${escapeHtml(a.title)}</strong>
            <p style="color:var(--text-muted);margin-top:0.3rem">${escapeHtml(a.content)}</p>
            <small>${formatDate(a.publish_at)}</small>
          </div>
          <button class="btn btn-sm btn-danger" onclick="API.del('/api/announcements/${a.id}').then(renderAnnouncements)">حذف</button>
        </div>
      `).join("") : '<div class="empty-state">لا إعلانات</div>'}
    </div>
  `;
}

function showAddAnn() {
  openModal("إعلان جديد", `
    <form id="addAnnForm">
      <div class="form-group"><label>العنوان *</label><input name="title" required /></div>
      <div class="form-group"><label>المحتوى *</label><textarea name="content" required></textarea></div>
      <div class="form-group"><label><input type="checkbox" name="is_important" /> إعلان مهم</label></div>
      <button type="submit" class="btn btn-primary btn-block">نشر</button>
    </form>
  `);
  document.getElementById("addAnnForm").onsubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const body = {
      title: fd.get("title"),
      content: fd.get("content"),
      is_important: !!fd.get("is_important"),
      is_published: true,
    };
    try {
      await API.post("/api/announcements", body);
      closeModal();
      renderAnnouncements();
    } catch (err) { alert(err.message); }
  };
}

/* ─── Notifications send ─── */
async function renderNotifications() {
  const students = await API.get("/api/students/");
  content.innerHTML = `
    <div class="card">
      <div class="card-title">إرسال إشعار</div>
      <form id="sendNotifForm">
        <div class="form-group"><label>المستلم</label>
          <select name="target" id="notifTarget">
            <option value="all">جميع الطلاب</option>
            ${students.map(s => `<option value="${s.user_id}">${escapeHtml(s.full_name)}</option>`).join("")}
          </select>
        </div>
        <div class="form-group"><label>العنوان *</label><input name="title" required /></div>
        <div class="form-group"><label>الرسالة *</label><textarea name="message" required></textarea></div>
        <button type="submit" class="btn btn-primary">إرسال</button>
      </form>
    </div>
  `;
  document.getElementById("sendNotifForm").onsubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const target = fd.get("target");
    const body = { title: fd.get("title"), message: fd.get("message") };
    if (target !== "all") body.user_id = parseInt(target);
    try {
      const r = await API.post("/api/notifications/send", body);
      alert(r.message);
      e.target.reset();
    } catch (err) { alert(err.message); }
  };
}

// Init
const hash = location.hash.replace("#", "") || "dashboard";
loadPage(hash);
document.querySelector(`.nav-item[data-page="${hash}"]`)?.classList.add("active");
