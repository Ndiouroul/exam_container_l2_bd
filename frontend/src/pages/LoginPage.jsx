import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../api/auth.jsx";
import LibraryBackdrop from "../assets/library-bg.jsx";

export default function LoginPage() {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const redirectTo = location.state?.from || "/";

  const [mode, setMode] = useState("login"); // "login" | "register"
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const [loginForm, setLoginForm] = useState({ email: "", password: "" });
  const [registerForm, setRegisterForm] = useState({ full_name: "", email: "", password: "" });

  const switchMode = (next) => {
    setMode(next);
    setError(null);
  };

  const onLogin = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(loginForm.email, loginForm.password);
      navigate(redirectTo, { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const onRegister = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await register(registerForm);
      navigate(redirectTo, { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-shell">
      <LibraryBackdrop />
      <div className="auth-overlay" />

      <div className="auth-content">
        <div className="auth-brand">
          Bibliothèque <em>Numérique</em>
        </div>

        <div className="library-card library-card--wide">
          <div className="library-card__head">
            <div>
              <div className="label">{mode === "login" ? "Carte d'accès" : "Nouvelle inscription"}</div>
              <h1>{mode === "login" ? "Identification" : "Créer un compte"}</h1>
              <p className="library-card__tagline">
                {mode === "login"
                  ? "Réservé aux étudiants, professeurs et personnel du Dakar Institute of Technology"
                  : "Ouvert à tout étudiant ou professeur du DIT — aucune démarche préalable requise"}
              </p>
            </div>
            <div className="library-card__number">
              DIT · L2
              <br />
              {mode === "login" ? "N° adhérent requis" : "Fonds Bibliothèque"}
            </div>
          </div>

          <div className="library-card__body">
            {error && <div className="banner banner--error" onClick={() => setError(null)}>{error}</div>}

            {mode === "login" ? (
              <form onSubmit={onLogin}>
                <div className="form-grid">
                  <div className="form-row span-2">
                    <label>Email</label>
                    <input
                      type="email"
                      required
                      autoFocus
                      placeholder="prenom.nom@dit.sn"
                      value={loginForm.email}
                      onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })}
                    />
                  </div>
                  <div className="form-row span-2">
                    <label>Mot de passe</label>
                    <input
                      type="password"
                      required
                      value={loginForm.password}
                      onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                    />
                  </div>
                </div>
                <div className="form-actions">
                  <button type="submit" disabled={loading}>
                    {loading ? "Connexion…" : "Se connecter"}
                  </button>
                  <button type="button" className="link" onClick={() => switchMode("register")}>
                    S'inscrire
                  </button>
                </div>
              </form>
            ) : (
              <form onSubmit={onRegister}>
                <div className="form-grid">
                  <div className="form-row span-2">
                    <label>Nom complet</label>
                    <input
                      required
                      autoFocus
                      value={registerForm.full_name}
                      onChange={(e) => setRegisterForm({ ...registerForm, full_name: e.target.value })}
                    />
                  </div>
                  <div className="form-row span-2">
                    <label>Email</label>
                    <input
                      type="email"
                      required
                      placeholder="prenom.nom@dit.sn"
                      value={registerForm.email}
                      onChange={(e) => setRegisterForm({ ...registerForm, email: e.target.value })}
                    />
                  </div>
                  <div className="form-row span-2">
                    <label>Mot de passe (min. 6 caractères)</label>
                    <input
                      type="password"
                      required
                      minLength={6}
                      value={registerForm.password}
                      onChange={(e) => setRegisterForm({ ...registerForm, password: e.target.value })}
                    />
                  </div>
                </div>
                <div className="form-actions">
                  <button type="submit" disabled={loading}>
                    {loading ? "Création…" : "Créer mon compte"}
                  </button>
                  <button type="button" className="link" onClick={() => switchMode("login")}>
                    J'ai déjà un compte
                  </button>
                </div>
              </form>
            )}
          </div>

          <div className="library-card__barcode" />
        </div>

        {mode === "register" && (
          <p className="auth-footnote">
            Un compte administrateur du personnel de la bibliothèque peut, si nécessaire,
            créer directement un compte professeur ou personnel administratif.
          </p>
        )}
      </div>
    </div>
  );
}
