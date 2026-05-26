"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiFetch } from "@/lib/api-client";

const COPY = {
  email: "Email",
  password: "Password",
  signIn: "Sign in",
  signInSubtitle: "Enter your email and password",
  error: "Invalid email or password",
  rateLimited: "Too many login attempts. Please try again later.",
};

export function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await apiFetch<{ accessToken: string }>(
        "/auth/login",
        {
          method: "POST",
          body: { email, password },
        }
      );

      if (response && "accessToken" in response) {
        // Store token in localStorage (client-side for NextAuth)
        localStorage.setItem("token", response.accessToken);
        // Also set as cookie for server-side requests
        document.cookie = `token=${response.accessToken}; path=/; SameSite=Strict; Secure`;
        router.push("/dashboard");
      }
    } catch (err: unknown) {
      if (err instanceof Error && "status" in err && (err as { status: number }).status === 429) {
        setError(COPY.rateLimited);
      } else {
        setError(COPY.error);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email">{COPY.email}</Label>
          <Input
            id="email"
            type="email"
            placeholder="juan@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={loading}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">{COPY.password}</Label>
          <Input
            id="password"
            type="password"
            placeholder="••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={loading}
            required
          />
        </div>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <Button
        type="submit"
        className="w-full"
        disabled={loading}
      >
        {loading ? "Signing in..." : COPY.signIn}
      </Button>

      <p className="text-xs text-muted-foreground text-center">
        MVP: Single-user only. Contact admin for credentials.
      </p>
    </form>
  );
}
