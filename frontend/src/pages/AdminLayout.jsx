import { NavLink, Navigate, Outlet, useLocation, useNavigate } from "react-router-dom";
import { api } from "../api";

export default function AdminLayout({ usuario, onLogout, onUsuarioActualizado }) {
  const navigate = useNavigate();
  const location = useLocation();

  async function salir() {
    await api.logout().catch(() => {});
    onLogout();
    navigate("/admin");
  }

  if (usuario.debe_cambiar_password && location.pathname !== "/admin/cuenta") {
    return <Navigate to="/admin/cuenta" replace />;
  }

  return (
    <div className="panel-admin">
      <nav className="panel-nav">
        {!usuario.debe_cambiar_password && (
          <>
            <NavLink to="/admin/inventario" className={({ isActive }) => (isActive ? "activo" : "")}>
              Inventario
            </NavLink>
            <NavLink to="/admin/categorias" className={({ isActive }) => (isActive ? "activo" : "")}>
              Categorías
            </NavLink>
            <NavLink to="/admin/apartados" className={({ isActive }) => (isActive ? "activo" : "")}>
              Apartados
            </NavLink>
            <NavLink to="/admin/usuarios" className={({ isActive }) => (isActive ? "activo" : "")}>
              Usuarios
            </NavLink>
          </>
        )}
        <NavLink to="/admin/cuenta" className={({ isActive }) => (isActive ? "activo" : "")}>
          Cuenta
        </NavLink>
        <a href="#salir" onClick={salir}>Cerrar sesión ({usuario.nombre})</a>
      </nav>
      <div className="panel-contenido">
        <Outlet context={{ usuario, onUsuarioActualizado }} />
      </div>
    </div>
  );
}
