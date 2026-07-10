import { useEffect, useState } from "react";
import { booksApi } from "../api/client.js";
import { useAuth } from "../api/auth.jsx";

const EMPTY_FORM = { title: "", author: "", isbn: "", year: "", quantity: 1 };

export default function BooksPage() {
  const { isAdmin } = useAuth();
  const [books, setBooks] = useState([]);
  const [search, setSearch] = useState("");
  const [form, setForm] = useState(EMPTY_FORM);
  const [editingId, setEditingId] = useState(null);
  const [message, setMessage] = useState(null);
  const [loading, setLoading] = useState(false);

  const load = async (q = "") => {
    setLoading(true);
    try {
      setBooks(await booksApi.list(q));
    } catch (err) {
      setMessage({ type: "error", text: err.message });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const onSearch = (e) => {
    e.preventDefault();
    load(search);
  };

  const resetForm = () => {
    setForm(EMPTY_FORM);
    setEditingId(null);
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        title: form.title,
        author: form.author,
        isbn: form.isbn,
        year: form.year ? Number(form.year) : null,
        quantity: Number(form.quantity),
      };
      if (editingId) {
        await booksApi.update(editingId, payload);
        setMessage({ type: "success", text: "Livre mis à jour." });
      } else {
        await booksApi.create(payload);
        setMessage({ type: "success", text: "Livre ajouté au catalogue." });
      }
      resetForm();
      load(search);
    } catch (err) {
      setMessage({ type: "error", text: err.message });
    }
  };

  const onEdit = (book) => {
    setEditingId(book.id);
    setForm({
      title: book.title,
      author: book.author,
      isbn: book.isbn,
      year: book.year ?? "",
      quantity: book.quantity,
    });
  };

  const onDelete = async (id) => {
    if (!confirm("Supprimer ce livre du catalogue ?")) return;
    try {
      await booksApi.remove(id);
      load(search);
    } catch (err) {
      setMessage({ type: "error", text: err.message });
    }
  };

  return (
    <>
      <div className="page-header">
        <div className="eyebrow">Catalogue</div>
        <h1>Livres</h1>
        <div className="subtitle">
          {isAdmin
            ? "Fonds documentaire, disponibilité et gestion du catalogue"
            : "Recherchez un ouvrage et consultez sa disponibilité"}
        </div>
      </div>

      {message && (
        <div className={`banner banner--${message.type}`} onClick={() => setMessage(null)}>
          {message.text}
        </div>
      )}

      {isAdmin && (
        <div className="form-panel">
          <h2>{editingId ? "Modifier le livre" : "Ajouter un livre"}</h2>
          <form onSubmit={onSubmit}>
            <div className="form-grid">
              <div className="form-row span-2">
                <label>Titre</label>
                <input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
              </div>
              <div className="form-row">
                <label>Auteur</label>
                <input required value={form.author} onChange={(e) => setForm({ ...form, author: e.target.value })} />
              </div>
              <div className="form-row">
                <label>ISBN</label>
                <input required value={form.isbn} onChange={(e) => setForm({ ...form, isbn: e.target.value })} />
              </div>
              <div className="form-row">
                <label>Année</label>
                <input type="number" value={form.year} onChange={(e) => setForm({ ...form, year: e.target.value })} />
              </div>
              <div className="form-row">
                <label>Quantité totale</label>
                <input
                  type="number"
                  min="0"
                  required
                  value={form.quantity}
                  onChange={(e) => setForm({ ...form, quantity: e.target.value })}
                />
              </div>
            </div>
            <div className="form-actions">
              <button type="submit">{editingId ? "Enregistrer" : "Ajouter"}</button>
              {editingId && (
                <button type="button" className="link" onClick={resetForm}>
                  Annuler
                </button>
              )}
            </div>
          </form>
        </div>
      )}

      <form className="toolbar" onSubmit={onSearch}>
        <input
          placeholder="Rechercher par titre, auteur ou ISBN…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <button type="submit" className="secondary">Rechercher</button>
      </form>

      {loading ? (
        <div className="empty-state">Chargement…</div>
      ) : books.length === 0 ? (
        <div className="empty-state">Aucun livre trouvé.</div>
      ) : (
        <div className="record-list">
          {books.map((b, i) => (
            <div className="record-row" key={b.id}>
              <div className="record-row__index">{String(i + 1).padStart(2, "0")}</div>
              <div>
                <p className="record-row__title">{b.title}</p>
                <p className="record-row__meta">
                  {b.author}
                  <span className="sep">·</span>
                  {b.year || "s.d."}
                  <span className="sep">·</span>
                  ISBN {b.isbn}
                </p>
                <p className={`record-row__status ${b.available_quantity > 0 ? "ok" : "out"}`}>
                  {b.available_quantity > 0
                    ? `${b.available_quantity} / ${b.quantity} disponible(s)`
                    : "Épuisé"}
                </p>
              </div>
              {isAdmin && (
                <div className="record-row__actions">
                  <button className="secondary" onClick={() => onEdit(b)}>Modifier</button>
                  <button className="danger" onClick={() => onDelete(b.id)}>Supprimer</button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </>
  );
}
