import { SignInForm } from "@/features/auth/sign-in-form";

export default function HomePage() {
  return (
    <main>
      <h1>Telesales Portal</h1>
      <p>Sign in using your phone number or email.</p>
      <SignInForm />
    </main>
  );
}
