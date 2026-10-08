const $ = (id) => document.getElementById(id);
let activeTab = "text";
let loaderTimer;

/* ---------- file drop zones ---------- */
function setupDrop(dropId, inputId, nameId, emptyHtml) {
  const drop = $(dropId), input = $(inputId), name = $(nameId);

  const update = () => {
    const f = input.files[0];
    drop.classList.toggle("has-file", !!f);
    name.innerHTML = f ? "✓ " + f.name : emptyHtml;
  };

  input.addEventListener("change", update);
  ["dragenter", "dragover"].forEach((ev) =>
    drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("over"); }));
  ["dragleave", "drop"].forEach((ev) =>
    drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.remove("over"); }));
  drop.addEventListener("drop", (e) => {
    if (e.dataTransfer.files.length) { input.files = e.dataTransfer.files; update(); }
  });
}

setupDrop("resumeDrop", "resume", "resumeName", "Drop your resume here or <u>browse</u>");
setupDrop("jdDrop", "jdFile", "jdName", "Drop the job description PDF here or <u>browse</u>");

/* ---------- JD tabs ---------- */
document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    activeTab = tab.dataset.tab;
    document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t === tab));
    $("paneText").classList.toggle("hidden", activeTab !== "text");
    $("panePdf").classList.toggle("hidden", activeTab !== "pdf");
  });
});

/* ---------- helpers ---------- */
function showError(msg) {
  const el = $("error");
  el.classList.add("hidden");
  void el.offsetWidth;               // restart the shake animation
  el.textContent = msg;
  el.classList.remove("hidden");
}

function setLoading(on) {
  $("loader").classList.toggle("hidden", !on);
  $("btn").disabled = on;
  $("btnText").textContent = on ? "Analyzing…" : "Analyze match";
  clearInterval(loaderTimer);

  if (on) {
    $("error").classList.add("hidden");
    $("results").classList.add("hidden");
    $("results").classList.remove("show");
    const msgs = ["Reading your resume…", "Parsing the job description…", "Comparing skills…", "Scoring the match…", "Writing suggestions…"];
    let i = 0;
    $("loaderText").textContent = msgs[0];
    loaderTimer = setInterval(() => {
      i = (i + 1) % msgs.length;
      $("loaderText").textContent = msgs[i];
    }, 1800);
  }
}

function fillChips(el, items) {
  el.innerHTML = "";
  (items || []).forEach((t, i) => {
    const s = document.createElement("span");
    s.textContent = t;
    s.style.animationDelay = `${0.5 + i * 0.05}s`;
    el.appendChild(s);
  });
  if (!items || !items.length) el.innerHTML = '<span style="animation-delay:.5s;border:1px solid #333;color:#888">None</span>';
}

function fillList(el, items) {
  el.innerHTML = "";
  (items || []).forEach((t) => {
    const li = document.createElement("li");
    li.textContent = t;
    el.appendChild(li);
  });
}

function countUp(el, target) {
  const start = performance.now(), dur = 1400;
  const tick = (now) => {
    const t = Math.min((now - start) / dur, 1);
    const eased = 1 - Math.pow(1 - t, 3);
    el.textContent = Math.round(target * eased);
    if (t < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

function render(d) {
  const score = Math.max(0, Math.min(100, Number(d.match_score) || 0));
  const results = $("results");
  const ring = $("ring");

  $("summary").textContent = d.summary || "";
  fillChips($("matched"), d.matched_skills);
  fillChips($("missing"), d.missing_skills);
  fillList($("strengths"), d.strengths);
  fillList($("improvements"),
    (d.improvements || []).map((i) => (typeof i === "string" ? i : `${i.section}: ${i.suggestion}`)));
  $("rewritten").textContent = d.rewritten_summary || "";

  ring.style.setProperty("--p", 0);
  $("score").textContent = "0";
  results.classList.remove("hidden", "show");
  void results.offsetWidth;
  results.classList.add("show");

  requestAnimationFrame(() => {
    ring.style.setProperty("--p", score);
    countUp($("score"), score);
  });
  results.scrollIntoView({ behavior: "smooth", block: "start" });
}

/* ---------- submit ---------- */
$("form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const resume = $("resume").files[0];
  if (!resume) return showError("Please upload your resume.");

  const data = new FormData();
  data.append("resume", resume);

  if (activeTab === "pdf") {
    const jdFile = $("jdFile").files[0];
    if (!jdFile) return showError("Please upload the job description file, or switch to 'Paste text'.");
    data.append("jd_file", jdFile);
  } else {
    const text = $("jd").value.trim();
    if (!text) return showError("Please paste the job description, or switch to 'Upload PDF'.");
    data.append("jd_text", text);
  }

  setLoading(true);
  try {
    const res = await fetch("/analyze", { method: "POST", body: data });
    const json = await res.json();
    if (!res.ok) throw new Error(json.detail || "Something went wrong.");
    render(json);
  } catch (err) {
    showError(err.message);
  } finally {
    setLoading(false);
  }
});