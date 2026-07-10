// Illustration SVG légère et autonome représentant une salle de lecture de
// bibliothèque (rangées d'étagères, table de lecture, lampe) utilisée comme
// arrière-plan des écrans d'authentification. Générée en interne : aucune
// dépendance externe, aucun poids d'image à charger.
export default function LibraryBackdrop() {
  return (
    <svg
      className="auth-backdrop"
      viewBox="0 0 1600 1000"
      preserveAspectRatio="xMidYMid slice"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#1a1f24" />
          <stop offset="100%" stopColor="#0f1215" />
        </linearGradient>
        <linearGradient id="floorGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#20262c" />
          <stop offset="100%" stopColor="#161a1e" />
        </linearGradient>
        <radialGradient id="lampGlow" cx="50%" cy="30%" r="60%">
          <stop offset="0%" stopColor="#c89b3c" stopOpacity="0.5" />
          <stop offset="100%" stopColor="#c89b3c" stopOpacity="0" />
        </radialGradient>
      </defs>

      <rect width="1600" height="1000" fill="url(#skyGrad)" />
      <rect y="760" width="1600" height="240" fill="url(#floorGrad)" />

      {/* Rangées d'étagères en perspective, gauche */}
      {[0, 1, 2, 3, 4].map((row) => (
        <g key={`l-${row}`} opacity={0.9 - row * 0.13}>
          <rect x={-40 + row * 8} y={120 + row * 6} width="330" height="620" fill="#232a30" stroke="#2e353b" strokeWidth="2" />
          {Array.from({ length: 6 }).map((_, shelf) => (
            <line
              key={shelf}
              x1={-40 + row * 8}
              y1={160 + row * 6 + shelf * 96}
              x2={290 + row * 8}
              y2={160 + row * 6 + shelf * 96}
              stroke="#3a4249"
              strokeWidth="3"
            />
          ))}
          {Array.from({ length: 6 }).map((_, shelf) =>
            Array.from({ length: 14 }).map((_, book) => (
              <rect
                key={`${shelf}-${book}`}
                x={-30 + row * 8 + book * 21}
                y={166 + row * 6 + shelf * 96}
                width="15"
                height={70 + ((book * 7 + shelf * 3) % 18)}
                fill={book % 3 === 0 ? "#5a4632" : book % 3 === 1 ? "#4a3f52" : "#3f4a44"}
                opacity="0.85"
              />
            ))
          )}
        </g>
      ))}

      {/* Rangées d'étagères en perspective, droite (miroir) */}
      {[0, 1, 2, 3, 4].map((row) => (
        <g key={`r-${row}`} opacity={0.9 - row * 0.13}>
          <rect x={1310 - row * 8} y={120 + row * 6} width="330" height="620" fill="#232a30" stroke="#2e353b" strokeWidth="2" />
          {Array.from({ length: 6 }).map((_, shelf) => (
            <line
              key={shelf}
              x1={1310 - row * 8}
              y1={160 + row * 6 + shelf * 96}
              x2={1640 - row * 8}
              y2={160 + row * 6 + shelf * 96}
              stroke="#3a4249"
              strokeWidth="3"
            />
          ))}
          {Array.from({ length: 6 }).map((_, shelf) =>
            Array.from({ length: 14 }).map((_, book) => (
              <rect
                key={`${shelf}-${book}`}
                x={1320 - row * 8 + book * 21}
                y={166 + row * 6 + shelf * 96}
                width="15"
                height={70 + ((book * 5 + shelf * 4) % 18)}
                fill={book % 3 === 0 ? "#4a3f52" : book % 3 === 1 ? "#5a4632" : "#3f4a44"}
                opacity="0.85"
              />
            ))
          )}
        </g>
      ))}

      {/* Halo de lumière central façon lampe de bibliothèque */}
      <circle cx="800" cy="300" r="520" fill="url(#lampGlow)" />

      {/* Table de lecture centrale */}
      <rect x="620" y="760" width="360" height="14" rx="3" fill="#2e353b" />
      <rect x="650" y="774" width="16" height="140" fill="#232a30" />
      <rect x="934" y="774" width="16" height="140" fill="#232a30" />

      {/* Lampe de table */}
      <line x1="800" y1="760" x2="800" y2="700" stroke="#3a4249" strokeWidth="4" />
      <path d="M 770 700 L 830 700 L 815 660 L 785 660 Z" fill="#c89b3c" opacity="0.75" />
      <circle cx="800" cy="700" r="6" fill="#e3c77a" />

      {/* Livres ouverts sur la table */}
      <path d="M 690 762 Q 715 748 740 762 L 740 774 Q 715 762 690 774 Z" fill="#8a6a3a" opacity="0.8" />
      <path d="M 860 764 Q 885 752 910 764 L 910 774 Q 885 764 860 774 Z" fill="#6a5a8a" opacity="0.8" />
    </svg>
  );
}
