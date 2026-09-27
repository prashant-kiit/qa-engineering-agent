import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { LoginView } from "../views";
import {
  installFetch,
  jsonResponse,
  headerOf,
  basicHeader,
  TEST_CREDS,
} from "../test/helpers";

/**
 * LoginView contract (Tester-defined, documented in p0-shop-frontend.tests.md):
 *   import { LoginView } from "../views"
 *   props: { onLogin: (creds: {username,password}) => void }
 *   testids: login-username, login-password, login-submit, login-error
 * On submit it performs an authenticated (HTTP Basic) fetch derived from the
 * entered credentials; on success it calls onLogin, on 401 it shows an auth
 * error and does NOT proceed (onLogin not called).
 */
describe("LoginView", () => {
  it("renders username, password, and submit controls (criterion 3, 17)", () => {
    render(<LoginView onLogin={() => {}} />);
    expect(screen.getByTestId("login-username")).toBeInTheDocument();
    expect(screen.getByTestId("login-password")).toBeInTheDocument();
    expect(screen.getByTestId("login-submit")).toBeInTheDocument();
  });

  it("captures entered credentials and issues an authenticated Basic-auth request (criterion 4)", async () => {
    const { calls } = installFetch(() => jsonResponse({ items: [], total: 0 }, 200));
    const onLogin = vi.fn();
    render(<LoginView onLogin={onLogin} />);

    fireEvent.change(screen.getByTestId("login-username"), {
      target: { value: TEST_CREDS.username },
    });
    fireEvent.change(screen.getByTestId("login-password"), {
      target: { value: TEST_CREDS.password },
    });
    fireEvent.click(screen.getByTestId("login-submit"));

    await waitFor(() => expect(calls.length).toBeGreaterThan(0));
    const authed = calls.find(
      (c) => headerOf(c.init, "Authorization") === basicHeader(TEST_CREDS)
    );
    expect(authed, "expected a fetch carrying Basic auth for entered creds").toBeTruthy();

    await waitFor(() =>
      expect(onLogin).toHaveBeenCalledWith(
        expect.objectContaining({
          username: TEST_CREDS.username,
          password: TEST_CREDS.password,
        })
      )
    );
  });

  it("shows an auth-failure indication on 401 and does not proceed (criterion 5)", async () => {
    installFetch(() => jsonResponse({ detail: "Unauthorized" }, 401));
    const onLogin = vi.fn();
    render(<LoginView onLogin={onLogin} />);

    fireEvent.change(screen.getByTestId("login-username"), {
      target: { value: "wrong" },
    });
    fireEvent.change(screen.getByTestId("login-password"), {
      target: { value: "creds" },
    });
    fireEvent.click(screen.getByTestId("login-submit"));

    await waitFor(() =>
      expect(screen.getByTestId("login-error")).toBeInTheDocument()
    );
    expect(onLogin).not.toHaveBeenCalled();
  });
});
