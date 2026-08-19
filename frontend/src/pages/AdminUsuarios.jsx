import { useEffect, useState } from "react";
import { api } from "../api";

export default function AdminUsuarios() {
  const [usuarios, setUsuarios] = useState(null);
  const [error, setError] = useState("");
  const [nombreUsuario, setNombreUsuario] = useState("");
  const [nombre, setNombre] = useState("");
  const [creando, setCreando] = useState(false);
  const [nuevoCreado, setNuevoCreado] = useState(null);

  function cargar() {
    api.adminUsuarios().then(setUsuarios).catch((e) => setError(e.message));
  }

  useEffect(cargar, []);

  async function crear(evento) {
    evento.preventDefault();
    setError("");
    setNuevoCreado(null);
    setCreando(true);
    try {
      const creado = await api.crearUsuario({ nombre_usuario: nombreUsuario, nombre });
      setNuevoCreado(creado);
      setNombreUsuario("");
      setNombre("");
      cargar();
    } catch (e) {
      setError(e.message);
    } finally {
      setCreando(false);
    }
  }

  async function eliminar(usuario) {
    if (!confirm(`¿Eliminar el usuario "${usuario.nombre_usuario}"?`)) return;
    try {
      await api.eliminarUsuario(usuario.id);
      cargar();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div>
      <h1 style={{ fontSize: 18, fontWeight: 500, margin: "0 0 16px" }}>Usuarios</h1>
      {error && <p className="mensaje-error">{error}</p>}

      <div className="tarjeta-blanca" style={{ maxWidth: 420 }}>
        <h2 style={{ fontSize: 15, fontWeight: 500, margin: "0 0 12px" }}>Agregar usuario</h2>
        {nuevoCreado && (
          <p className="mensaje-exito">
            Usuario <strong>{nuevoCreado.nombre_usuario}</strong> creado. Contraseña temporal (cópiala
            ahora, no se vuelve a mostrar): <strong>{nuevoCreado.password_temporal}</strong> — se le
            pedirá cambiarla al iniciar sesión.
          </p>
        )}
        <form onSubmit={crear}>
          <div className="campo">
            <label htmlFor="nuevo-usuario">Usuario</label>
            <input
              id="nuevo-usuario"
              required
              minLength={3}
              value={nombreUsuario}
              onChange={(e) => setNombreUsuario(e.target.value)}
            />
          </div>
          <div className="campo">
            <label htmlFor="nuevo-nombre">Nombre (opcional)</label>
            <input id="nuevo-nombre" value={nombre} onChange={(e) => setNombre(e.target.value)} />
          </div>
          <button type="submit" className="boton boton-naranja" disabled={creando}>
            {creando ? "Creando…" : "Crear usuario"}
          </button>
        </form>
      </div>

      {!usuarios && <p className="centrado">Cargando…</p>}
      {usuarios && usuarios.length > 0 && (
        <div className="tarjeta-blanca" style={{ overflowX: "auto" }}>
          <table className="tabla-simple">
            <thead>
              <tr>
                <th>Usuario</th>
                <th>Nombre</th>
                <th>Estado</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {usuarios.map((u) => (
                <tr key={u.id}>
                  <td>{u.nombre_usuario}</td>
                  <td>{u.nombre}</td>
                  <td>
                    {u.debe_cambiar_password ? (
                      <span className="etiqueta-estado estado-pendiente">Debe cambiar contraseña</span>
                    ) : (
                      <span className="etiqueta-estado estado-entregado">Activo</span>
                    )}
                  </td>
                  <td>
                    {usuarios.length > 1 && (
                      <button className="boton boton-secundario" onClick={() => eliminar(u)}>
                        Eliminar
                      </button>
                    )}
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
