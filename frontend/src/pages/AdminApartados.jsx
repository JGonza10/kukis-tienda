import { useEffect, useState } from "react";
import { api } from "../api";

const ETIQUETAS = {
  pendiente: "Pendiente",
  confirmado: "Confirmado",
  entregado: "Entregado",
  cancelado: "Cancelado",
};

export default function AdminApartados() {
  const [apartados, setApartados] = useState(null);
  const [filtro, setFiltro] = useState("");
  const [error, setError] = useState("");
  const [mensaje, setMensaje] = useState("");

  function cargar() {
    api.adminApartados(filtro || undefined).then(setApartados).catch((e) => setError(e.message));
  }

  useEffect(cargar, [filtro]);

  async function cambiarEstado(id, estado) {
    setError("");
    setMensaje("");
    try {
      await api.actualizarApartado(id, { estado });
      cargar();
      setMensaje(`Estado actualizado a "${ETIQUETAS[estado]}".`);
      setTimeout(() => setMensaje(""), 3000);
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, flexWrap: "wrap", gap: 8 }}>
        <h1 style={{ fontSize: 18, fontWeight: 500, margin: 0 }}>Apartados</h1>
        <select value={filtro} onChange={(e) => setFiltro(e.target.value)} style={{ padding: 8, borderRadius: 8, border: "0.5px solid var(--borde)" }}>
          <option value="">Todos los estados</option>
          {Object.entries(ETIQUETAS).map(([valor, texto]) => (
            <option key={valor} value={valor}>{texto}</option>
          ))}
        </select>
      </div>

      {error && <p className="mensaje-error">{error}</p>}
      {mensaje && <p className="mensaje-exito">{mensaje}</p>}
      {!apartados && <p className="centrado">Cargando…</p>}
      {apartados && apartados.length === 0 && <p className="centrado">No hay apartados con ese filtro.</p>}

      {apartados && apartados.length > 0 && (
        <div className="tarjeta-blanca" style={{ overflowX: "auto" }}>
          <table className="tabla-simple">
            <thead>
              <tr>
                <th>Prenda</th><th>Clienta</th><th>Teléfono</th><th>Entrega</th><th>Estado</th><th></th>
              </tr>
            </thead>
            <tbody>
              {apartados.map((a) => (
                <tr key={a.id}>
                  <td>{a.producto_nombre} · {a.talla} · {a.color}</td>
                  <td>{a.cliente_nombre}</td>
                  <td>
                    <a href={`https://wa.me/52${a.cliente_telefono}`} target="_blank" rel="noreferrer">
                      {a.cliente_telefono}
                    </a>
                  </td>
                  <td>{a.fecha_entrega}</td>
                  <td><span className={`etiqueta-estado estado-${a.estado}`}>{ETIQUETAS[a.estado]}</span></td>
                  <td>
                    <select
                      value={a.estado}
                      onChange={(e) => cambiarEstado(a.id, e.target.value)}
                      style={{ padding: 6, borderRadius: 8, border: "0.5px solid var(--borde)", fontSize: 12 }}
                    >
                      {Object.entries(ETIQUETAS).map(([valor, texto]) => (
                        <option key={valor} value={valor}>{texto}</option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
