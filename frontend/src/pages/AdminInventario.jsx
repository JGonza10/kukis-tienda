import { useEffect, useState } from "react";
import { api } from "../api";

const VARIANTE_VACIA = { talla: "", color: "", color_hex: "#FF6FA5", stock: 1 };

function SelectorCategoria({ value, onChange, categorias }) {
  return (
    <select value={value} onChange={onChange}>
      <option value="">Sin categoría</option>
      {categorias.map((c) => (
        <option key={c.id} value={c.nombre}>{c.nombre}</option>
      ))}
    </select>
  );
}

function FormularioNuevoProducto({ onCreado, categorias }) {
  const [nombre, setNombre] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [categoria, setCategoria] = useState("");
  const [precio, setPrecio] = useState("");
  const [variantes, setVariantes] = useState([{ ...VARIANTE_VACIA }]);
  const [fotos, setFotos] = useState([]);
  const [error, setError] = useState("");
  const [guardando, setGuardando] = useState(false);

  function actualizarVariante(i, campo, valor) {
    setVariantes((prev) => prev.map((v, idx) => (idx === i ? { ...v, [campo]: valor } : v)));
  }

  async function guardar(evento) {
    evento.preventDefault();
    setError("");
    if (!nombre || !precio) {
      setError("Nombre y precio son obligatorios.");
      return;
    }
    setGuardando(true);
    try {
      const producto = await api.crearProducto({
        nombre,
        descripcion,
        categoria,
        precio: Number(precio),
        variantes: variantes.filter((v) => v.talla && v.color),
      });
      for (const foto of fotos) {
        await api.subirImagen(producto.id, foto).catch((e) => setError(e.message));
      }
      setNombre(""); setDescripcion(""); setCategoria(""); setPrecio("");
      setVariantes([{ ...VARIANTE_VACIA }]);
      setFotos([]);
      onCreado(producto);
    } catch (e) {
      setError(e.message);
    } finally {
      setGuardando(false);
    }
  }

  return (
    <form onSubmit={guardar} className="tarjeta-blanca">
      <h2 style={{ fontSize: 15, fontWeight: 500, margin: "0 0 12px" }}>Agregar prenda nueva</h2>
      {error && <p className="mensaje-error">{error}</p>}
      <div className="campo">
        <label>Nombre</label>
        <input value={nombre} onChange={(e) => setNombre(e.target.value)} required />
      </div>
      <div className="campo">
        <label>Descripción</label>
        <textarea rows={2} value={descripcion} onChange={(e) => setDescripcion(e.target.value)} />
      </div>
      <div style={{ display: "flex", gap: 12 }}>
        <div className="campo" style={{ flex: 1 }}>
          <label>Categoría</label>
          <SelectorCategoria value={categoria} onChange={(e) => setCategoria(e.target.value)} categorias={categorias} />
        </div>
        <div className="campo" style={{ flex: 1 }}>
          <label>Precio</label>
          <input type="number" min="0" step="1" value={precio} onChange={(e) => setPrecio(e.target.value)} required />
        </div>
      </div>

      <label style={{ fontSize: 13, color: "#6B6259" }}>Tallas y colores disponibles</label>
      {variantes.map((v, i) => (
        <div key={i} style={{ display: "flex", gap: 8, margin: "8px 0", alignItems: "center" }}>
          <input placeholder="Talla" style={{ width: 60 }} value={v.talla} onChange={(e) => actualizarVariante(i, "talla", e.target.value)} />
          <input placeholder="Color" style={{ width: 100 }} value={v.color} onChange={(e) => actualizarVariante(i, "color", e.target.value)} />
          <input type="color" value={v.color_hex} onChange={(e) => actualizarVariante(i, "color_hex", e.target.value)} style={{ width: 40, padding: 2 }} />
          <input type="number" min="0" placeholder="Stock" style={{ width: 70 }} value={v.stock} onChange={(e) => actualizarVariante(i, "stock", e.target.value)} />
          {variantes.length > 1 && (
            <button type="button" className="boton boton-secundario" onClick={() => setVariantes((prev) => prev.filter((_, idx) => idx !== i))}>
              Quitar
            </button>
          )}
        </div>
      ))}
      <button type="button" className="boton boton-secundario" onClick={() => setVariantes((prev) => [...prev, { ...VARIANTE_VACIA }])} style={{ marginBottom: 14 }}>
        + Agregar talla/color
      </button>

      <div className="campo">
        <label>Fotos (opcional, se suben al guardar)</label>
        <input
          type="file"
          accept="image/png,image/jpeg,image/webp"
          multiple
          onChange={(e) => setFotos(Array.from(e.target.files))}
        />
        {fotos.length > 0 && (
          <span style={{ fontSize: 12, color: "#6B6259" }}>{fotos.length} foto(s) seleccionada(s)</span>
        )}
      </div>

      <button type="submit" className="boton boton-naranja" disabled={guardando}>
        {guardando ? "Guardando…" : "Guardar prenda"}
      </button>
    </form>
  );
}

function FormularioEditarProducto({ producto, onGuardado, onCancelar, categorias }) {
  const [nombre, setNombre] = useState(producto.nombre);
  const [descripcion, setDescripcion] = useState(producto.descripcion);
  const [categoria, setCategoria] = useState(producto.categoria);
  const [precio, setPrecio] = useState(String(producto.precio));
  const [variantes, setVariantes] = useState(producto.variantes.map((v) => ({ ...v })));
  const [error, setError] = useState("");
  const [guardando, setGuardando] = useState(false);

  function actualizarVariante(i, campo, valor) {
    setVariantes((prev) => prev.map((v, idx) => (idx === i ? { ...v, [campo]: valor } : v)));
  }

  function quitarVariante(i) {
    const v = variantes[i];
    if (v.id && (v.apartados_activos_count ?? 0) > 0) return;
    setVariantes((prev) => prev.filter((_, idx) => idx !== i));
  }

  async function guardar(evento) {
    evento.preventDefault();
    setError("");
    if (!nombre || !precio) {
      setError("Nombre y precio son obligatorios.");
      return;
    }
    setGuardando(true);
    try {
      const actualizado = await api.editarProducto(producto.id, {
        nombre,
        descripcion,
        categoria,
        precio: Number(precio),
        variantes: variantes
          .filter((v) => v.talla && v.color)
          .map((v) => ({ id: v.id, talla: v.talla, color: v.color, color_hex: v.color_hex, stock: Number(v.stock) })),
      });
      onGuardado(actualizado);
    } catch (e) {
      setError(e.message);
    } finally {
      setGuardando(false);
    }
  }

  return (
    <form onSubmit={guardar} style={{ margin: "14px 0" }}>
      {error && <p className="mensaje-error">{error}</p>}
      <div className="campo">
        <label>Nombre</label>
        <input value={nombre} onChange={(e) => setNombre(e.target.value)} required />
      </div>
      <div className="campo">
        <label>Descripción</label>
        <textarea rows={2} value={descripcion} onChange={(e) => setDescripcion(e.target.value)} />
      </div>
      <div style={{ display: "flex", gap: 12 }}>
        <div className="campo" style={{ flex: 1 }}>
          <label>Categoría</label>
          <SelectorCategoria value={categoria} onChange={(e) => setCategoria(e.target.value)} categorias={categorias} />
        </div>
        <div className="campo" style={{ flex: 1 }}>
          <label>Precio</label>
          <input type="number" min="0" step="1" value={precio} onChange={(e) => setPrecio(e.target.value)} required />
        </div>
      </div>

      <label style={{ fontSize: 13, color: "#6B6259" }}>Tallas y colores</label>
      {variantes.map((v, i) => {
        const bloqueada = v.id && (v.apartados_activos_count ?? 0) > 0;
        return (
          <div key={v.id ?? `nueva-${i}`} style={{ display: "flex", gap: 8, margin: "8px 0", alignItems: "center" }}>
            <input placeholder="Talla" style={{ width: 60 }} value={v.talla} onChange={(e) => actualizarVariante(i, "talla", e.target.value)} />
            <input placeholder="Color" style={{ width: 100 }} value={v.color} onChange={(e) => actualizarVariante(i, "color", e.target.value)} />
            <input type="color" value={v.color_hex} onChange={(e) => actualizarVariante(i, "color_hex", e.target.value)} style={{ width: 40, padding: 2 }} />
            <input type="number" min="0" placeholder="Existencia" style={{ width: 80 }} value={v.stock} onChange={(e) => actualizarVariante(i, "stock", e.target.value)} />
            <button
              type="button"
              className="boton boton-secundario"
              onClick={() => quitarVariante(i)}
              disabled={bloqueada}
              title={bloqueada ? "Tiene apartados sin entregar, no se puede quitar" : ""}
            >
              Quitar
            </button>
          </div>
        );
      })}
      <button
        type="button"
        className="boton boton-secundario"
        onClick={() => setVariantes((prev) => [...prev, { ...VARIANTE_VACIA }])}
        style={{ marginBottom: 14 }}
      >
        + Agregar talla/color
      </button>

      <div style={{ display: "flex", gap: 8 }}>
        <button type="submit" className="boton boton-naranja" disabled={guardando}>
          {guardando ? "Guardando…" : "Guardar cambios"}
        </button>
        <button type="button" className="boton boton-secundario" onClick={onCancelar}>Cancelar</button>
      </div>
    </form>
  );
}

function TarjetaProductoAdmin({ producto, onCambio, categorias }) {
  const [subiendo, setSubiendo] = useState(false);
  const [editando, setEditando] = useState(false);
  const [error, setError] = useState("");

  async function subirImagen(evento) {
    const archivo = evento.target.files[0];
    if (!archivo) return;
    setSubiendo(true);
    setError("");
    try {
      await api.subirImagen(producto.id, archivo);
      onCambio();
    } catch (e) {
      setError(e.message);
    } finally {
      setSubiendo(false);
      evento.target.value = "";
    }
  }

  async function eliminarImagen(imagenId) {
    await api.eliminarImagen(imagenId).catch((e) => setError(e.message));
    onCambio();
  }

  async function alternarActivo() {
    await api.editarProducto(producto.id, { activo: !producto.activo }).catch((e) => setError(e.message));
    onCambio();
  }

  async function eliminarProducto() {
    if (!confirm(`¿Eliminar "${producto.nombre}"? Esta acción no se puede deshacer.`)) return;
    await api.eliminarProducto(producto.id).catch((e) => setError(e.message));
    onCambio();
  }

  return (
    <div className="tarjeta-blanca">
      {error && <p className="mensaje-error">{error}</p>}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12, flexWrap: "wrap" }}>
        <div>
          <strong style={{ fontSize: 14 }}>{producto.nombre}</strong>
          <div style={{ fontSize: 13, color: "var(--acento-oscuro)", fontWeight: 500 }}>${producto.precio.toLocaleString("es-MX")}</div>
          <div style={{ fontSize: 12, color: "#6B6259" }}>{producto.categoria || "Sin categoría"}</div>
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button className="boton boton-secundario" onClick={() => setEditando((v) => !v)}>
            {editando ? "Cancelar edición" : "Editar"}
          </button>
          <button className="boton boton-secundario" onClick={alternarActivo}>
            {producto.activo ? "Ocultar del catálogo" : "Mostrar en catálogo"}
          </button>
          <button className="boton boton-secundario" onClick={eliminarProducto}>Eliminar</button>
        </div>
      </div>

      {editando ? (
        <FormularioEditarProducto
          producto={{
            ...producto,
            variantes: producto.variantes.map((v) => ({
              ...v,
              apartados_activos_count: (v.apartados || []).filter((a) => a.estado === "pendiente" || a.estado === "confirmado").length,
            })),
          }}
          onGuardado={() => {
            setEditando(false);
            onCambio();
          }}
          onCancelar={() => setEditando(false)}
          categorias={categorias}
        />
      ) : (
        <>
          <div style={{ margin: "14px 0" }}>
            <label style={{ fontSize: 12, color: "#6B6259" }}>Fotos</label>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", margin: "6px 0" }}>
              {producto.imagenes.map((img) => (
                <div key={img.id} style={{ position: "relative" }}>
                  <img src={img.url} alt="" style={{ width: 64, height: 64, objectFit: "cover", borderRadius: 8, border: "0.5px solid var(--borde)" }} />
                  <button
                    onClick={() => eliminarImagen(img.id)}
                    style={{ position: "absolute", top: -6, right: -6, width: 18, height: 18, borderRadius: "50%", border: "none", background: "#A32D2D", color: "#fff", fontSize: 11, cursor: "pointer" }}
                    aria-label="Eliminar foto"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
            <input type="file" accept="image/png,image/jpeg,image/webp" onChange={subirImagen} disabled={subiendo} />
          </div>

          <table className="tabla-simple">
            <thead>
              <tr><th>Talla</th><th>Color</th><th>Existencia</th><th>Apartadas</th><th>Disponible</th></tr>
            </thead>
            <tbody>
              {producto.variantes.map((v) => (
                <tr key={v.id}>
                  <td>{v.talla}</td>
                  <td style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span className="punto-color" style={{ background: v.color_hex }} />{v.color}
                  </td>
                  <td>{v.stock}</td>
                  <td>{v.stock - v.disponible}</td>
                  <td style={{ color: v.disponible <= 0 ? "#A32D2D" : undefined, fontWeight: 500 }}>{v.disponible}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p style={{ fontSize: 12, color: "#6B6259", margin: "8px 0 0" }}>
            La existencia baja hasta que marcas un apartado como "Entregado" en la pestaña Apartados.
            Para corregir la existencia física usa "Editar".
          </p>
        </>
      )}
    </div>
  );
}

export default function AdminInventario() {
  const [productos, setProductos] = useState(null);
  const [categorias, setCategorias] = useState([]);
  const [error, setError] = useState("");
  const [mostrarFormulario, setMostrarFormulario] = useState(false);

  function cargar() {
    api.adminProductos().then(setProductos).catch((e) => setError(e.message));
  }

  function cargarCategorias() {
    api.adminCategorias().then(setCategorias).catch((e) => setError(e.message));
  }

  useEffect(cargar, []);
  useEffect(cargarCategorias, []);

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <h1 style={{ fontSize: 18, fontWeight: 500, margin: 0 }}>Inventario</h1>
        <button className="boton boton-naranja" onClick={() => setMostrarFormulario((v) => !v)}>
          {mostrarFormulario ? "Cancelar" : "+ Agregar prenda"}
        </button>
      </div>

      {error && <p className="mensaje-error">{error}</p>}
      {mostrarFormulario && (
        <FormularioNuevoProducto
          categorias={categorias}
          onCreado={() => {
            setMostrarFormulario(false);
            cargar();
          }}
        />
      )}

      {!productos && <p className="centrado">Cargando…</p>}
      {productos && productos.length === 0 && <p className="centrado">Todavía no has agregado ninguna prenda.</p>}
      {productos && productos.map((p) => (
        <TarjetaProductoAdmin key={p.id} producto={p} onCambio={cargar} categorias={categorias} />
      ))}
    </div>
  );
}
