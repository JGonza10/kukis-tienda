import { useEffect, useState } from "react";
import { api } from "../api";

export default function AdminCategorias() {
  const [categorias, setCategorias] = useState(null);
  const [nombre, setNombre] = useState("");
  const [error, setError] = useState("");
  const [creando, setCreando] = useState(false);

  function cargar() {
    api.adminCategorias().then(setCategorias).catch((e) => setError(e.message));
  }

  useEffect(cargar, []);

  async function crear(evento) {
    evento.preventDefault();
    setError("");
    setCreando(true);
    try {
      await api.crearCategoria({ nombre });
      setNombre("");
      cargar();
    } catch (e) {
      setError(e.message);
    } finally {
      setCreando(false);
    }
  }

  async function eliminar(categoria) {
    if (!confirm(`¿Eliminar la categoría "${categoria.nombre}"?`)) return;
    setError("");
    try {
      await api.eliminarCategoria(categoria.id);
      cargar();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div>
      <h1 style={{ fontSize: 18, fontWeight: 500, margin: "0 0 16px" }}>Categorías</h1>
      <p style={{ fontSize: 13, color: "#6B6259", margin: "0 0 16px", maxWidth: 480 }}>
        Aquí das de alta las categorías una sola vez. Al agregar o editar una prenda, la eliges de
        una lista en vez de escribirla — así se evitan categorías repetidas por un error de dedo o
        por mayúsculas y minúsculas.
      </p>
      {error && <p className="mensaje-error">{error}</p>}

      <div className="tarjeta-blanca" style={{ maxWidth: 420 }}>
        <h2 style={{ fontSize: 15, fontWeight: 500, margin: "0 0 12px" }}>Agregar categoría</h2>
        <form onSubmit={crear}>
          <div className="campo">
            <label htmlFor="nueva-categoria">Nombre</label>
            <input
              id="nueva-categoria"
              required
              minLength={2}
              placeholder="Ej. Blusas"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
            />
          </div>
          <button type="submit" className="boton boton-naranja" disabled={creando}>
            {creando ? "Agregando…" : "Agregar categoría"}
          </button>
        </form>
      </div>

      {!categorias && <p className="centrado">Cargando…</p>}
      {categorias && categorias.length === 0 && (
        <p className="centrado">Todavía no has agregado ninguna categoría.</p>
      )}
      {categorias && categorias.length > 0 && (
        <div className="tarjeta-blanca" style={{ maxWidth: 420, overflowX: "auto" }}>
          <table className="tabla-simple">
            <thead>
              <tr>
                <th>Nombre</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {categorias.map((c) => (
                <tr key={c.id}>
                  <td>{c.nombre}</td>
                  <td>
                    <button className="boton boton-secundario" onClick={() => eliminar(c)}>
                      Eliminar
                    </button>
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
