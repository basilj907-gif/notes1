const API = "http://127.0.0.1:8000";

async function fetchNotes() {
    const res = await fetch(`${API}/notes`);
    const notes = await res.json();

    const list = document.getElementById("notesList");
    list.innerHTML = "";

    notes.forEach(note => {
        const li = document.createElement("li");
        li.innerHTML = `
            ${note.content}
            <button onclick="deleteNote(${note.id})">X</button>
        `;
        list.appendChild(li);
    });
}

async function addNote() {
    const input = document.getElementById("noteInput");
    const content = input.value;

    await fetch(`${API}/notes?content=${content}`, {
        method: "POST"
    });

    input.value = "";
    fetchNotes();
}

async function deleteNote(id) {
    await fetch(`${API}/notes/${id}`, {
        method: "DELETE"
    });

    fetchNotes();
}

fetchNotes();