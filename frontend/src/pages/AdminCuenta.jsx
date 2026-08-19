import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import { api } from "../api";

export default function AdminCuenta() {
  const { usuario, onUsuarioActualizado } = useOutletContext();
  const [passwordActual, setPasswordActual] = useState("");
  const [passwordNueva, setPasswordNueva] = useState("");
  const [passwordConfirmar, setPasswordConfirmar] = useState("");
  const [error, setError] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [enviando, setEnviando] = useState(false);

  async function enviar(evento) {
    evento.preventDefault();
    setError("");
    setMensaje("");

    if (passwordNueva !== passwordConfirmar) {
      setError("La nueva contraseña y su confirmación no coinciden.");
      return;
    }

    setEnviando(true);
    try {
      await api.cambiarPassword({
        password_actual: passwordActual,
        password_nueva: passwordNueva,
      });
      setMensaje("Contraseña actualizada.");
      setPasswordActual("");
      setPasswordNueva("");
      setPasswordConfirmar("");
      if (usuario.debe_cambiar_password) {
        onUsuarioActualizado({ ...usuario, debe_cambiar_password: false });
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div style={{ maxWidth: 360 }}>
      <h1 style={{ fontSize: 18, fontWeight: 500, margin: "0 0 16px" }}>Cambiar contraseña</h1>
      {usuario.debe_cambiar_password && (
        <p className="mensaje-error">
          Por seguridad, debes cambiar tu contraseña antes de usar el resto del panel.
        </p>
      )}
      <div className="tarjeta-blanca">
        {error && <p className="mensaje-error">{error}</p>}
        {mensaje && <p className="mensaje-exito">{mensaje}</p>}
        <form onSubmit={enviar}>
          <div className="campo">
            <label htmlFor="password-actual">
              {usuario.debe_cambiar_password ? "Contraseña temporal" : "Contraseña actual"}
            </label>
            <input
              id="password-actual"
              required
              type="password"
              value={passwordActual}
              onChange={(e) => setPasswordActual(e.target.value)}
            />
          </div>
          <div className="campo">
            <label htmlFor="password-nueva">Contraseña nueva</label>
            <input
              id="password-nueva"
              required
              minLength={8}
              type="password"
              value={passwordNueva}
              onChange={(e) => setPasswordNueva(e.target.value)}
            />
          </div>
          <div className="campo">
            <label htmlFor="password-confirmar">Confirmar contraseña nueva</label>
            <input
              id="password-confirmar"
              required
              minLength={8}
              type="password"
              value={passwordConfirmar}
              onChange={(e) => setPasswordConfirmar(e.target.value)}
            />
          </div>
          <button type="submit" className="boton boton-azul" disabled={enviando} style={{ width: "100%" }}>
            {enviando ? "Guardando…" : "Guardar contraseña"}
          </button>
        </form>
      </div>
    </div>
  );
}
