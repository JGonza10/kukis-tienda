import { useEffect, useState } from "react";
import { api } from "../api";

export default function HorarioBadge() {
  const [horario, setHorario] = useState(null);

  useEffect(() => {
    api.horario().then(setHorario).catch(() => {});
  }, []);

  if (!horario) return null;

  return (
    <span className={`badge-horario ${horario.abierto ? "" : "cerrado"}`}>
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.6" />
        <path d="M12 7v5l3.5 2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      </svg>
      {horario.abierto
        ? `Abierto ahora · ${horario.apertura}–${horario.cierre}`
        : `Cerrado ahora · abre a las ${horario.apertura}`}
    </span>
  );
}
