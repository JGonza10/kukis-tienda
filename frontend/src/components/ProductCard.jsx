import { Link } from "react-router-dom";

export default function ProductCard({ producto }) {
  const imagenPrincipal = producto.imagenes[0];
  const tallas = [...new Set(producto.variantes.map((v) => v.talla))];
  const colores = [...new Map(producto.variantes.map((v) => [v.color, v.color_hex])).entries()];
  const hayStock = producto.variantes.some((v) => v.disponible > 0);

  return (
    <Link to={`/producto/${producto.id}`} className="tarjeta-producto">
      <div className="imagen">
        {imagenPrincipal ? (
          <img src={imagenPrincipal.url} alt={producto.nombre} />
        ) : (
          <span style={{ color: "var(--acento-oscuro)", fontSize: 12 }}>Sin foto</span>
        )}
      </div>
      <div className="cuerpo">
        <span className="nombre">{producto.nombre}</span>
        <span className="precio">${producto.precio.toLocaleString("es-MX")}</span>
        <div className="fila-inferior">
          <div className="chips">
            {tallas.map((t) => (
              <span key={t} className="chip-talla">{t}</span>
            ))}
            {colores.map(([nombre, hex]) => (
              <span key={nombre} className="punto-color" style={{ background: hex }} title={nombre} />
            ))}
          </div>
          <span className="boton-mini">Ver detalle</span>
        </div>
        {!hayStock && <span className="texto-agotado">Sin existencia</span>}
      </div>
    </Link>
  );
}
