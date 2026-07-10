import { Routes, Route, NavLink, Navigate } from "react-router-dom";
import BooksPage from "./pages/BooksPage.jsx";
import UsersPage from "./pages/UsersPage.jsx";
import LoansPage from "./pages/LoansPage.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import AdminRoute from "./components/AdminRoute.jsx";
import { useAuth } from "./api/auth.jsx";

const ROLE_LABELS = {
  ETUDIANT: "Étudiant",
  PROFESSEUR: "Professeur",
  PERSONNEL_ADMINISTRATIF: "Personnel administratif",
};

function AppLayout() {
  const { user, logout, isAdmin } = useAuth();

  const NAV = [
    { to: "/", label: "Livres", end: true, show: true },
    { to: "/utilisateurs", label: "Utilisateurs", show: isAdmin },
    { to: "/emprunts", label: "Emprunts", show: true },
  ];

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar__brand">
          Bibliothèque <em>Numérique</em>
          <small>DIT · L2</small>
        </div>
        <nav className="topbar__nav">
          {NAV.filter((item) => item.show).map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => "topbar__link" + (isActive ? " active" : "")}
            >
              {item.label}
            </NavLink>
          ))}
          <div className="topbar__user">
            <span>
              {user?.full_name}
              <span className="role-badge">{ROLE_LABELS[user?.user_type] || user?.user_type}</span>
            </span>
            <button className="link" onClick={logout}>Déconnexion</button>
          </div>
        </nav>
      </header>

      <main className="main">
        <Routes>
          <Route path="/" element={<BooksPage />} />
          <Route
            path="/utilisateurs"
            element={
              <AdminRoute>
                <UsersPage />
              </AdminRoute>
            }
          />
          <Route path="/emprunts" element={<LoansPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>

      <footer className="foot">
        books · users · loans — FastAPI · PostgreSQL · Docker
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}
