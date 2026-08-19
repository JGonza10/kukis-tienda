import { useEffect, useState } from "react";
import { Routes, Route, Navigate, Outlet } from "react-router-dom";
import { api } from "./api";
import Header from "./components/Header";
import Footer from "./components/Footer";
import HorarioBadge from "./components/HorarioBadge";
import Catalogo from "./pages/Catalogo";
import ProductoDetalle from "./pages/ProductoDetalle";
import AdminLogin from "./pages/AdminLogin";
import AdminLayout from "./pages/AdminLayout";
import AdminInventario from "./pages/AdminInventario";
import AdminApartados from "./pages/AdminApartados";
import AdminCuenta from "./pages/AdminCuenta";
import AdminUsuarios from "./pages/AdminUsuarios";

function LayoutPublico() {
  return (
    <>
      <Header />
      <div className="franja-horario">
        <HorarioBadge />
      </div>
      <Outlet />
      <Footer />
    </>
  );
}

export default function App() {
  const [usuario, setUsuario] = useState(null);
  const [cargandoSesion, setCargandoSesion] = useState(true);

  useEffect(() => {
    api.me().then(setUsuario).catch(() => {}).finally(() => setCargandoSesion(false));
  }, []);

  if (cargandoSesion) return null;

  return (
    <Routes>
      <Route element={<LayoutPublico />}>
        <Route path="/" element={<Catalogo />} />
        <Route path="/producto/:id" element={<ProductoDetalle />} />
      </Route>

      <Route
        path="/admin"
        element={
          usuario ? (
            <Navigate to={usuario.debe_cambiar_password ? "/admin/cuenta" : "/admin/inventario"} replace />
          ) : (
            <AdminLogin onLogin={setUsuario} />
          )
        }
      />

      <Route
        path="/admin"
        element={
          usuario ? (
            <AdminLayout usuario={usuario} onLogout={() => setUsuario(null)} onUsuarioActualizado={setUsuario} />
          ) : (
            <Navigate to="/admin" replace />
          )
        }
      >
        <Route path="inventario" element={<AdminInventario />} />
        <Route path="apartados" element={<AdminApartados />} />
        <Route path="cuenta" element={<AdminCuenta />} />
        <Route path="usuarios" element={<AdminUsuarios />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
