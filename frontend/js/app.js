async function api(path, options = {}) {
  const res = await fetch(`${window.API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt || res.statusText);
  }
  return res.json();
}

function qs(sel) { return document.querySelector(sel); }
function qsa(sel) { return Array.from(document.querySelectorAll(sel)); }

// Tabs
qsa('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    qsa('.tab').forEach(t => t.classList.remove('active'));
    qs(`#${btn.dataset.tab}`).classList.add('active');
  });
});

// Books
async function loadBooks(query = "") {
  const data = await api(`/api/books${query ? `?q=${encodeURIComponent(query)}` : ""}`);
  const tbody = qs("#booksTable tbody");
  tbody.innerHTML = "";
  data.forEach(b => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${b.title}</td><td>${b.author}</td><td>${b.isbn}</td>
      <td>${b.copies}</td><td>${b.available}</td>
      <td>
        <button data-action="del" data-id="${b.id}">Delete</button>
      </td>`;
    tbody.appendChild(tr);
  });
}
qs("#btnSearchBooks").addEventListener("click", () => loadBooks(qs("#bookSearch").value));
qs("#btnAddBook").addEventListener("click", async () => {
  const title = qs("#title").value.trim();
  const author = qs("#author").value.trim();
  const isbn = qs("#isbn").value.trim();
  const copies = parseInt(qs("#copies").value, 10) || 1;
  if (!title || !author || !isbn) return alert("Fill all fields");
  try {
    await api("/api/books", { method: "POST", body: JSON.stringify({ title, author, isbn, copies }) });
    qs("#title").value = qs("#author").value = qs("#isbn").value = "";
    qs("#copies").value = 1;
    await loadBooks();
    await loadBooksForLoan();
  } catch (e) { alert(e.message); }
});
qs("#booksTable").addEventListener("click", async (e) => {
  const btn = e.target.closest("button");
  if (!btn) return;
  if (btn.dataset.action === "del") {
    if (!confirm("Delete this book?")) return;
    try {
      await api(`/api/books/${btn.dataset.id}`, { method: "DELETE" });
      await loadBooks();
      await loadBooksForLoan();
    } catch (e) { alert(e.message); }
  }
});

// Members
async function loadMembers() {
  const data = await api("/api/members");
  const tbody = qs("#membersTable tbody");
  tbody.innerHTML = "";
  data.forEach(m => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${m.name}</td><td>${m.email}</td>`;
    tbody.appendChild(tr);
  });
}
qs("#btnAddMember").addEventListener("click", async () => {
  const name = qs("#memberName").value.trim();
  const email = qs("#memberEmail").value.trim();
  if (!name || !email) return alert("Fill all fields");
  try {
    await api("/api/members", { method: "POST", body: JSON.stringify({ name, email }) });
    qs("#memberName").value = qs("#memberEmail").value = "";
    await loadMembers();
    await loadMembersForLoan();
  } catch (e) { alert(e.message); }
});

// Loans
async function loadLoans() {
  const data = await api("/api/loans");
  const tbody = qs("#loansTable tbody");
  tbody.innerHTML = "";
  data.forEach(l => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${l.book_title}</td><td>${l.member_name}</td>
      <td>${new Date(l.issued_at).toLocaleString()}</td>
      <td>${l.returned_at ? new Date(l.returned_at).toLocaleString() : "-"}</td>
      <td>${l.returned_at ? "" : `<button data-action="return" data-id="${l.id}">Return</button>`}</td>`;
    tbody.appendChild(tr);
  });
}

async function loadBooksForLoan() {
  const data = await api("/api/books");
  const sel = qs("#loanBook");
  sel.innerHTML = data.map(b => `<option value="${b.id}">${b.title} (${b.available}/${b.copies})</option>`).join("");
}
async function loadMembersForLoan() {
  const data = await api("/api/members");
  const sel = qs("#loanMember");
  sel.innerHTML = data.map(m => `<option value="${m.id}">${m.name}</option>`).join("");
}

qs("#btnIssue").addEventListener("click", async () => {
  const book_id = parseInt(qs("#loanBook").value, 10);
  const member_id = parseInt(qs("#loanMember").value, 10);
  try {
    await api("/api/loans/issue", { method: "POST", body: JSON.stringify({ book_id, member_id }) });
    await loadBooks();
    await loadBooksForLoan();
    await loadLoans();
  } catch (e) { alert(e.message); }
});

qs("#loansTable").addEventListener("click", async (e) => {
  const btn = e.target.closest("button");
  if (!btn) return;
  if (btn.dataset.action === "return") {
    try {
      await api("/api/loans/return", { method: "POST", body: JSON.stringify({ loan_id: parseInt(btn.dataset.id, 10) }) });
      await loadBooks();
      await loadBooksForLoan();
      await loadLoans();
    } catch (e) { alert(e.message); }
  }
});

// init
(async function init() {
  await loadBooks();
  await loadMembers();
  await loadBooksForLoan();
  await loadMembersForLoan();
  await loadLoans();
})();
