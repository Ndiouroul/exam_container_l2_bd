import { useEffect, useState } from "react";
import { loansApi } from "../api/client.js";
import { useAuth } from "../api/auth.jsx";

export default function LoansPage() {
  const { user, isAdmin } = useAuth();
  const [history, setHistory] = useState([]);
  const [form, setForm] = useState({ book_id: "", user_id: "" });
  const [message, setMessage] = useState(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      setHistory(await loansApi.history());
    } catch (err) {
      setMessage({ type: "error", text: err.message });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const onBorrow = async (e) => {
    e.preventDefault();
    try {
      const targetUserId = isAdmin ? Number(form.user_id) : user.id;
      await loansApi.borrow(Number(form.book_id), targetUserId);
      setMessage({ type: "success", text: "Emprunt enregistré." });
      setForm({ book_id: "", user_id: "" });
      load();
    } catch (err) {
      setMessage({ type: "error", text: err.message });
    }
  };

  const onReturn = async (loanId) => {
    try {
      await loansApi.return(loanId);
      setMessage({ type: "success", text: "Retour enregistré." });
      load();
    } catch (err) {
      setMessage({ type: "error", text: err.message });
    }
  };

  return (
    <>
      <div className="page-header">
        <div className="eyebrow">Mouvements</div>
        <h1>Emprunts</h1>
        <div className="subtitle">
          {isAdmin ? "Enregistrer un prêt au guichet et consulter l'historique complet" : "Vos prêts en cours et votre historique"}
        </div>
      </div>

      {message && (
        <div className={`banner banner--${message.type}`} onClick={() => setMessage(null)}>
          {message.text}
        </div>
      )}

      <div className="form-panel">
        <h2>{isAdmin ? "Enregistrer un emprunt (guichet)" : "Emprunter un livre"}</h2>
        <form onSubmit={onBorrow}>
          <div className="form-grid">
            <div className="form-row">
              <label>ID du livre</label>
              <input
                type="number"
                required
                value={form.book_id}
                onChange={(e) => setForm({ ...form, book_id: e.target.value })}
              />
            </div>
            {isAdmin && (
              <div className="form-row">
                <label>ID de l'utilisateur emprunteur</label>
                <input
                  type="number"
                  required
                  value={form.user_id}
                  onChange={(e) => setForm({ ...form, user_id: e.target.value })}
                />
              </div>
            )}
          </div>
          <div className="form-actions">
            <button type="submit">Emprunter</button>
          </div>
        </form>
      </div>

      <p className="section-label">{isAdmin ? "Historique de tous les emprunts" : "Mon historique d'emprunts"}</p>

      {loading ? (
        <div className="empty-state">Chargement…</div>
      ) : history.length === 0 ? (
        <div className="empty-state">Aucun emprunt enregistré.</div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>N°</th>
              <th>Livre</th>
              {isAdmin && <th>Utilisateur</th>}
              <th>Emprunté le</th>
              <th>Retourné le</th>
              <th>Statut</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {history.map((l) => (
              <tr key={l.id}>
                <td className="mono">{String(l.id).padStart(3, "0")}</td>
                <td className="mono">#{l.book_id}</td>
                {isAdmin && <td className="mono">#{l.user_id}</td>}
                <td>{new Date(l.borrow_date).toLocaleDateString("fr-FR")}</td>
                <td>{l.return_date ? new Date(l.return_date).toLocaleDateString("fr-FR") : "—"}</td>
                <td>
                  <span className={`tag ${l.status === "EN_COURS" ? "tag--pending" : "tag--muted"}`}>
                    {l.status === "EN_COURS" ? "En cours" : "Retourné"}
                  </span>
                </td>
                <td>
                  {l.status === "EN_COURS" && (
                    <button className="secondary" onClick={() => onReturn(l.id)}>Retourner</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
