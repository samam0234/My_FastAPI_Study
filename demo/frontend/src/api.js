const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8001";

async function request(path, { method = "GET", body, token, form } = {}) {
  const headers = {};
  let payload;

  if (form) {
    headers["Content-Type"] = "application/x-www-form-urlencoded";
    payload = new URLSearchParams(body).toString();
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json; charset=utf-8";
    payload = JSON.stringify(body);
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE_URL}${path}`, { method, headers, body: payload });
  const isJson = res.headers.get("content-type")?.includes("application/json");
  const data = isJson ? await res.json() : null;
  if (!res.ok) {
    const error = data?.error;
    const fieldText = error?.fields
      ? " " + Object.entries(error.fields).map(([key, messages]) => `${key}: ${messages.join(", ")}`).join(" / ")
      : "";
    throw new Error((error?.message || `요청 실패 (${res.status})`) + fieldText);
  }
  return data;
}

export const api = {
  listPosts: (params) => {
    const query = new URLSearchParams(params).toString();
    return request(`/api/posts${query ? `?${query}` : ""}`);
  },
  createPost: (post, token) => request("/api/posts", { method: "POST", body: post, token }),
  deletePost: (id, token) => request(`/api/posts/${id}`, { method: "DELETE", token }),
  addComment: (id, body, token) => request(`/api/posts/${id}/comments`, { method: "POST", body: { body }, token }),
  signup: (email, password, nickname) =>
    request("/api/auth/signup", { method: "POST", body: { email, password, nickname } }),
  login: (email, password) => request("/api/auth/login", { method: "POST", body: { email, password } }),
  logout: (token) => request("/api/auth/logout", { method: "POST", token }),
  me: (token) => request("/api/auth/me", { token }),
};
