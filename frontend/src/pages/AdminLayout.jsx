import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { api } from "../api";

export default function AdminLayout({ usuario, onLogout }) {
  const navigate = useNavigate();

  async function salir() {
    await api.logout().catch(() => {});
    onLogout();
    navigate("/admin");
  }

  return (
    <div className="panel-admin">
      <nav className="panel-nav">
        <NavLink to="/admin/inventario" className={({ isActive }) => (isActive ? "activo" : "")}>
          Inventario
        </NavLink>
        <NavLink to="/admin/apartados" className={({ isActive }) => (isActive ? "activo" : "")}>
          Apartados
        </NavLink>
        <NavLink to="/admin/cuenta" className={({ isActive }) => (isActive ? "activo" : "")}>
          Cuenta
        </NavLink>
        <a href="#salir" onClick={salir}>Cerrar sesión ({usuario.nombre})</a>
      </nav>
      <div className="panel-contenido">
        <Outlet />
      </div>
    </div>
  );
}
