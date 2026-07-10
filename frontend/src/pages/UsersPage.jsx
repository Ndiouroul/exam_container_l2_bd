import { useEffect, useState } from "react";
import { usersApi } from "../api/client.js";

const EMPTY_FORM = { full_name: "", email: "", user_type: "ETUDIANT", password: "" };
const TYPE_LABELS = {
  ETUDIANT: "Étudiant",
  PROFESSEUR: "Professeur",
  PERSONNEL_ADMINISTRATIF: "Personnel administratif",
};

export default function UsersPage() {
  const [users, setUsers] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editingId, setEditingId] = useState(null);
  const [message, setMessage] = useState(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      setUsers(await usersApi.list());
    } catch (err) {
      setMessage({ type: "error", text: err.message });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const resetForm = () => {
    setForm(EMPTY_FORM);
    setEditingId(null);
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingId) {
        const { password, ...updatePayload } = form;
        await usersApi.update(editingId, updatePayload);
        setMessage({ type: "success", text: "Profil mis à jour." });
      } else {
        await usersApi.create(form);
        setMessage({ type: "success", text: "Utilisateur créé." });
      }
      resetForm();
      load();
    } catch (err) {
      setMessage({ type: "error", text: err.message });
    }
  };

  const onEdit = (u) => {
    setEditingId(u.id);
    setForm({ full_name: u.full_name, email: u.email, user_type: u.user_type, password: "" });
  };

  const onDelete = async (id) => {
    if (!confirm("Supprimer cet utilisateur ?")) return;
    try {
      await usersApi.remove(id);
      load();
    } catch (err) {
      setMessage({ type: "error", text: err.message });
    }
  };

  return (
    <>
      <div className="page-header">
        <div className="eyebrow">Registre</div>
        <h1>Utilisateurs</h1>
        <div className="subtitle">Étudiants, professeurs et personnel administratif</div>
      </div>

      {message && (
        <div className={`banner banner--${message.type}`} onClick={() => setMessage(null)}>
          {message.text}
        </div>
      )}

      <div className="form-panel">
        <h2>{editingId ? "Modifier le profil" : "Créer un utilisateur"}</h2>
        <form onSubmit={onSubmit}>
          <div className="form-grid">
            <div className="form-row span-2">
              <label>Nom complet</label>
              <input
                required
                value={form.full_name}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              />
            </div>
            <div className="form-row">
              <label>Email</label>
              <input
                type="email"
                required
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
            </div>
            <div className="form-row">
              <label>Type d'utilisateur</label>
              <select value={form.user_type} onChange={(e) => setForm({ ...form, user_type: e.target.value })}>
                {Object.entries(TYPE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
            {!editingId && (
              <div className="form-row">
                <label>Mot de passe (min. 6 caractères)</label>
                <input
                  type="password"
                  required
                  minLength={6}
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                />
              </div>
            )}
          </div>
          <div className="form-actions">
            <button type="submit">{editingId ? "Enregistrer" : "Créer"}</button>
            {editingId && (
              <button type="button" className="link" onClick={resetForm}>
                Annuler
              </button>
            )}
          </div>
        </form>
      </div>

      {loading ? (
        <div className="empty-state">Chargement…</div>
      ) : users.length === 0 ? (
        <div className="empty-state">Aucun utilisateur enregistré.</div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>N°</th>
              <th>Nom</th>
              <th>Email</th>
              <th>Type</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td className="mono">{String(u.id).padStart(3, "0")}</td>
                <td>{u.full_name}</td>
                <td className="mono">{u.email}</td>
                <td>{TYPE_LABELS[u.user_type]}</td>
                <td className="actions-cell">
                  <button className="secondary" onClick={() => onEdit(u)}>Modifier</button>
                  <span className="actions-sep">·</span>
                  <button className="danger" onClick={() => onDelete(u.id)}>Supprimer</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
