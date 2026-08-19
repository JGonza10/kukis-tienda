import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";

export default function AdminLogin({ onLogin }) {
  const [nombreUsuario, setNombreUsuario] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);
  const navigate = useNavigate();

  async function enviar(evento) {
    evento.preventDefault();
    setError("");
    setEnviando(true);
    try {
      const usuario = await api.login({ nombre_usuario: nombreUsuario, password });
      onLogin(usuario);
      navigate("/admin/inventario");
    } catch (e) {
      setError(e.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="contenedor" style={{ maxWidth: 360, padding: "60px 20px" }}>
      <div className="tarjeta-blanca">
        <h1 style={{ fontSize: 18, fontWeight: 500, margin: "0 0 16px" }}>Panel de la vendedora</h1>
        {error && <p className="mensaje-error">{error}</p>}
        <form onSubmit={enviar}>
          <div className="campo">
            <label htmlFor="usuario">Usuario</label>
            <input id="usuario" required value={nombreUsuario} onChange={(e) => setNombreUsuario(e.target.value)} />
          </div>
          <div className="campo">
            <label htmlFor="password">Contraseña</label>
            <input id="password" required type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          <button type="submit" className="boton boton-azul" disabled={enviando} style={{ width: "100%" }}>
            {enviando ? "Entrando…" : "Entrar"}
          </button>
        </form>
        <p style={{ fontSize: 12, color: "#6B6259", marginTop: 14, marginBottom: 0 }}>
          El panel solo está disponible entre 9:00 y 22:00, todos los días.
        </p>
      </div>
    </div>
  );
}
