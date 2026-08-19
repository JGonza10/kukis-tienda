const BASE = "/api";

async function solicitud(ruta, opciones = {}) {
  const respuesta = await fetch(`${BASE}${ruta}`, {
    credentials: "include",
    headers: opciones.body instanceof FormData ? {} : { "Content-Type": "application/json" },
    ...opciones,
  });
  const contentType = respuesta.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await respuesta.json() : null;
  if (!respuesta.ok) {
    throw new Error((data && data.error) || "Ocurrió un error inesperado.");
  }
  return data;
}

export const api = {
  horario: () => solicitud("/horario"),
  productos: () => solicitud("/productos"),
  producto: (id) => solicitud(`/productos/${id}`),
  crearApartado: (payload) =>
    solicitud("/apartados", { method: "POST", body: JSON.stringify(payload) }),

  login: (payload) =>
    solicitud("/admin/login", { method: "POST", body: JSON.stringify(payload) }),
  logout: () => solicitud("/admin/logout", { method: "POST" }),
  me: () => solicitud("/admin/me"),
  cambiarPassword: (payload) =>
    solicitud("/admin/password", { method: "PUT", body: JSON.stringify(payload) }),

  adminUsuarios: () => solicitud("/admin/usuarios"),
  crearUsuario: (payload) =>
    solicitud("/admin/usuarios", { method: "POST", body: JSON.stringify(payload) }),
  eliminarUsuario: (id) => solicitud(`/admin/usuarios/${id}`, { method: "DELETE" }),

  adminProductos: () => solicitud("/admin/productos"),
  crearProducto: (payload) =>
    solicitud("/admin/productos", { method: "POST", body: JSON.stringify(payload) }),
  editarProducto: (id, payload) =>
    solicitud(`/admin/productos/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  eliminarProducto: (id) => solicitud(`/admin/productos/${id}`, { method: "DELETE" }),
  subirImagen: (productoId, archivo) => {
    const formData = new FormData();
    formData.append("imagen", archivo);
    return solicitud(`/admin/productos/${productoId}/imagenes`, {
      method: "POST",
      body: formData,
    });
  },
  eliminarImagen: (id) => solicitud(`/admin/imagenes/${id}`, { method: "DELETE" }),

  adminApartados: (estado) =>
    solicitud(`/admin/apartados${estado ? `?estado=${estado}` : ""}`),
  actualizarApartado: (id, payload) =>
    solicitud(`/admin/apartados/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
};
