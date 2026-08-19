import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api";

export default function ProductoDetalle() {
  const { id } = useParams();
  const [producto, setProducto] = useState(null);
  const [error, setError] = useState("");
  const [imagenActiva, setImagenActiva] = useState(0);
  const [varianteId, setVarianteId] = useState(null);
  const [nombre, setNombre] = useState("");
  const [telefono, setTelefono] = useState("");
  const [notas, setNotas] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [errorApartado, setErrorApartado] = useState("");
  const [confirmacion, setConfirmacion] = useState(null);

  useEffect(() => {
    api
      .producto(id)
      .then((data) => {
        setProducto(data);
        const primeraDisponible = data.variantes.find((v) => v.disponible > 0);
        setVarianteId(primeraDisponible ? primeraDisponible.id : null);
      })
      .catch((e) => setError(e.message));
  }, [id]);

  if (error) return <p className="mensaje-error contenedor">{error}</p>;
  if (!producto) return <p className="centrado">Cargando…</p>;

  const variante = producto.variantes.find((v) => v.id === varianteId);
  const imagenes = producto.imagenes;

  async function apartar(evento) {
    evento.preventDefault();
    setErrorApartado("");
    if (!varianteId) {
      setErrorApartado("Elige una talla y color disponible.");
      return;
    }
    setEnviando(true);
    try {
      const resultado = await api.crearApartado({
        variante_id: varianteId,
        cliente_nombre: nombre,
        cliente_telefono: telefono,
        notas,
      });
      setConfirmacion(resultado);
    } catch (e) {
      setErrorApartado(e.message);
    } finally {
      setEnviando(false);
    }
  }

  if (confirmacion) {
    return (
      <div className="contenedor" style={{ padding: "40px 20px", maxWidth: 480 }}>
        <div className="tarjeta-blanca">
          <p className="mensaje-exito">¡Tu prenda quedó apartada!</p>
          <p style={{ fontSize: 14 }}>
            <strong>{confirmacion.producto_nombre}</strong> · talla {confirmacion.talla} · {confirmacion.color}
          </p>
          <p style={{ fontSize: 13, color: "#6B6259" }}>
            Recógela y págala el domingo {confirmacion.fecha_entrega} en el tianguis. Cualquier
            duda, escríbenos por WhatsApp al 55 2417 7160.
          </p>
          <Link to="/" className="boton boton-naranja" style={{ marginTop: 10, display: "inline-block" }}>
            Seguir viendo el catálogo
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="ficha-producto contenedor">
      <div className="galeria">
        <div className="principal">
          {imagenes[imagenActiva] ? (
            <img src={imagenes[imagenActiva].url} alt={producto.nombre} />
          ) : (
            <span style={{ color: "#B85A16", fontSize: 13 }}>Sin foto todavía</span>
          )}
        </div>
        {imagenes.length > 1 && (
          <div className="miniaturas">
            {imagenes.map((img, i) => (
              <img
                key={img.id}
                src={img.url}
                alt=""
                onClick={() => setImagenActiva(i)}
                style={{ borderColor: i === imagenActiva ? "#1B5FCC" : undefined }}
              />
            ))}
          </div>
        )}
      </div>

      <div>
        <h1 style={{ fontSize: 20, fontWeight: 500, margin: "0 0 4px" }}>{producto.nombre}</h1>
        <p style={{ fontSize: 18, fontWeight: 500, color: "#B23368", margin: "0 0 10px" }}>
          ${producto.precio.toLocaleString("es-MX")}
        </p>
        <p style={{ fontSize: 14, color: "#6B6259" }}>{producto.descripcion}</p>

        <div className="selector-variante">
          {producto.variantes.map((v) => (
            <button
              key={v.id}
              type="button"
              className={`opcion-variante ${v.id === varianteId ? "activa" : ""} ${v.disponible <= 0 ? "agotada" : ""}`}
              disabled={v.disponible <= 0}
              onClick={() => setVarianteId(v.id)}
            >
              <span className="punto-color" style={{ background: v.color_hex }} />
              {v.talla} · {v.color}
            </button>
          ))}
        </div>

        <form onSubmit={apartar} className="tarjeta-blanca">
          {errorApartado && <p className="mensaje-error">{errorApartado}</p>}
          <div className="campo">
            <label htmlFor="nombre">Tu nombre</label>
            <input id="nombre" required value={nombre} onChange={(e) => setNombre(e.target.value)} />
          </div>
          <div className="campo">
            <label htmlFor="telefono">Tu teléfono (WhatsApp)</label>
            <input
              id="telefono"
              required
              type="tel"
              value={telefono}
              onChange={(e) => setTelefono(e.target.value)}
              placeholder="5512345678"
            />
          </div>
          <div className="campo">
            <label htmlFor="notas">Notas (opcional)</label>
            <textarea id="notas" rows={2} value={notas} onChange={(e) => setNotas(e.target.value)} />
          </div>
          <button
            type="submit"
            className="boton boton-naranja"
            disabled={enviando || !variante || variante.disponible <= 0}
            style={{ width: "100%" }}
          >
            {enviando ? "Apartando…" : "Apartar esta prenda"}
          </button>
          <p style={{ fontSize: 12, color: "#6B6259", marginTop: 10, marginBottom: 0 }}>
            Se paga y se recoge en persona el domingo en el tianguis.
          </p>
        </form>
      </div>
    </div>
  );
}
