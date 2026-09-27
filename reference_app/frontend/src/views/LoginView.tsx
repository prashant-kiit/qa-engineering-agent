import { useState } from "react";
import { apiUrl, authHeaders, type Credentials } from "../api";

export type LoginViewProps = {
  onLogin: (creds: Credentials) => void;
};

/**
 * Login view: captures username + password and verifies them against the
 * backend with an authenticated (HTTP Basic) request. On success it hands the
 * credentials up via `onLogin`; on a 401 it surfaces an auth-failure and does
 * not proceed.
 */
export function LoginView({ onLogin }: LoginViewProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    const creds: Credentials = { username, password };
    try {
      const res = await fetch(apiUrl("/cart"), {
        method: "GET",
        headers: authHeaders(creds),
      });
      if (!res.ok) {
        setError("Authentication failed. Please check your credentials.");
        return;
      }
      onLogin(creds);
    } catch {
      setError("Unable to reach the server. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <h1>Sign in</h1>
      <label>
        Username
        <input
          data-testid="login-username"
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
      </label>
      <label>
        Password
        <input
          data-testid="login-password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </label>
      <button data-testid="login-submit" type="submit" disabled={busy}>
        Sign in
      </button>
      {error && (
        <p data-testid="login-error" role="alert">
          {error}
        </p>
      )}
    </form>
  );
}
