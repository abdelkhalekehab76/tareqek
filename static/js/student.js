/**
 * Student portal SPA logic
 */
const content = document.getElementById("pageContent");
const pageTitle = document.getElementById("pageTitle");

document.getElementById("studentName").textContent =
  localStorage.getItem("user_name") || "الطالب";

document.querySelectorAll(".nav-item, .bottom-nav a").forEach((el) => {
  el.addEventListener("click", (e) => {
    e.preventDefault();
    document.querySelectorAll(".nav-item, .bottom-nav a").forEach((n) => n.classList.remove("active"));
    el.classList.add("active");
    const page = el.dataset.page;
    loadPage(page);
    history.replaceState(null, "", "#" + page);
    document.getElementById("sidebar")?.classList.remove("open");
  });
});

async function loadPage(page) {
  const titles = {
    dashboard: "الرئيسية", progress: "تقدمي", grades: "درجاتي",
    plan: "خطة الحفظ", quran: "القرآن الكريم", adhkar: "الأذكار",
    tasbeeh: "التسبيح", prayer: "مواقيت الصلاة", schedule: "جدولي",
    profile: "الملف الشخصي",
  };
  pageTitle.textContent = titles[page] || page;
  content.innerHTML = '<div class="empty-state"><div class="icon">⏳</div>جاري التحميل...</div>';
  try {
    switch (page) {
      case "dashboard": await renderDash(); break;
      case "progress": await renderProgress(); break;
      case "grades": await renderGrades(); break;
      case "plan": await renderPlan(); break;
      case "quran": await renderQuran(); break;
      case "adhkar": await renderAdhkar(); break;
      case "tasbeeh": await renderTasbeeh(); break;
      case "prayer": await renderPrayer(); break;
      case "schedule": await renderSchedule(); break;
      case "profile": await renderProfile(); break;
      default: content.innerHTML = "<p>صفحة غير معروفة</p>";
    }
  } catch (err) {
    content.innerHTML = '<div class="empty-state"><div class="icon">⚠️</div>' + escapeHtml(err.message) + '</div>';
  }
}

async function renderDash() {
  const d = await API.get("/api/dashboard/student");
  const badge = document.getElementById("notifBadge");
  if (d.unread_notifications > 0) {
    badge.textContent = d.unread_notifications;
    badge.hidden = false;
  }
  content.innerHTML = `
    <h3 style="margin-bottom:1rem">مرحباً، ${escapeHtml(d.welcome_name)} 👋</h3>
    <div class="stats-grid">
      <div class="stat-card"><div class="stat-value">${d.overall_percentage}%</div><div class="stat-label">تقدم القرآن</div>
        <div class="progress-bar"><div class="fill" style="width:${d.overall_percentage}%"></div></div></div>
      <div class="stat-card"><div class="stat-value">${d.current_juz}</div><div class="stat-label">الجزء الحالي</div></div>
      <div class="stat-card"><div class="stat-value">${d.average_grade ?? "—"}</div><div class="stat-label">متوسط الدرجات</div></div>
      <div class="stat-card"><div class="stat-value">${d.latest_grade ?? "—"}</div><div class="stat-label">آخر درجة</div></div>
    </div>
    <div class="card"><div class="card-title">مهام اليوم</div>
      ${d.today_tasks.length ? d.today_tasks.map(t => `
        <div style="display:flex;justify-content:space-between;align-items:center;padding:0.6rem 0;border-bottom:1px solid var(--border)">
          <div>حفظ: ${t.memorize_pages} ص | مراجعة: ${t.revision_pages} ص<br><small>${t.status === "COMPLETED" ? "✓ مكتمل" : t.status === "IN_PROGRESS" ? "جارٍ" : "لم يبدأ"}</small></div>
          <div class="actions">${t.status !== "COMPLETED" ? `
            ${t.status === "NOT_STARTED" ? `<button class="btn btn-sm btn-secondary" onclick="startTask(${t.id})">بدء</button>` : ""}
            <button class="btn btn-sm btn-success" onclick="completeTask(${t.id})">إكمال ✓</button>` : "<span style='color:var(--success)'>✓</span>"}
          </div></div>`).join("") : '<div class="empty-state">لا مهام لليوم</div>'}
    </div>
    <div class="grid-2">
      <div class="card"><div class="card-title">الإعلانات</div>
        ${d.announcements.map(a => `<div style="padding:0.5rem 0;border-bottom:1px solid var(--border)">${a.important ? "⭐ " : ""}<strong>${escapeHtml(a.title)}</strong><p style="font-size:0.85rem;color:var(--text-muted)">${escapeHtml(a.content)}</p></div>`).join("") || '<div class="empty-state">لا إعلانات</div>'}
      </div>
      <div class="card"><div class="card-title">الفعاليات</div>
        ${d.events.map(e => `<div style="padding:0.5rem 0;border-bottom:1px solid var(--border)">${escapeHtml(e.title)} — ${formatDate(e.date)}</div>`).join("") || '<div class="empty-state">لا فعاليات</div>'}
      </div>
    </div>
    <div class="card"><div class="card-title">إجراءات سريعة</div>
      <div class="actions">
        <button class="btn btn-primary btn-sm" onclick="loadPage('quran')">📗 القرآن</button>
        <button class="btn btn-primary btn-sm" onclick="loadPage('plan')">📋 خطة الحفظ</button>
        <button class="btn btn-primary btn-sm" onclick="loadPage('grades')">📝 الدرجات</button>
        <button class="btn btn-primary btn-sm" onclick="loadPage('adhkar')">🤲 الأذكار</button>
        <button class="btn btn-primary btn-sm" onclick="loadPage('tasbeeh')">📿 التسبيح</button>
        <button class="btn btn-primary btn-sm" onclick="loadPage('prayer')">🕌 الصلاة</button>
      </div>
    </div>`;
}

async function startTask(id) { await API.post(`/api/progress/tasks/${id}/start`); loadPage("dashboard"); }
async function completeTask(id) { await API.post(`/api/progress/tasks/${id}/complete`); loadPage("dashboard"); }

async function renderProgress() {
  const p = await API.get("/api/progress/my");
  content.innerHTML = `
    <div class="stats-grid">
      <div class="stat-card"><div class="stat-value">${p.overall_percentage}%</div><div class="stat-label">التقدم الكلي</div>
        <div class="progress-bar"><div class="fill" style="width:${p.overall_percentage}%"></div></div></div>
      <div class="stat-card"><div class="stat-value">${p.current_juz}</div><div class="stat-label">الجزء الحالي</div></div>
      <div class="stat-card"><div class="stat-value">${p.total_pages_memorized}</div><div class="stat-label">صفحات محفوظة</div></div>
      <div class="stat-card"><div class="stat-value">${p.total_pages_revised}</div><div class="stat-label">صفحات مراجعة</div></div>
    </div>
    <div class="card table-wrap"><div class="card-title">سجل الحفظ</div>
      ${p.history.length ? `<table><thead><tr><th>التاريخ</th><th>الجزء</th><th>السورة</th><th>الآيات</th><th>صفحات</th><th>نوع</th></tr></thead>
        <tbody>${p.history.map(r => `<tr><td>${formatDate(r.record_date)}</td><td>${r.juz}</td><td>${r.surah}</td><td>${r.from_ayah}–${r.to_ayah}</td><td>${r.pages_amount}</td><td>${r.is_revision ? "مراجعة" : "حفظ"}</td></tr>`).join("")}</tbody></table>`
        : '<div class="empty-state">لا سجلات بعد</div>'}
    </div>`;
}

async function renderGrades() {
  const s = await API.get("/api/exams/my/summary");
  content.innerHTML = `
    <div class="stats-grid">
      <div class="stat-card"><div class="stat-value">${s.count}</div><div class="stat-label">عدد الاختبارات</div></div>
      <div class="stat-card"><div class="stat-value">${s.average ?? "—"}</div><div class="stat-label">المتوسط</div></div>
      <div class="stat-card"><div class="stat-value">${s.highest ?? "—"}</div><div class="stat-label">أعلى درجة</div></div>
      <div class="stat-card"><div class="stat-value">${s.lowest ?? "—"}</div><div class="stat-label">أدنى درجة</div></div>
    </div>
    <div class="card table-wrap"><div class="card-title">سجل الدرجات</div>
      ${s.exams.length ? `<table><thead><tr><th>الاختبار</th><th>النوع</th><th>التاريخ</th><th>الدرجة</th><th>ملاحظات</th></tr></thead>
        <tbody>${s.exams.map(e => `<tr><td>${escapeHtml(e.title)}</td><td>${escapeHtml(e.exam_type)}</td><td>${formatDate(e.exam_date)}</td>
          <td><strong>${e.grade}</strong>/${e.max_grade} (${e.percentage}%)</td><td>${escapeHtml(e.teacher_notes || "—")}</td></tr>`).join("")}</tbody></table>`
        : '<div class="empty-state">لا درجات بعد</div>'}
    </div>`;
}

async function renderPlan() {
  const plans = await API.get("/api/progress/plans/my");
  const tasks = await API.get("/api/progress/tasks/today");
  content.innerHTML = `
    <div class="actions" style="margin-bottom:1rem"><button class="btn btn-primary" onclick="showCreatePlan()">+ إنشاء خطة حفظ</button></div>
    <div class="card"><div class="card-title">مهام اليوم</div>
      ${tasks.length ? tasks.map(t => `<div style="display:flex;justify-content:space-between;padding:0.6rem 0;border-bottom:1px solid var(--border)">
        <span>حفظ ${t.memorize_pages} ص | مراجعة ${t.revision_pages} ص — ${t.status}</span>
        ${t.status !== "COMPLETED" ? `<button class="btn btn-sm btn-success" onclick="API.post('/api/progress/tasks/${t.id}/complete').then(()=>loadPage('plan'))">إكمال</button>` : ""}
      </div>`).join("") : '<div class="empty-state">لا مهام لليوم</div>'}
    </div>
    <div class="card"><div class="card-title">خططي النشطة</div>
      ${plans.length ? plans.map(p => `<div style="padding:0.75rem 0;border-bottom:1px solid var(--border)">
        <strong>${escapeHtml(p.title)}</strong>
        <div class="progress-bar"><div class="fill" style="width:${p.progress_pct}%"></div></div>
        <small>${p.tasks_completed}/${p.tasks_total} (${p.progress_pct}%)</small>
      </div>`).join("") : '<div class="empty-state">لا خطط بعد</div>'}
    </div>`;
}

function showCreatePlan() {
  openModal("إنشاء خطة حفظ", `
    <form id="createPlanForm">
      <div class="form-group"><label>عنوان الخطة *</label><input name="title" required /></div>
      <div class="form-row">
        <div class="form-group"><label>تاريخ البدء *</label><input name="start_date" type="date" required value="${new Date().toISOString().slice(0,10)}" /></div>
        <div class="form-group"><label>تاريخ الهدف</label><input name="target_date" type="date" /></div>
      </div>
      <div class="form-row">
        <div class="form-group"><label>كل كم يوم؟</label><input name="frequency_days" type="number" value="1" min="1" /></div>
        <div class="form-group"><label>صفحات الحفظ</label><input name="memorize_pages" type="number" step="0.5" value="2" /></div>
      </div>
      <div class="form-group"><label>صفحات المراجعة</label><input name="revision_pages" type="number" step="0.5" value="3" /></div>
      <button type="submit" class="btn btn-primary btn-block">إنشاء</button>
    </form>`);
  document.getElementById("createPlanForm").onsubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      await API.post("/api/progress/plans", {
        title: fd.get("title"), start_date: fd.get("start_date"),
        target_date: fd.get("target_date") || null,
        frequency_days: parseInt(fd.get("frequency_days")) || 1,
        memorize_pages: parseFloat(fd.get("memorize_pages")) || 1,
        revision_pages: parseFloat(fd.get("revision_pages")) || 2,
      });
      closeModal(); loadPage("plan");
    } catch (err) { alert(err.message); }
  };
}

async function renderQuran() {
  const surahs = await API.get("/api/quran/surahs");
  content.innerHTML = `
    <div class="card">
      <div class="form-group"><input type="text" id="surahSearch" placeholder="بحث عن سورة..." style="width:100%;padding:0.7rem;border:1.5px solid var(--border);border-radius:8px;font-family:var(--font)" oninput="filterSurahs()" /></div>
      <div id="surahList" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:0.5rem">
        ${surahs.map(s => `<button class="btn btn-secondary btn-sm" style="text-align:right" onclick="openSurah(${s.number})" data-name="${s.name}" data-en="${s.englishName}">
          ${s.number}. ${s.name}<br><small style="color:var(--text-muted)">${s.ayahs} آية</small></button>`).join("")}
      </div>
    </div><div id="surahContent"></div>`;
}

function filterSurahs() {
  const q = document.getElementById("surahSearch").value.trim().toLowerCase();
  document.querySelectorAll("#surahList button").forEach(btn => {
    btn.style.display = (!q || btn.dataset.name.includes(q) || btn.dataset.en.toLowerCase().includes(q) || btn.textContent.includes(q)) ? "" : "none";
  });
}

async function openSurah(num) {
  const box = document.getElementById("surahContent");
  box.innerHTML = '<div class="empty-state">جاري تحميل السورة...</div>';
  try {
    const s = await API.get(`/api/quran/surah/${num}`);
    box.innerHTML = `<div class="card" style="margin-top:1rem">
      <div class="card-title" style="text-align:center;font-size:1.3rem">${s.name} — ${s.englishName}</div>
      <p style="text-align:center;color:var(--text-muted)">${s.ayahs_count} آية</p>
      <div class="quran-text">${s.ayahs.map(a => `<span class="ayah">${a.text}<span class="ayah-num">﴿${a.number}﴾</span></span> `).join("")}</div>
    </div>`;
    box.scrollIntoView({ behavior: "smooth" });
  } catch (err) { box.innerHTML = `<div class="empty-state">${escapeHtml(err.message)}</div>`; }
}

async function renderAdhkar() {
  const cats = await API.get("/api/adhkar");
  content.innerHTML = cats.map(c => `
    <div class="card"><div class="card-title">${escapeHtml(c.name_ar)}</div>
      ${c.items.map(item => `
        <div class="adhkar-item" id="adhkar-${item.id}">
          <div class="adhkar-text">${item.text_ar}</div>
          <div style="display:flex;justify-content:space-between;align-items:center">
            <small>${item.source ? "المصدر: " + item.source : ""} | ${item.repetitions} مرة</small>
            <div class="actions"><span id="count-${item.id}" style="font-weight:700;min-width:30px;text-align:center">0</span>
              <button class="btn btn-sm btn-primary" onclick="incAdhkar(${item.id},${item.repetitions})">+1</button></div>
          </div>
        </div>`).join("")}
    </div>`).join("") || '<div class="empty-state">لا أذكار</div>';
}

const adhkarCounts = {};
function incAdhkar(id, max) {
  adhkarCounts[id] = (adhkarCounts[id] || 0) + 1;
  const el = document.getElementById("count-" + id);
  el.textContent = adhkarCounts[id];
  if (adhkarCounts[id] >= max) { el.textContent = "✓"; el.style.color = "var(--success)"; document.getElementById("adhkar-" + id).style.borderRightColor = "var(--success)"; }
}

let tasbeehCount = 0, tasbeehTarget = 33;
async function renderTasbeeh() {
  tasbeehCount = 0;
  content.innerHTML = `
    <div class="card tasbeeh-counter">
      <div class="form-group" style="max-width:200px;margin:0 auto 1rem"><label>الهدف</label>
        <select id="tasbeehTarget" onchange="tasbeehTarget=parseInt(this.value);tasbeehCount=0;updateTasbeeh()">
          <option value="33">33</option><option value="100">100</option><option value="1000">1000</option>
        </select></div>
      <div class="form-group" style="max-width:250px;margin:0 auto">
        <input id="dhikrText" value="سبحان الله" style="text-align:center;font-family:var(--font-quran);font-size:1.2rem" /></div>
      <div class="tasbeeh-count" id="tasbeehDisplay">0</div>
      <div class="progress-bar" style="max-width:200px;margin:0 auto 1.5rem"><div class="fill" id="tasbeehBar" style="width:0%"></div></div>
      <button class="tasbeeh-btn" onclick="tapTasbeeh()">+</button>
      <div class="actions" style="justify-content:center;margin-top:1.5rem">
        <button class="btn btn-secondary" onclick="tasbeehCount=0;updateTasbeeh()">إعادة</button>
        <button class="btn btn-primary" onclick="saveTasbeeh()">حفظ الجلسة</button>
      </div>
    </div>`;
}
function tapTasbeeh() { tasbeehCount++; updateTasbeeh(); if (navigator.vibrate) navigator.vibrate(30); }
function updateTasbeeh() {
  document.getElementById("tasbeehDisplay").textContent = tasbeehCount;
  document.getElementById("tasbeehBar").style.width = Math.min(100, tasbeehCount / tasbeehTarget * 100) + "%";
  if (tasbeehCount >= tasbeehTarget) document.getElementById("tasbeehDisplay").style.color = "var(--success)";
}
async function saveTasbeeh() {
  try {
    await API.post("/api/tasbeeh", { count: tasbeehCount, target: tasbeehTarget, dhikr_text: document.getElementById("dhikrText")?.value || "سبحان الله" });
    alert("تم حفظ الجلسة");
  } catch (err) { alert(err.message); }
}

async function renderPrayer() {
  let pref = { city: "Riyadh", country: "Saudi Arabia" };
  try { pref = await API.get("/api/prayer-times/my"); } catch {}
  content.innerHTML = `
    <div class="card">
      <div class="form-row">
        <div class="form-group"><label>المدينة</label><input id="prayerCity" value="${escapeHtml(pref.city)}" /></div>
        <div class="form-group"><label>الدولة</label><input id="prayerCountry" value="${escapeHtml(pref.country)}" /></div>
      </div>
      <button class="btn btn-primary" onclick="fetchPrayer()">عرض المواقيت</button>
      <div id="prayerResult" style="margin-top:1.5rem"></div>
    </div>`;
  fetchPrayer();
}
async function fetchPrayer() {
  const city = document.getElementById("prayerCity").value || "Riyadh";
  const country = document.getElementById("prayerCountry").value || "Saudi Arabia";
  const box = document.getElementById("prayerResult");
  box.innerHTML = '<div class="empty-state">جاري التحميل...</div>';
  try {
    const d = await API.get(`/api/prayer-times?city=${encodeURIComponent(city)}&country=${encodeURIComponent(country)}`);
    const names = { Fajr: "الفجر", Sunrise: "الشروق", Dhuhr: "الظهر", Asr: "العصر", Maghrib: "المغرب", Isha: "العشاء" };
    box.innerHTML = `<p style="text-align:center;margin-bottom:1rem">${escapeHtml(d.city)} — ${d.date || ""}</p>
      <div class="prayer-grid">${Object.entries(d.timings).map(([k,v]) => `<div class="prayer-card"><div class="name">${names[k]||k}</div><div class="time" dir="ltr">${v}</div></div>`).join("")}</div>`;
  } catch (err) { box.innerHTML = `<div class="empty-state">${escapeHtml(err.message)}</div>`; }
}

async function renderSchedule() {
  const items = await API.get("/api/schedules/my");
  content.innerHTML = `<div class="card"><div class="card-title">مواعيدي القادمة</div>
    ${items.length ? items.map(s => `<div style="padding:0.75rem 0;border-bottom:1px solid var(--border)">
      <strong>${escapeHtml(s.title)}</strong><br>
      <small>${formatDate(s.schedule_date)} ${s.start_time||""} – ${s.end_time||""} | ${escapeHtml(s.location||"")}</small>
    </div>`).join("") : '<div class="empty-state">لا مواعيد قادمة</div>'}</div>`;
}

async function renderProfile() {
  const s = await API.get("/api/students/me");
  content.innerHTML = `
    <div class="card"><div class="card-title">الملف الشخصي</div>
      <p><strong>الاسم:</strong> ${escapeHtml(s.full_name)}</p>
      <p><strong>اسم المستخدم:</strong> <span dir="ltr">${escapeHtml(s.username)}</span></p>
      <p><strong>الهاتف:</strong> ${escapeHtml(s.phone||"—")}</p>
      <p><strong>المعلم:</strong> ${escapeHtml(s.teacher_name||"—")}</p>
      <p><strong>المجموعة:</strong> ${escapeHtml(s.group_name||"—")}</p>
      <p><strong>الجزء الحالي:</strong> ${s.current_juz} | <strong>السورة:</strong> ${s.current_surah}</p>
      ${s.notes ? `<p><strong>ملاحظات:</strong> ${escapeHtml(s.notes)}</p>` : ""}
    </div>
    <div class="card"><div class="card-title">تغيير كلمة المرور</div>
      <form id="changePwForm">
        <div class="form-group"><label>كلمة المرور الحالية</label><input name="current_password" type="password" required dir="ltr" /></div>
        <div class="form-group"><label>كلمة المرور الجديدة</label><input name="new_password" type="password" required dir="ltr" minlength="6" /></div>
        <button type="submit" class="btn btn-primary">تغيير</button>
      </form>
    </div>`;
  document.getElementById("changePwForm").onsubmit = async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      const r = await API.post("/api/auth/change-password", { current_password: fd.get("current_password"), new_password: fd.get("new_password") });
      alert(r.message); e.target.reset();
    } catch (err) { alert(err.message); }
  };
}

const hash = location.hash.replace("#", "") || "dashboard";
loadPage(hash);
document.querySelector(`.nav-item[data-page="${hash}"]`)?.classList.add("active");
