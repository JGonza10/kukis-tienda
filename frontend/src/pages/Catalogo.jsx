import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import ProductCard from "../components/ProductCard";

export default function Catalogo() {
  const [productos, setProductos] = useState(null);
  const [error, setError] = useState("");
  const [categoria, setCategoria] = useState("");
  const [talla, setTalla] = useState("");

  useEffect(() => {
    api.productos().then(setProductos).catch((e) => setError(e.message));
  }, []);

  const categorias = useMemo(() => {
    if (!productos) return [];
    return [...new Set(productos.map((p) => p.categoria).filter(Boolean))].sort();
  }, [productos]);

  const tallas = useMemo(() => {
    if (!productos) return [];
    const todas = productos.flatMap((p) => p.variantes.map((v) => v.talla));
    return [...new Set(todas.filter(Boolean))].sort();
  }, [productos]);

  const productosFiltrados = useMemo(() => {
    if (!productos) return productos;
    return productos.filter((p) => {
      if (categoria && p.categoria !== categoria) return false;
      if (talla && !p.variantes.some((v) => v.talla === talla)) return false;
      return true;
    });
  }, [productos, categoria, talla]);

  return (
    <>
      <section className="hero">
        <span className="kicker">En el tianguis · cada domingo</span>
        <h1>Moda para cada domingo</h1>
        <p>Aparta tu prenda favorita y recógela en el tianguis del mercado de Bola, junto a la primaria</p>
      </section>

      <div className="contenedor">
        <div style={{ padding: "20px 0 0", fontSize: 14, fontWeight: 500 }}>Novedades</div>
        {error && <p className="mensaje-error">{error}</p>}
        {!productos && !error && <p className="centrado">Cargando catálogo…</p>}
        {productos && productos.length === 0 && (
          <p className="centrado">Todavía no hay prendas publicadas. Vuelve pronto.</p>
        )}

        {productos && productos.length > 0 && (categorias.length > 0 || tallas.length > 0) && (
          <div className="filtros-catalogo">
            {categorias.length > 0 && (
              <div className="grupo-filtro">
                <span className="etiqueta-filtro">Categoría:</span>
                <button
                  className={`filtro-chip${categoria === "" ? " activo" : ""}`}
                  onClick={() => setCategoria("")}
                >
                  Todas
                </button>
                {categorias.map((c) => (
                  <button
                    key={c}
                    className={`filtro-chip${categoria === c ? " activo" : ""}`}
                    onClick={() => setCategoria(c === categoria ? "" : c)}
                  >
                    {c}
                  </button>
                ))}
              </div>
            )}
            {tallas.length > 0 && (
              <div className="grupo-filtro">
                <span className="etiqueta-filtro">Talla:</span>
                <button
                  className={`filtro-chip${talla === "" ? " activo" : ""}`}
                  onClick={() => setTalla("")}
                >
                  Todas
                </button>
                {tallas.map((t) => (
                  <button
                    key={t}
                    className={`filtro-chip${talla === t ? " activo" : ""}`}
                    onClick={() => setTalla(t === talla ? "" : t)}
                  >
                    {t}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {productos && productos.length > 0 && productosFiltrados.length === 0 && (
          <p className="centrado">Ninguna prenda coincide con ese filtro.</p>
        )}
      </div>

      {productosFiltrados && productosFiltrados.length > 0 && (
        <div className="rejilla-productos contenedor">
          {productosFiltrados.map((p) => (
            <ProductCard key={p.id} producto={p} />
          ))}
        </div>
      )}
    </>
  );
}
