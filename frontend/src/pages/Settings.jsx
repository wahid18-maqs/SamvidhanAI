import { Link } from "react-router-dom";
import { Moon } from "lucide-react";
import { useAuth } from "../context/AuthContext";

/** Ui updates and features.md 2.2 A3/A4: Account Details + Display Theme.
 * Account Details is sourced straight from the existing Supabase Auth
 * session (client-side, same as TopBar's avatar) — no new backend call
 * needed, `user.id`/`user.email`/`user.created_at` are already there.
 * Display Theme: the app's neutral dark palette (Ui updates and
 * features.md Part 1) is the one locked design system, not a toggle
 * between two built themes — this section confirms that rather than
 * building a real, separately-designed light mode with no spec of its
 * own yet. */
export default function Settings() {
  const { user, signOut } = useAuth();

  return (
    <div className="min-h-screen bg-base px-6 py-6">
      <div className="mx-auto max-w-2xl">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-lg font-semibold text-heading">Settings</h1>
          <Link to="/chat" className="text-sm text-body underline decoration-border-strong underline-offset-4">
            Back to chat
          </Link>
        </div>

        <section className="mb-6 rounded-xl border border-border bg-panel p-5">
          <h2 className="text-sm font-semibold text-heading">Account Details</h2>
          <dl className="mt-3 space-y-2 text-sm">
            <div className="flex justify-between gap-4">
              <dt className="text-muted">Email</dt>
              <dd className="text-body">{user?.email}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="text-muted">User ID</dt>
              <dd className="truncate text-body" title={user?.id}>
                {user?.id}
              </dd>
            </div>
            {user?.created_at && (
              <div className="flex justify-between gap-4">
                <dt className="text-muted">Member since</dt>
                <dd className="text-body">{new Date(user.created_at).toLocaleDateString()}</dd>
              </div>
            )}
          </dl>
          <button
            type="button"
            onClick={signOut}
            className="mt-4 rounded-lg border border-border px-3 py-1.5 text-xs font-medium text-body transition hover:bg-border/60"
          >
            Sign out
          </button>
        </section>

        <section className="rounded-xl border border-border bg-panel p-5">
          <h2 className="text-sm font-semibold text-heading">Display Theme</h2>
          <div className="mt-3 flex items-center gap-2.5 rounded-lg border border-border bg-base/60 px-3 py-2.5 text-sm text-body">
            <Moon size={16} className="shrink-0 text-muted" />
            <span>Dark — the only theme currently available.</span>
          </div>
          <p className="mt-2 text-xs text-muted">
            SamvidhanAI uses one locked neutral dark design system today. A separately-designed
            light theme isn't built yet.
          </p>
        </section>
      </div>
    </div>
  );
}
