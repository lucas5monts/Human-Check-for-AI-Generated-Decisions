export const API_BASE_URL = import.meta.env.PUBLIC_API_BASE_URL ?? "";

export function apiUrl(path) {
  return `${API_BASE_URL}${path}`;
}
