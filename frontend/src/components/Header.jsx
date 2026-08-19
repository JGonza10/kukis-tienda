import { Link } from "react-router-dom";

export default function Header() {
  return (
    <header className="encabezado">
      <nav className="nav">
        <Link to="/">Catálogo</Link>
        <a href="#contacto">Contacto</a>
      </nav>
      <Link to="/" className="logo">
        <span className="logo-marca">K</span>
        <span>Kukis</span>
      </Link>
      <Link to="/admin" className="enlace-cuenta">Panel de la vendedora</Link>
    </header>
  );
}
