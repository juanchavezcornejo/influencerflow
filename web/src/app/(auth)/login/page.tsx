import { LoginForm } from "./LoginForm.client";

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="w-full max-w-md px-4">
        <div className="space-y-6">
          <div className="text-center">
            <h1 className="text-2xl font-semibold">InfluencerFlow</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Turn travel photos into Instagram-ready posts
            </p>
          </div>
          <LoginForm />
        </div>
      </div>
    </div>
  );
}
