// Where the login token lives.
// "Remember me" ticked  -> localStorage   (stays after the browser is closed)
// "Remember me" not ticked -> sessionStorage (cleared when the browser is closed)
const KEY = 'access_token';

export function getToken() {
  return localStorage.getItem(KEY) || sessionStorage.getItem(KEY);
}

export function saveToken(token, remember) {
  clearToken();
  (remember ? localStorage : sessionStorage).setItem(KEY, token);
}

export function clearToken() {
  localStorage.removeItem(KEY);
  sessionStorage.removeItem(KEY);
}
